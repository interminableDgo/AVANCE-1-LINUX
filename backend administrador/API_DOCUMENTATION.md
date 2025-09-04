# API Documentation - Backend Administrador CRUD

Este backend de Go se comunica directamente con PostgreSQL, InfluxDB y Redis, evitando los microservicios y funcionando como un CRUD completo.

## Endpoints Disponibles

### 1. Health Check
- **GET** `/health`
- **Descripción**: Verifica el estado del servicio
- **Respuesta**: `{"status": "healthy", "service": "backend-admin-crud"}`

### 2. CRUD de Usuarios

#### Obtener todos los usuarios
- **GET** `/api/users`
- **Descripción**: Lista todos los usuarios registrados
- **Respuesta**: Array de usuarios con información completa

#### Crear usuario
- **POST** `/api/users`
- **Body**:
```json
{
  "patient_id": "uuid-string",
  "name": "John Doe",
  "date_of_birth": "1980-01-01T00:00:00Z",
  "gender": "male",
  "email": "john@example.com",
  "password": "hashed_password",
  "medical_history": "Hypertension",
  "rol_account": "patient"
}
```
- **Respuesta**: `{"message": "User created successfully", "patient_id": "uuid"}`

#### Obtener usuario específico
- **GET** `/api/users/{patient_id}`
- **Descripción**: Obtiene información de un usuario específico
- **Respuesta**: Objeto usuario completo

#### Actualizar usuario
- **PUT** `/api/users/{patient_id}`
- **Body**: Mismo formato que crear usuario (sin password)
- **Respuesta**: `{"message": "User updated successfully"}`

#### Eliminar usuario
- **DELETE** `/api/users/{patient_id}`
- **Descripción**: Elimina un usuario del sistema
- **Respuesta**: `{"message": "User deleted successfully"}`

### 3. Datos de Series de Tiempo (InfluxDB)

#### Datos GPS
- **GET** `/api/gps?patient_id={patient_id}&limit={limit}`
- **Parámetros**:
  - `patient_id`: ID del paciente (requerido)
  - `limit`: Número máximo de registros (opcional, default: 100)
- **Respuesta**: Array de datos GPS con latitud, longitud y timestamp

#### Signos Vitales
- **GET** `/api/vitals?patient_id={patient_id}&limit={limit}`
- **Parámetros**: Igual que GPS
- **Respuesta**: Array de signos vitales (ritmo cardíaco, oxigenación, temperatura)

#### KPIs de Riesgo
- **GET** `/api/kpis?patient_id={patient_id}&limit={limit}`
- **Parámetros**: Igual que GPS
- **Respuesta**: Array de KPIs de riesgo con score y categoría

### 4. Dashboard de Usuario
- **GET** `/api/dashboard?patient_id={patient_id}`
- **Descripción**: Vista consolidada de información del usuario y métricas
- **Respuesta**: Información del usuario + resumen de datos

## Estructuras de Datos

### User
```go
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
```

### GPSData
```go
type GPSData struct {
    PatientID string    `json:"patient_id"`
    Latitude  float64   `json:"latitude"`
    Longitude float64   `json:"longitude"`
    Timestamp time.Time `json:"timestamp"`
}
```

### VitalSigns
```go
type VitalSigns struct {
    PatientID   string    `json:"patient_id"`
    HeartRate   int       `json:"heart_rate"`
    BloodOxygen int       `json:"blood_oxygen"`
    Temperature float64   `json:"temperature"`
    Timestamp   time.Time `json:"timestamp"`
}
```

### KPIRisk
```go
type KPIRisk struct {
    PatientID string    `json:"patient_id"`
    RiskScore float64   `json:"risk_score"`
    Category  string    `json:"category"`
    Timestamp time.Time `json:"timestamp"`
}
```

## Configuración de Base de Datos

### Variables de Entorno
- `PG_URL`: URL de conexión a PostgreSQL (default: postgres://hoonigans:666@localhost:5432/General%20information%20users)
- `INFLUX_URL`: URL de InfluxDB (default: http://localhost:8086)
- `INFLUX_TOKEN`: Token de autenticación (default: admin:Trodat74)
- `INFLUX_ORG`: Organización de InfluxDB (default: my-org)

### Conexiones
- **PostgreSQL**: Puerto 5432
- **InfluxDB**: Puerto 8086
- **Redis**: Puerto 6379 (configurado pero no implementado aún)

## Ejemplos de Uso

### Crear un nuevo usuario
```bash
curl -X POST http://localhost:5004/api/users \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "20250831-5f21-4f32-8e12-28e441467a18",
    "name": "Jane Smith",
    "email": "jane@example.com",
    "rol_account": "patient"
  }'
```

### Obtener datos GPS de un usuario
```bash
curl "http://localhost:5004/api/gps?patient_id=20250831-5f21-4f32-8e12-28e441467a18&limit=50"
```

### Obtener dashboard de usuario
```bash
curl "http://localhost:5004/api/dashboard?patient_id=20250831-5f21-4f32-8e12-28e441467a18"
```

## Notas Importantes

1. **Autenticación**: Actualmente no implementada, se puede agregar middleware de autenticación
2. **Validación**: Se valida que los campos requeridos estén presentes
3. **Manejo de Errores**: Respuestas HTTP apropiadas para diferentes tipos de errores
4. **Logging**: Logs detallados para debugging
5. **Conexiones**: Manejo automático de conexiones a múltiples bases de datos

## Próximos Pasos Sugeridos

1. Implementar autenticación JWT
2. Agregar validación más robusta de datos
3. Implementar caché con Redis
4. Agregar paginación para listas grandes
5. Implementar filtros avanzados para consultas
6. Agregar métricas y monitoreo
