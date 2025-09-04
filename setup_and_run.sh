#!/bin/bash

# ========================================
#    SISTEMA COMPLETO HÍBRIDO - LINUX
#    Backend CRUD + Microservicios
# ========================================
# Script de configuración automática para Ubuntu/Debian
# Autor: Sistema de Integración de Aplicaciones Computacionales
# Fecha: $(date +%Y-%m-%d)

set -e  # Exit on any error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para logging
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

# Función para verificar si un comando existe
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Función para esperar que un servicio esté disponible
wait_for_service() {
    local host=$1
    local port=$2
    local service_name=$3
    local max_attempts=30
    local attempt=1
    
    log "Esperando que $service_name esté disponible en $host:$port..."
    
    while ! nc -z "$host" "$port" 2>/dev/null; do
        if [ $attempt -ge $max_attempts ]; then
            error "$service_name no está disponible después de $max_attempts intentos"
            return 1
        fi
        echo -n "."
        sleep 2
        ((attempt++))
    done
    echo ""
    success "$service_name está disponible"
}

# Función para verificar si Docker está corriendo
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        error "Docker no está corriendo. Por favor inicia Docker y vuelve a ejecutar este script."
        exit 1
    fi
    success "Docker está corriendo"
}

# Función para instalar prerrequisitos
install_prerequisites() {
    log "Instalando prerrequisitos del sistema..."
    
    # Actualizar sistema
    log "Actualizando sistema..."
    sudo apt update && sudo apt upgrade -y
    
    # Instalar paquetes básicos
    log "Instalando paquetes básicos..."
    sudo apt install -y curl wget git unzip software-properties-common apt-transport-https ca-certificates gnupg lsb-release netcat-openbsd
    
    # Instalar Docker si no está instalado
    if ! command_exists docker; then
        log "Instalando Docker..."
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
        echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
        sudo apt update
        sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
        
        # Agregar usuario actual al grupo docker
        sudo usermod -aG docker $USER
        success "Docker instalado. Por favor reinicia la sesión o ejecuta: newgrp docker"
    else
        success "Docker ya está instalado"
    fi
    
    # Instalar Docker Compose si no está instalado
    if ! command_exists docker-compose; then
        log "Instalando Docker Compose..."
        sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose
        success "Docker Compose instalado"
    else
        success "Docker Compose ya está instalado"
    fi
    
    # Instalar Go si no está instalado
    if ! command_exists go; then
        log "Instalando Go..."
        wget https://go.dev/dl/go1.22.0.linux-amd64.tar.gz
        sudo tar -C /usr/local -xzf go1.22.0.linux-amd64.tar.gz
        echo 'export PATH=$PATH:/usr/local/go/bin' >> ~/.bashrc
        export PATH=$PATH:/usr/local/go/bin
        rm go1.22.0.linux-amd64.tar.gz
        success "Go instalado"
    else
        success "Go ya está instalado"
    fi
    
    # Instalar Python si no está instalado
    if ! command_exists python3; then
        log "Instalando Python..."
        sudo apt install -y python3 python3-pip python3-venv
        success "Python instalado"
    else
        success "Python ya está instalado"
    fi
    
    # Instalar pip si no está instalado
    if ! command_exists pip3; then
        log "Instalando pip..."
        sudo apt install -y python3-pip
        success "pip instalado"
    else
        success "pip ya está instalado"
    fi
    
    # Crear enlaces simbólicos para python y pip
    if [ ! -f /usr/bin/python ]; then
        sudo ln -sf /usr/bin/python3 /usr/bin/python
    fi
    if [ ! -f /usr/bin/pip ]; then
        sudo ln -sf /usr/bin/pip3 /usr/bin/pip
    fi
}

