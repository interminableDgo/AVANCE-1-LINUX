# Backend Administrador CRUD

Este backend de Go se comunica directamente con múltiples bases de datos (PostgreSQL, InfluxDB, Redis) evitando los microservicios y funcionando como un CRUD completo para el sistema de monitoreo de salud.

## 🚀 Características Principales

- **CRUD Completo de Usuarios**: Crear, leer, actualizar y eliminar usuarios
- **Acceso Directo a Bases de Datos**: Sin dependencia de microservicios
- **Múltiples Fuentes de Datos**:
  - PostgreSQL para información de usuarios
  - InfluxDB para datos de series de tiempo (GPS, vitals, KPIs)
  - Redis para caché (configurado pero no implementado aún)
- **API RESTful**: Endpoints bien definidos y documentados
- **Dashboard Integrado**: Vista consolidada de información del usuario

## 🏗️ Arquitectura

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend UI   │    │   Backend Go    │    │   PostgreSQL    │
│   (HTML/JS)     │◄──►│   (CRUD API)    │◄──►│   (Users)       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │    InfluxDB     │
                       │ (GPS, Vitals,   │
                       │  KPIs)          │
                       └─────────────────┘
```

## 📋 Requisitos

- Go 1.19+
- PostgreSQL 12+
- InfluxDB 2.0+
- Redis 6+ (opcional)

## 🛠️ Instalación

1. **Clonar y navegar al directorio**:
   ```bash
   cd "backend administrador"
   ```

2. **Instalar dependencias**:
   ```bash
   go mod tidy
   ```

3. **Configurar variables de entorno** (opcional):
   ```bash
   # Copiar archivo de ejemplo
   cp env.example .env
   
   # Editar variables según tu configuración
   ```

4. **Compilar**:
   ```bash
   go build -o server.exe ./cmd/server
   ```

## 🚀 Ejecución

### Opción 1: Ejecutar directamente
```bash
./server.exe
```

### Opción 2: Ejecutar con Go
```bash
go run ./cmd/server
```

### Opción 3: Ejecutar en background
```bash
nohup ./server.exe > server.log 2>&1 &
```

## 🌐 Endpoints Disponibles

### Usuarios (CRUD)
- `GET /api/users` - Listar todos los usuarios
- `POST /api/users` - Crear nuevo usuario
- `GET /api/users/{id}` - Obtener usuario específico
- `PUT /api/users/{id}` - Actualizar usuario
- `DELETE /api/users/{id}` - Eliminar usuario

### Datos de Series de Tiempo
- `GET /api/gps?patient_id={id}&limit={n}` - Datos GPS
- `GET /api/vitals?patient_id={id}&limit={n}` - Signos vitales
- `GET /api/kpis?patient_id={id}&limit={n}` - KPIs de riesgo

### Dashboard y Utilidades
- `GET /api/dashboard?patient_id={id}` - Dashboard del usuario
- `GET /health` - Health check del servicio

## 🧪 Pruebas

### Ejecutar Script de Pruebas
```bash
# Instalar requests si no está instalado
pip install requests

# Ejecutar pruebas
python test_api.py
```

### Pruebas Manuales con curl

**Crear usuario**:
```bash
curl -X POST http://localhost:5004/api/users \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "test-123",
    "name": "Test User",
    "email": "test@example.com",
    "rol_account": "patient"
  }'
```

**Obtener usuarios**:
```bash
curl http://localhost:5004/api/users
```

**Obtener datos GPS**:
```bash
curl "http://localhost:5004/api/gps?patient_id=test-123&limit=10"
```

## ⚙️ Configuración

### Variables de Entorno
- `PG_URL`: URL de PostgreSQL (default: postgres://hoonigans:666@localhost:5432/General%20information%20users)
- `INFLUX_URL`: URL de InfluxDB (default: http://localhost:8086)
- `INFLUX_TOKEN`: Token de InfluxDB (default: admin:Trodat74)
- `INFLUX_ORG`: Organización de InfluxDB (default: my-org)

### Puertos por Defecto
- **Backend**: 5004
- **PostgreSQL**: 5432
- **InfluxDB**: 8086
- **Redis**: 6379

## 📊 Estructura de Datos

### Usuario (PostgreSQL)
```sql
CREATE TABLE users (
    patient_id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255),
    date_of_birth DATE,
    gender gender_enum,
    email VARCHAR(255),
    password VARCHAR(255),
    medical_history TEXT,
    rol_account rol_enum
);
```

### Datos de Series de Tiempo (InfluxDB)
- **GPS**: `gps_data` measurement con campos `latitude`, `longitude`
- **Vitals**: `vital_signs` measurement con campos `heart_rate`, `blood_oxygen`, `temperature`
- **KPIs**: `kpi_risk` measurement con campos `risk_score`, `category`

## 🔧 Desarrollo

### Estructura del Proyecto
```
cmd/server/
├── main.go          # Punto de entrada principal
├── handlers.go      # Manejadores HTTP (opcional)
└── models.go        # Estructuras de datos (opcional)

internal/            # Lógica interna (opcional)
├── database/        # Conexiones a BD
├── auth/           # Autenticación
└── middleware/     # Middleware HTTP

ui/                 # Frontend estático
├── index.html
└── assets/
```

### Agregar Nuevos Endpoints

1. **Definir estructura de datos** en `main.go`
2. **Crear handler function** con la lógica
3. **Registrar ruta** en la función `main()`
4. **Documentar** en `API_DOCUMENTATION.md`

### Ejemplo de Nuevo Endpoint
```go
func (s *Server) handleNewFeature(w http.ResponseWriter, r *http.Request) {
    // Lógica del endpoint
    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(map[string]string{"message": "Success"})
}

// En main():
http.HandleFunc("/api/new-feature", s.handleNewFeature)
```

## 🚨 Solución de Problemas

### Error de Conexión a PostgreSQL
```bash
# Verificar que PostgreSQL esté corriendo
docker ps | grep postgres

# Verificar credenciales
docker exec -it my-postgres psql -U hoonigans -d "General information users"
```

### Error de Conexión a InfluxDB
```bash
# Verificar que InfluxDB esté corriendo
docker ps | grep influxdb

# Verificar health check
curl http://localhost:8086/health
```

### Puerto ya en uso
```bash
# Cambiar puerto en el código o
# Liberar puerto 5004
netstat -ano | findstr :5004
taskkill /PID <PID> /F
```

## 📈 Monitoreo y Logs

### Logs del Servidor
- Los logs se muestran en la consola
- Para logs persistentes: `./server.exe > server.log 2>&1`

### Métricas de Salud
- Endpoint `/health` para verificar estado
- Verificar conexiones a bases de datos en logs de inicio

## 🔮 Próximos Pasos

1. **Autenticación JWT**: Implementar sistema de login seguro
2. **Caché Redis**: Optimizar consultas frecuentes
3. **Validación Avanzada**: Validar datos de entrada más robustamente
4. **Paginación**: Implementar paginación para listas grandes
5. **Filtros**: Agregar filtros avanzados para consultas
6. **Métricas**: Implementar métricas de rendimiento
7. **Tests Unitarios**: Agregar tests automatizados

## 📚 Documentación Adicional

- [API_DOCUMENTATION.md](API_DOCUMENTATION.md) - Documentación completa de la API
- [env.example](env.example) - Ejemplo de variables de entorno
- [test_api.py](test_api.py) - Script de pruebas automatizadas

## 🤝 Contribución

1. Fork el proyecto
2. Crear rama para feature (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir Pull Request

## 📄 Licencia

Este proyecto es parte del sistema de monitoreo de salud de la Universidad de Monterrey.
