package main

import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"strconv"
	"strings"
	"time"

	influxdb2 "github.com/influxdata/influxdb-client-go/v2"
	"github.com/influxdata/influxdb-client-go/v2/api"
	"github.com/jackc/pgx/v5/pgxpool"
)

// Estructuras de datos
type User struct {
	PatientID      string     `json:"patient_id"`
	Name           string     `json:"name"`
	DateOfBirth    *time.Time `json:"date_of_birth,omitempty"`
	Gender         string     `json:"gender"`
	Email          string     `json:"email"`
	Password       string     `json:"password,omitempty"`
	MedicalHistory string     `json:"medical_history"`
	RolAccount     string     `json:"rol_account"`
}

// Estructura temporal para recibir datos del frontend
type CreateUserRequest struct {
	PatientID      string `json:"patient_id"`
	Name           string `json:"name"`
	DateOfBirth    string `json:"date_of_birth"`
	Gender         string `json:"gender"`
	Email          string `json:"email"`
	Password       string `json:"password"`
	MedicalHistory string `json:"medical_history"`
	RolAccount     string `json:"rol_account"`
}

type GPSData struct {
	PatientID string    `json:"patient_id"`
	Latitude  float64   `json:"latitude"`
	Longitude float64   `json:"longitude"`
	Timestamp time.Time `json:"timestamp"`
}

type VitalSigns struct {
	PatientID   string    `json:"patient_id"`
	HeartRate   int       `json:"heart_rate"`
	BloodOxygen int       `json:"blood_oxygen"`
	Temperature float64   `json:"temperature"`
	Timestamp   time.Time `json:"timestamp"`
}

type KPIRisk struct {
	PatientID string    `json:"patient_id"`
	RiskScore float64   `json:"risk_score"`
	Category  string    `json:"category"`
	Timestamp time.Time `json:"timestamp"`
}

type Server struct {
	PostgresDB *pgxpool.Pool
	InfluxDB   influxdb2.Client
	InfluxAPI  api.QueryAPI
}