# Función para configurar Docker Compose
setup_docker_compose() {
    log "Configurando Docker Compose..."
    
    # Crear archivo docker-compose.yml si no existe
    if [ ! -f "docker-compose.yml" ]; then
        log "Creando archivo docker-compose.yml..."
        cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  # Servicio de PostgreSQL para datos relacionales
  postgres:
    container_name: my-postgres
    image: postgres:latest
    ports:
      - "5432:5432"
    environment:
      POSTGRES_USER: hoonigans
      POSTGRES_PASSWORD: "666"
      POSTGRES_DB: "General information users"
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./Inicializacion/init.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U hoonigans"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Servicio de InfluxDB para todos los datos de series de tiempo
  influxdb:
    container_name: my-influxdb
    image: influxdb:latest
    ports:
      - "8086:8086"
    environment:
      DOCKER_INFLUXDB_INIT_MODE: setup
      DOCKER_INFLUXDB_INIT_USERNAME: admin
      DOCKER_INFLUXDB_INIT_PASSWORD: Trodat74
      DOCKER_INFLUXDB_INIT_ORG: my-org
      DOCKER_INFLUXDB_INIT_BUCKETS: my_app_raw_data,my_app_processed_data
      DOCKER_INFLUXDB_INIT_ADMIN_TOKEN: PpCwdSIMJdtVNgnnghBtDll0Q7KKRWzOm-LrSyCAOEo5jaVix2-NP0VPNkCoM_ztd4ZzsZzuyPi5Iuk9CD0ZCg==
    volumes:
      - influxdb-data:/var/lib/influxdb2
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8086/health"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7
    container_name: my-redis
    ports: ["6379:6379"]
    command: ["redis-server", "--appendonly", "yes"]
    volumes:
      - redis-data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres-data:
  influxdb-data:
  redis-data:
EOF
        success "Archivo docker-compose.yml creado"
    else
        success "Archivo docker-compose.yml ya existe"
    fi
}

# Función para crear script SQL personalizado
create_custom_sql() {
    log "Creando script SQL personalizado..."
    
    cat > Inicializacion/custom_init.sql << 'EOF'
-- Script SQL personalizado para la aplicación
-- Borrar tipos previos si existen
DROP TYPE IF EXISTS gender_enum CASCADE;
DROP TYPE IF EXISTS role_enum CASCADE;

-- Crear enums nuevos
CREATE TYPE gender_enum AS ENUM ('Masculino', 'Femenino', 'Otro', 'Prefiero no decir');
CREATE TYPE role_enum AS ENUM ('Usuario', 'Administrador');

-- Borrar tabla si ya existía
DROP TABLE IF EXISTS user_information CASCADE;

-- Crear tabla
CREATE TABLE user_information (
   patient_id UUID PRIMARY KEY,
   name VARCHAR(100) NOT NULL,
   date_of_birth DATE NOT NULL,
   gender gender_enum NOT NULL,
   email VARCHAR(150) UNIQUE NOT NULL,
   password VARCHAR(100) NOT NULL,
   medical_history TEXT,
   rol_account role_enum NOT NULL
);

-- Habilitar extensión pgcrypto si no existe
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Insertar usuario Juan (con UUID fijo)
INSERT INTO user_information (
   patient_id, name, date_of_birth, gender, email, password, medical_history, rol_account
) VALUES (
   '20250831-5f21-4f32-8e12-28e441467a18',
   'Juan',
   '1990-01-01',
   'Masculino',
   'juan@example.com',
   '1234',  -- contraseña sencilla
   'Sin antecedentes',
   'Usuario'
);

-- Insertar usuario Administrador (con UUID generado automáticamente)
INSERT INTO user_information (
   patient_id, name, date_of_birth, gender, email, password, medical_history, rol_account
) VALUES (
   gen_random_uuid(),
   'Administrador',
   '1985-01-01',
   'Masculino',
   'admin@example.com',
   'admin123',  -- contraseña sencilla
   'N/A',
   'Administrador'
);

-- Verificar que los usuarios estén creados
SELECT * FROM user_information;
EOF
    success "Script SQL personalizado creado"
}

# Función para levantar contenedores Docker
start_docker_containers() {
    log "Levantando contenedores Docker..."
    
    # Detener contenedores existentes si están corriendo
    if docker ps --format "table {{.Names}}" | grep -q "my-postgres\|my-influxdb\|my-redis"; then
        log "Deteniendo contenedores existentes..."
        docker-compose down
    fi
    
    # Levantar contenedores
    log "Iniciando contenedores..."
    docker-compose up -d
    
    # Esperar que los contenedores estén listos
    log "Esperando que los contenedores estén listos..."
    sleep 10
    
    # Verificar estado de los contenedores
    if docker ps --format "table {{.Names}}\t{{.Status}}" | grep -q "my-postgres\|my-influxdb\|my-redis"; then
        success "Contenedores Docker iniciados correctamente"
    else
        error "Error al iniciar contenedores Docker"
        exit 1
    fi
}

