# Sistema de Monitoreo de Salud - Arquitectura Completa

Este sistema implementa una arquitectura de microservicios completa para el monitoreo de salud en tiempo real.

## 🏗️ Arquitectura del Sistema

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Reloj IoT     │───▶│  AltaDeDatos     │───▶│     Redis       │
│  (Simulador)    │    │  (Puerto 5000)   │    │  (Puerto 6379)  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │   InfluxDB       │
                       │ (Puerto 8086)    │
                       └──────────────────┘
                                │
                                ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │ CalculoMetricas  │───▶│   InfluxDB      │
                       │  (Puerto 5001)   │    │ (processed_data)│
                       └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │    Dashboards    │◀───│  Frontend       │
                       │  (Puerto 5002)   │    │ Usuario.html    │
                       └──────────────────┘    └─────────────────┘
                                ▲
                                │
                       ┌──────────────────┐
                       │  InicioSesion    │
                       │  (Puerto 5003)   │
                       └──────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │   PostgreSQL     │
                       │  (Puerto 5432)   │
                       └──────────────────┘
```

## 📁 Estructura de Archivos

```
├── microservicios/
│   ├── AltaDeDatos/
│   │   ├── app.py
│   │   ├── requirements.txt
│   │   └── README.md
│   ├── CalculoMetricas/
│   │   ├── app.py
│   │   ├── requirements.txt
│   │   └── README.md
│   ├── Dashboards/
│   │   ├── app.py
│   │   └── requirements.txt
│   └── InicioSesion/
│       ├── app.py
│       └── requirements.txt
├── Inicializacion/
│   ├── docker.yaml
│   └── init.sql
├── frontendUsuario.html
├── SimulacionSmartWatch_Microservicio.py
├── llenado_GPS_Vitals_30seg_InfluxBDbucket.py
└── llenado_KPIs_Risk_Diario_InfluxBDbucket.py
```

## 🚀 Microservicios

### 1. AltaDeDatos (Puerto 5000)
**Función**: Recibe datos del reloj inteligente y los almacena en Redis e InfluxDB

**Endpoints**:
- `POST /vitals` - Recibir datos del reloj
- `GET /vitals/<patient_id>` - Obtener datos de un paciente
- `POST /sync` - Sincronización manual
- `GET /health` - Estado del servicio

### 2. CalculoMetricas (Puerto 5001)
**Función**: Calcula métricas diarias y genera KPIs y análisis de riesgo

**Endpoints**:
- `POST /metrics/calculate` - Calcular métricas del día anterior
- `POST /metrics/calculate/<patient_id>` - Calcular para paciente específico
- `POST /metrics/batch` - Calcular para múltiples días
- `GET /health` - Estado del servicio

### 3. Dashboards (Puerto 5002)
**Función**: Sirve datos al frontend en formatos JSON y XML

**Endpoints**:
- `GET /api/current-vitals/<patient_id>` - Datos actuales (JSON)
- `GET /api/vitals-gps/<patient_id>` - Datos históricos Vitals/GPS (XML)
- `GET /api/kpis-risk/<patient_id>` - Datos KPIs/Risk (XML)
- `GET /health` - Estado del servicio

### 4. InicioSesion (Puerto 5003)
**Función**: Maneja autenticación y registro de usuarios

**Endpoints**:
- `GET /` - Página de inicio de sesión
- `GET /register` - Página de registro
- `POST /api/login` - Autenticación
- `POST /api/register` - Registro de usuarios
- `GET /health` - Estado del servicio

## 🗄️ Bases de Datos

### Redis (Puerto 6379)
- **Función**: Almacenamiento temporal de datos actuales
- **Estructura**: Hash con clave `patient_vitals:{patient_id}`
- **TTL**: 1 hora

### InfluxDB (Puerto 8086)
- **Buckets**:
  - `my_app_raw_data`: Datos crudos de GPS y Vitals
  - `my_app_processed_data`: KPIs y análisis de riesgo
- **Mediciones**:
  - `vitals`: heart_rate, systolic_bp, diastolic_bp
  - `gps`: lat, lon
  - `KPI_daily`: Métricas diarias calculadas
  - `Risk_inference`: Análisis de riesgo

### PostgreSQL (Puerto 5432)
- **Base de datos**: "General information users"
- **Tabla**: `users`
- **Campos**: patient_id, name, email, password, medical_history, etc.

## 🎨 Frontend

### frontendUsuario.html
- **Tecnologías**: Bootstrap 5, Highcharts, JavaScript
- **Características**:
  - Dashboard en tiempo real
  - Gráficos interactivos
  - Métricas actuales
  - Actualización automática cada 30 segundos
  - Diseño responsive y minimalista

## 🔧 Instalación y Configuración

### 1. Iniciar servicios de base de datos
```bash
docker-compose up -d
```

### 2. Instalar dependencias de microservicios
```bash
# AltaDeDatos
cd microservicios/AltaDeDatos
pip install -r requirements.txt

# CalculoMetricas
cd ../CalculoMetricas
pip install -r requirements.txt

# Dashboards
cd ../Dashboards
pip install -r requirements.txt

# InicioSesion
cd ../InicioSesion
pip install -r requirements.txt
```

### 3. Ejecutar microservicios
```bash
# Terminal 1 - AltaDeDatos
cd microservicios/AltaDeDatos
python app.py

# Terminal 2 - CalculoMetricas
cd microservicios/CalculoMetricas
python app.py

# Terminal 3 - Dashboards
cd microservicios/Dashboards
python app.py

# Terminal 4 - InicioSesion
cd microservicios/InicioSesion
python app.py
```

### 4. Ejecutar simulador de reloj
```bash
python SimulacionSmartWatch_Microservicio.py
```

### 5. Acceder al sistema
- **Inicio de sesión**: http://localhost:5003/
- **Dashboard**: http://localhost:5003/frontendUsuario.html

## 👤 Usuarios de Prueba

### Usuario existente (desde init.sql)
- **Email**: john.doe@example.com
- **Contraseña**: hashed_password
- **Patient ID**: 20250831-5f21-4f32-8e12-28e441467a18

### Nuevo usuario
- Registrarse en http://localhost:5003/register
- El sistema generará automáticamente un nuevo patient_id

## 📊 Flujo de Datos

1. **Reloj IoT** → Envía datos cada 30 segundos a **AltaDeDatos**
2. **AltaDeDatos** → Almacena en **Redis** y sincroniza con **InfluxDB**
3. **CalculoMetricas** → Procesa datos diariamente y genera KPIs/Risk
4. **Dashboards** → Sirve datos al frontend en tiempo real
5. **Frontend** → Muestra dashboard interactivo al usuario

## 🔐 Seguridad

- Contraseñas hasheadas con SHA-256
- Autenticación basada en sesiones
- Validación de datos en todos los endpoints
- Manejo de errores y logging

## 📈 Monitoreo

- Logs detallados en todos los microservicios
- Endpoints de salud (`/health`) para monitoreo
- Actualización automática de datos cada 30 segundos
- Procesamiento automático de métricas diarias a las 2:00 AM

## 🚨 Alertas

El sistema detecta automáticamente:
- Frecuencia cardíaca alta (>100 bpm)
- Presión arterial elevada (>140/90 mmHg)
- Tiempo sedentario excesivo (>12 horas)
- Scores de riesgo altos (>0.7)

## 🔄 Escalabilidad

- Arquitectura de microservicios independientes
- Cada servicio puede escalarse horizontalmente
- Bases de datos separadas por función
- APIs REST estándar para integración