// Handlers para CRUD de usuarios
func (s *Server) handleCreateUser(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var req CreateUserRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		log.Printf("Error decoding JSON: %v", err)
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	// Validar campos requeridos
	if req.PatientID == "" || req.Name == "" || req.Email == "" || req.Password == "" || req.RolAccount == "" {
		http.Error(w, "Missing required fields", http.StatusBadRequest)
		return
	}

	// Convertir fecha de string a *time.Time
	var dateOfBirth *time.Time
	if req.DateOfBirth != "" {
		parsedDate, err := time.Parse("2006-01-02", req.DateOfBirth)
		if err != nil {
			log.Printf("Error parsing date: %v", err)
			http.Error(w, "Invalid date format. Use YYYY-MM-DD", http.StatusBadRequest)
			return
		}
		dateOfBirth = &parsedDate
	}

	// Crear usuario con la estructura correcta
	user := User{
		PatientID:      req.PatientID,
		Name:           req.Name,
		DateOfBirth:    dateOfBirth,
		Gender:         req.Gender,
		Email:          req.Email,
		Password:       req.Password,
		MedicalHistory: req.MedicalHistory,
		RolAccount:     req.RolAccount,
	}

	// Insertar usuario en PostgreSQL
	query := `INSERT INTO user_information (patient_id, name, date_of_birth, gender, email, password, medical_history, rol_account)
			  VALUES ($1, $2, $3, $4, $5, $6, $7, $8)`

	_, err := s.PostgresDB.Exec(r.Context(), query,
		user.PatientID, user.Name, user.DateOfBirth, user.Gender,
		user.Email, user.Password, user.MedicalHistory, user.RolAccount)

	if err != nil {
		log.Printf("Error creating user: %v", err)
		http.Error(w, "Database error", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(map[string]string{"message": "User created successfully", "patient_id": user.PatientID})
}

func (s *Server) handleGetUsers(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	rows, err := s.PostgresDB.Query(ctx, `SELECT patient_id, name, date_of_birth, gender, email, medical_history, rol_account FROM user_information ORDER BY name`)
	if err != nil {
		log.Printf("query users error: %v", err)
		http.Error(w, "db error", http.StatusInternalServerError)
		return
	}
	defer rows.Close()

	users := make([]User, 0, 100)
	for rows.Next() {
		var u User
		var dob sql.NullTime
		var gender sql.NullString
		var email sql.NullString
		var med sql.NullString
		var rol sql.NullString
		if err := rows.Scan(&u.PatientID, &u.Name, &dob, &gender, &email, &med, &rol); err != nil {
			log.Printf("scan error: %v", err)
			continue
		}
		if dob.Valid {
			t := dob.Time
			u.DateOfBirth = &t
		}
		if gender.Valid {
			u.Gender = gender.String
		}
		if email.Valid {
			u.Email = email.String
		}
		if med.Valid {
			u.MedicalHistory = med.String
		}
		if rol.Valid {
			u.RolAccount = rol.String
		} else {
			u.RolAccount = "patient"
		}
		users = append(users, u)
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]any{"users": users})
}

func (s *Server) handleGetUser(w http.ResponseWriter, r *http.Request) {
	patientID := strings.TrimPrefix(r.URL.Path, "/api/users/")
	if patientID == "" {
		http.Error(w, "Patient ID required", http.StatusBadRequest)
		return
	}

	var user User
	query := `SELECT patient_id, name, date_of_birth, gender, email, medical_history, rol_account FROM user_information WHERE patient_id = $1`

	err := s.PostgresDB.QueryRow(r.Context(), query, patientID).Scan(
		&user.PatientID, &user.Name, &user.DateOfBirth, &user.Gender,
		&user.Email, &user.MedicalHistory, &user.RolAccount)

	if err != nil {
		if err == sql.ErrNoRows {
			http.Error(w, "User not found", http.StatusNotFound)
			return
		}
		log.Printf("Error getting user: %v", err)
		http.Error(w, "Database error", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(user)
}

func (s *Server) handleUpdateUser(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPut {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	patientID := strings.TrimPrefix(r.URL.Path, "/api/users/")
	if patientID == "" {
		http.Error(w, "Patient ID required", http.StatusBadRequest)
		return
	}

	var user User
	if err := json.NewDecoder(r.Body).Decode(&user); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	// Actualizar usuario en PostgreSQL
	query := `UPDATE user_information SET name = $1, date_of_birth = $2, gender = $3, email = $4, medical_history = $5, rol_account = $6 WHERE patient_id = $7`

	result, err := s.PostgresDB.Exec(r.Context(), query,
		user.Name, user.DateOfBirth, user.Gender, user.Email,
		user.MedicalHistory, user.RolAccount, patientID)

	if err != nil {
		log.Printf("Error updating user: %v", err)
		http.Error(w, "Database error", http.StatusInternalServerError)
		return
	}

	if result.RowsAffected() == 0 {
		http.Error(w, "User not found", http.StatusNotFound)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"message": "User updated successfully"})
}

func (s *Server) handleDeleteUser(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodDelete {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	patientID := strings.TrimPrefix(r.URL.Path, "/api/users/")
	if patientID == "" {
		http.Error(w, "Patient ID required", http.StatusBadRequest)
		return
	}

	// Eliminar usuario de PostgreSQL
	query := `DELETE FROM user_information WHERE patient_id = $1`

	result, err := s.PostgresDB.Exec(r.Context(), query, patientID)
	if err != nil {
		log.Printf("Error deleting user: %v", err)
		http.Error(w, "Database error", http.StatusInternalServerError)
		return
	}

	if result.RowsAffected() == 0 {
		http.Error(w, "User not found", http.StatusNotFound)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"message": "User deleted successfully"})
}

// Handlers para datos de series de tiempo (InfluxDB)
func (s *Server) handleGetGPSData(w http.ResponseWriter, r *http.Request) {
	patientID := r.URL.Query().Get("patient_id")
	limit := r.URL.Query().Get("limit")
	if limit == "" {
		limit = "100"
	}

	query := fmt.Sprintf(`from(bucket:"my_app_raw_data")
		|> range(start: -24h)
		|> filter(fn: (r) => r["_measurement"] == "gps_data")
		|> filter(fn: (r) => r["patient_id"] == "%s")
		|> limit(n: %s)`, patientID, limit)

	result, err := s.InfluxAPI.Query(r.Context(), query)
	if err != nil {
		log.Printf("Error querying GPS data: %v", err)
		http.Error(w, "InfluxDB error", http.StatusInternalServerError)
		return
	}
	defer result.Close()

	var gpsData []GPSData
	for result.Next() {
		record := result.Record()
		if record.Value() != nil {
			// Parsear los datos según la estructura de InfluxDB
			patientID := record.ValueByKey("patient_id").(string)
			lat, _ := strconv.ParseFloat(record.ValueByKey("latitude").(string), 64)
			lon, _ := strconv.ParseFloat(record.ValueByKey("longitude").(string), 64)

			gpsData = append(gpsData, GPSData{
				PatientID: patientID,
				Latitude:  lat,
				Longitude: lon,
				Timestamp: record.Time(),
			})
		}
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]any{"gps_data": gpsData})
}

func (s *Server) handleGetVitalSigns(w http.ResponseWriter, r *http.Request) {
	patientID := r.URL.Query().Get("patient_id")
	limit := r.URL.Query().Get("limit")
	if limit == "" {
		limit = "100"
	}

	query := fmt.Sprintf(`from(bucket:"my_app_raw_data")
		|> range(start: -24h)
		|> filter(fn: (r) => r["_measurement"] == "vital_signs")
		|> filter(fn: (r) => r["patient_id"] == "%s")
		|> limit(n: %s)`, patientID, limit)

	result, err := s.InfluxAPI.Query(r.Context(), query)
	if err != nil {
		log.Printf("Error querying vital signs: %v", err)
		http.Error(w, "InfluxDB error", http.StatusInternalServerError)
		return
	}
	defer result.Close()

	var vitals []VitalSigns
	for result.Next() {
		record := result.Record()
		if record.Value() != nil {
			patientID := record.ValueByKey("patient_id").(string)
			hr, _ := strconv.Atoi(record.ValueByKey("heart_rate").(string))
			bo, _ := strconv.Atoi(record.ValueByKey("blood_oxygen").(string))
			temp, _ := strconv.ParseFloat(record.ValueByKey("temperature").(string), 64)

			vitals = append(vitals, VitalSigns{
				PatientID:   patientID,
				HeartRate:   hr,
				BloodOxygen: bo,
				Temperature: temp,
				Timestamp:   record.Time(),
			})
		}
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]any{"vital_signs": vitals})
}

func (s *Server) handleGetKPIs(w http.ResponseWriter, r *http.Request) {
	patientID := r.URL.Query().Get("patient_id")
	limit := r.URL.Query().Get("limit")
	if limit == "" {
		limit = "100"
	}

	query := fmt.Sprintf(`from(bucket:"my_app_processed_data")
		|> range(start: -7d)
		|> filter(fn: (r) => r["_measurement"] == "kpi_risk")
		|> filter(fn: (r) => r["patient_id"] == "%s")
		|> limit(n: %s)`, patientID, limit)

	result, err := s.InfluxAPI.Query(r.Context(), query)
	if err != nil {
		log.Printf("Error querying KPIs: %v", err)
		http.Error(w, "InfluxDB error", http.StatusInternalServerError)
		return
	}
	defer result.Close()

	var kpis []KPIRisk
	for result.Next() {
		record := result.Record()
		if record.Value() != nil {
			patientID := record.ValueByKey("patient_id").(string)
			riskScore, _ := strconv.ParseFloat(record.ValueByKey("risk_score").(string), 64)
			category := record.ValueByKey("category").(string)

			kpis = append(kpis, KPIRisk{
				PatientID: patientID,
				RiskScore: riskScore,
				Category:  category,
				Timestamp: record.Time(),
			})
		}
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]any{"kpi_risk": kpis})
}