# Función para configurar InfluxDB
setup_influxdb() {
    log "Configurando InfluxDB..."
    
    # Esperar que InfluxDB esté disponible
    wait_for_service "localhost" "8086" "InfluxDB"
    
    # Crear buckets si no existen
    log "Verificando buckets de InfluxDB..."
    
    # Verificar bucket raw_data
    if ! curl -s "http://localhost:8086/api/v2/buckets?org=my-org" -H "Authorization: Token PpCwdSIMJdtVNgnnghBtDll0Q7KKRWzOm-LrSyCAOEo5jaVix2-NP0VPNkCoM_ztd4ZzsZzuyPi5Iuk9CD0ZCg==" | grep -q "my_app_raw_data"; then
        log "Creando bucket my_app_raw_data..."
        curl -X POST "http://localhost:8086/api/v2/buckets" \
            -H "Authorization: Token PpCwdSIMJdtVNgnnghBtDll0Q7KKRWzOm-LrSyCAOEo5jaVix2-NP0VPNkCoM_ztd4ZzsZzuyPi5Iuk9CD0ZCg==" \
            -H "Content-Type: application/json" \
            -d '{"name": "my_app_raw_data", "orgID": "my-org", "retentionRules": []}'
    fi
    
    # Verificar bucket processed_data
    if ! curl -s "http://localhost:8086/api/v2/buckets?org=my-org" -H "Authorization: Token PpCwdSIMJdtVNgnnghBtDll0Q7KKRWzOm-LrSyCAOEo5jaVix2-NP0VPNkCoM_ztd4ZzsZzuyPi5Iuk9CD0ZCg==" | grep -q "my_app_processed_data"; then
        log "Creando bucket my_app_processed_data..."
        curl -X POST "http://localhost:8086/api/v2/buckets" \
            -H "Authorization: Token PpCwdSIMJdtVNgnnghBtDll0Q7KKRWzOm-LrSyCAOEo5jaVix2-NP0VPNkCoM_ztd4ZzsZzuyPi5Iuk9CD0ZCg==" \
            -H "Content-Type: application/json" \
            -d '{"name": "my_app_processed_data", "orgID": "my-org", "retentionRules": []}'
    fi
    
    success "InfluxDB configurado correctamente"
}

# Función para configurar PostgreSQL
setup_postgresql() {
    log "Configurando PostgreSQL..."
    
    # Esperar que PostgreSQL esté disponible
    wait_for_service "localhost" "5432" "PostgreSQL"
    
    # Ejecutar script SQL personalizado
    log "Ejecutando script SQL personalizado..."
    docker exec -i my-postgres psql -U hoonigans -d "General information users" < Inicializacion/custom_init.sql
    
    success "PostgreSQL configurado correctamente"
}

# Función para instalar dependencias de Python
install_python_dependencies() {
    log "Instalando dependencias de Python..."
    
    # Crear entorno virtual si no existe
    if [ ! -d "venv" ]; then
        log "Creando entorno virtual de Python..."
        python3 -m venv venv
    fi
    
    # Activar entorno virtual
    source venv/bin/activate
    
    # Instalar dependencias comunes
    log "Instalando dependencias comunes..."
    pip install --upgrade pip
    pip install flask redis influxdb-client requests python-dotenv
    
    # Instalar dependencias específicas de cada microservicio
    log "Instalando dependencias de microservicios..."
    
    # AltaDeDatos
    if [ -f "microservicios/AltaDeDatos/requirements.txt" ]; then
        pip install -r microservicios/AltaDeDatos/requirements.txt
    fi
    
    # CalculoMetricas
    if [ -f "microservicios/CalculoMetricas/requirements.txt" ]; then
        pip install -r microservicios/CalculoMetricas/requirements.txt
    fi
    
    # Dashboards
    if [ -f "microservicios/Dashboards/requirements.txt" ]; then
        pip install -r microservicios/Dashboards/requirements.txt
    fi
    
    # InicioSesion
    if [ -f "microservicios/InicioSesion/requirements.txt" ]; then
        pip install -r microservicios/InicioSesion/requirements.txt
    fi
    
    success "Dependencias de Python instaladas"
}

# Función para llenar datos en InfluxDB
fill_influxdb_data() {
    log "Llenando datos en InfluxDB..."
    
    # Activar entorno virtual
    source venv/bin/activate
    
    # Ejecutar script de GPS y Vitals primero
    if [ -f "llenado_GPS_Vitals_30seg_InfluxBDbucket.py" ]; then
        log "Ejecutando script de GPS y Vitals..."
        python llenado_GPS_Vitals_30seg_InfluxBDbucket.py
        success "Datos de GPS y Vitals cargados"
    else
        warning "Script de GPS y Vitals no encontrado"
    fi
    
    # Ejecutar script de KPIs Risk Diario
    if [ -f "llenado_KPIs_Risk_Diario_InfluxBDbucket.py" ]; then
        log "Ejecutando script de KPIs Risk Diario..."
        python llenado_KPIs_Risk_Diario_InfluxBDbucket.py
        success "Datos de KPIs Risk Diario cargados"
    else
        warning "Script de KPIs Risk Diario no encontrado"
    fi
}

# Función para compilar backend Go
compile_go_backend() {
    log "Compilando backend Go..."
    
    cd "backend administrador"
    
    # Verificar que Go esté en el PATH
    if ! command_exists go; then
        export PATH=$PATH:/usr/local/go/bin
    fi
    
    # Compilar el backend
    if go build -o server ./cmd/server; then
        success "Backend Go compilado correctamente"
    else
        error "Error al compilar el backend Go"
        exit 1
    fi
    
    cd ..
}

# Función para iniciar microservicios
start_microservices() {
    log "Iniciando microservicios..."
    
    # Activar entorno virtual
    source venv/bin/activate
    
    # Función para iniciar un microservicio en background
    start_service() {
        local service_name=$1
        local service_path=$2
        local port=$3
        
        if [ -f "$service_path/app.py" ]; then
            log "Iniciando $service_name en puerto $port..."
            cd "$service_path"
            nohup python app.py > "../${service_name}.log" 2>&1 &
            cd - > /dev/null
            sleep 2
            success "$service_name iniciado en puerto $port"
        else
            warning "Archivo app.py no encontrado para $service_name"
        fi
    }
    
    # Iniciar microservicios
    start_service "AltaDeDatos" "microservicios/AltaDeDatos" "5000"
    start_service "CalculoMetricas" "microservicios/CalculoMetricas" "5001"
    start_service "Dashboards" "microservicios/Dashboards" "5002"
    start_service "InicioSesion" "microservicios/InicioSesion" "5003"
    
    # Iniciar simulador de reloj
    if [ -f "SimulacionSmartWatch_Microservicio.py" ]; then
        log "Iniciando simulador de reloj..."
        nohup python SimulacionSmartWatch_Microservicio.py > "SimuladorReloj.log" 2>&1 &
        success "Simulador de reloj iniciado"
    fi
}

# Función para iniciar backend Go
start_go_backend() {
    log "Iniciando backend Go..."
    
    cd "backend administrador"
    
    # Iniciar backend en background
    nohup ./server > "../BackendGo.log" 2>&1 &
    cd ..
    
    # Esperar que el backend esté disponible
    wait_for_service "localhost" "5004" "Backend Go"
    
    success "Backend Go iniciado en puerto 5004"
}