func (s *Server) handleHealth(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	_ = json.NewEncoder(w).Encode(map[string]any{"status": "healthy", "service": "backend-admin-crud"})
}

func (s *Server) handleUserDashboard(w http.ResponseWriter, r *http.Request) {
	patientID := r.URL.Query().Get("patient_id")
	if patientID == "" {
		http.Error(w, "Patient ID required", http.StatusBadRequest)
		return
	}

	// Obtener información del usuario
	var user User
	userQuery := `SELECT patient_id, name, date_of_birth, gender, email, medical_history, rol_account FROM user_information WHERE patient_id = $1`

	err := s.PostgresDB.QueryRow(r.Context(), userQuery, patientID).Scan(
		&user.PatientID, &user.Name, &user.DateOfBirth, &user.Gender,
		&user.Email, &user.MedicalHistory, &user.RolAccount)

	if err != nil {
		if err == sql.ErrNoRows {
			http.Error(w, "User not found", http.StatusNotFound)
			return
		}
		log.Printf("Error getting user: %v", err)
		http.Error(w, "Database error", http.StatusInternalServerError)
		return
	}

	// Obtener datos recientes de GPS, vitals y KPIs
	// (Aquí podrías implementar las consultas a InfluxDB para obtener datos resumidos)

	dashboard := map[string]interface{}{
		"user_info": user,
		"summary": map[string]interface{}{
			"total_gps_records": 0,   // Implementar contador real
			"total_vitals":      0,   // Implementar contador real
			"latest_risk_score": 0.0, // Implementar valor real
		},
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(dashboard)
}

func main() {
	// Configuración de PostgreSQL
	pgURL := os.Getenv("PG_URL")
	if pgURL == "" {
		pgURL = "postgres://hoonigans:666@my-postgres:5432/General%20information%20users"
	}

	// Configuración de InfluxDB
	influxURL := os.Getenv("INFLUX_URL")
	if influxURL == "" {
		influxURL = "http://my-influxdb:8086"
	}

	influxToken := os.Getenv("INFLUX_TOKEN")
	if influxToken == "" {
		influxToken = "admin:Trodat74"
	}

	influxOrg := os.Getenv("INFLUX_ORG")
	if influxOrg == "" {
		influxOrg = "my-org"
	}

	ctx := context.Background()

	// Conectar a PostgreSQL
	postgresPool, err := pgxpool.New(ctx, pgURL)
	if err != nil {
		log.Fatalf("PostgreSQL connection error: %v", err)
	}
	defer postgresPool.Close()

	// Conectar a InfluxDB
	influxClient := influxdb2.NewClient(influxURL, influxToken)
	defer influxClient.Close()

	// Verificar conexión a InfluxDB
	health, err := influxClient.Health(ctx)
	if err != nil {
		log.Printf("Warning: InfluxDB health check failed: %v", err)
	} else {
		log.Printf("InfluxDB status: %s", health.Status)
	}

	influxAPI := influxClient.QueryAPI(influxOrg)

	s := &Server{
		PostgresDB: postgresPool,
		InfluxDB:   influxClient,
		InfluxAPI:  influxAPI,
	}

	// Rutas para CRUD de usuarios
	http.HandleFunc("/api/users", func(w http.ResponseWriter, r *http.Request) {
		switch r.Method {
		case http.MethodGet:
			s.handleGetUsers(w, r)
		case http.MethodPost:
			s.handleCreateUser(w, r)
		default:
			http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		}
	})

	http.HandleFunc("/api/users/", func(w http.ResponseWriter, r *http.Request) {
		if strings.HasSuffix(r.URL.Path, "/") {
			http.Error(w, "Invalid patient ID", http.StatusBadRequest)
			return
		}

		switch r.Method {
		case http.MethodGet:
			s.handleGetUser(w, r)
		case http.MethodPut:
			s.handleUpdateUser(w, r)
		case http.MethodDelete:
			s.handleDeleteUser(w, r)
		default:
			http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		}
	})

	// Rutas para datos de series de tiempo
	http.HandleFunc("/api/gps", s.handleGetGPSData)
	http.HandleFunc("/api/vitals", s.handleGetVitalSigns)
	http.HandleFunc("/api/kpis", s.handleGetKPIs)

	// Ruta para dashboard del usuario
	http.HandleFunc("/api/dashboard", s.handleUserDashboard)

	// Health check
	http.HandleFunc("/health", s.handleHealth)

	// Serve static admin UI
	http.Handle("/", http.FileServer(http.Dir("ui")))

	addr := ":5004"
	log.Printf("Admin CRUD backend listening on %s", addr)
	log.Printf("Connected to PostgreSQL: %s", pgURL)
	log.Printf("Connected to InfluxDB: %s", influxURL)
	log.Fatal(http.ListenAndServe(addr, nil))
}