# Función para verificar estado del sistema
check_system_status() {
    log "Verificando estado del sistema..."
    
    echo ""
    echo "========================================"
    echo "    ESTADO DEL SISTEMA"
    echo "========================================"
    
    # Verificar contenedores Docker
    echo "🐳 Contenedores Docker:"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    
    echo ""
    echo "🔧 Servicios:"
    
    # Verificar microservicios
    for port in 5000 5001 5002 5003 5004; do
        if nc -z localhost $port 2>/dev/null; then
            echo "  ✅ Puerto $port: Activo"
        else
            echo "  ❌ Puerto $port: Inactivo"
        fi
    done
    
    echo ""
    echo "🗄️ Bases de Datos:"
    
    # Verificar PostgreSQL
    if docker exec my-postgres pg_isready -U hoonigans >/dev/null 2>&1; then
        echo "  ✅ PostgreSQL: Activo"
    else
        echo "  ❌ PostgreSQL: Inactivo"
    fi
    
    # Verificar InfluxDB
    if curl -s "http://localhost:8086/health" >/dev/null 2>&1; then
        echo "  ✅ InfluxDB: Activo"
    else
        echo "  ❌ InfluxDB: Inactivo"
    fi
    
    # Verificar Redis
    if docker exec my-redis redis-cli ping >/dev/null 2>&1; then
        echo "  ✅ Redis: Activo"
    else
        echo "  ❌ Redis: Activo"
    fi
}

# Función principal
main() {
    echo "========================================"
    echo "    SISTEMA COMPLETO HÍBRIDO - LINUX"
    echo "    Backend CRUD + Microservicios"
    echo "========================================"
    echo ""
    
    # Verificar si se ejecuta como root
    if [ "$EUID" -eq 0 ]; then
        error "No ejecutes este script como root. Usa un usuario normal con permisos sudo."
        exit 1
    fi
    
    # Verificar sistema operativo
    if ! grep -q "Ubuntu\|Debian" /etc/os-release; then
        warning "Este script está optimizado para Ubuntu/Debian. Puede no funcionar en otros sistemas."
    fi
    
    # Instalar prerrequisitos
    install_prerequisites
    
    # Verificar Docker
    check_docker
    
    # Configurar Docker Compose
    setup_docker_compose
    
    # Crear script SQL personalizado
    create_custom_sql
    
    # Levantar contenedores Docker
    start_docker_containers
    
    # Configurar bases de datos
    setup_influxdb
    setup_postgresql
    
    # Instalar dependencias de Python
    install_python_dependencies
    
    # Llenar datos en InfluxDB
    fill_influxdb_data
    
    # Compilar backend Go
    compile_go_backend
    
    # Iniciar microservicios
    start_microservices
    
    # Iniciar backend Go
    start_go_backend
    
    # Verificar estado del sistema
    check_system_status
    
    echo ""
    echo "========================================"
    echo "    🚀 SISTEMA COMPLETO INICIADO 🚀"
    echo "========================================"
    echo ""
    echo "El sistema ahora tiene ambas arquitecturas funcionando:"
    echo ""
    echo "🔧 Backend CRUD Integrado (Puerto 5004):"
    echo "   - Health Check: http://localhost:5004/health"
    echo "   - API Usuarios: http://localhost:5004/api/users"
    echo "   - UI Admin: http://localhost:5004/"
    echo ""
    echo "📱 Microservicios:"
    echo "   - AltaDeDatos: http://localhost:5000/"
    echo "   - CalculoMetricas: http://localhost:5001/"
    echo "   - Dashboards: http://localhost:5002/"
    echo "   - InicioSesion: http://localhost:5003/"
    echo ""
    echo "🗄️ Bases de Datos:"
    echo "   - PostgreSQL: localhost:5432 (usuarios)"
    echo "   - InfluxDB: localhost:8086 (datos de series de tiempo)"
    echo "   - Redis: localhost:6379 (caché)"
    echo ""
    echo "📋 Logs disponibles en:"
    echo "   - Backend Go: BackendGo.log"
    echo "   - Microservicios: microservicios/*.log"
    echo "   - Simulador: SimuladorReloj.log"
    echo ""
    echo "🧪 Para probar el sistema:"
    echo "   curl http://localhost:5004/health"
    echo "   curl http://localhost:5000/"
    echo ""
    echo "💡 El sistema está funcionando en modo híbrido:"
    echo "   ✅ Backend CRUD para operaciones directas"
    echo "   ✅ Microservicios para funcionalidades específicas"
    echo ""
    echo "¡Sistema listo para usar! 🎉"
}

# Ejecutar función principal
main "$@"
