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

# Wrapper para docker: usa sudo si es necesario
_docker() {
    if docker "$@" >/dev/null 2>&1; then
        docker "$@"
        return 0
    fi
    if sudo -n true >/dev/null 2>&1; then
        sudo docker "$@"
        return $?
    fi
    sudo docker "$@"
}

# Wrapper para docker compose vs docker-compose
_compose() {
    if command_exists docker && docker compose version >/dev/null 2>&1; then
        docker compose "$@"
    elif command_exists docker-compose; then
        docker-compose "$@"
    else
        error "Docker Compose no está instalado"
        exit 1
    fi
}

# Función para esperar que un servicio TCP esté disponible
wait_for_service() {
    local host=$1
    local port=$2
    local service_name=$3
    local max_attempts=${4:-90}
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

# Iniciar servicio Docker si está detenido y validar acceso
ensure_docker_running() {
    log "Verificando servicio Docker..."
    if ! _docker info >/dev/null 2>&1; then
        if command_exists systemctl; then
            sudo systemctl enable --now docker >/dev/null 2>&1 || true
        fi
        if command_exists service; then
            sudo service docker start >/dev/null 2>&1 || true
        fi
        sleep 2
    fi

    if _docker info >/dev/null 2>&1; then
        success "Docker está corriendo"
    else
        warning "Docker podría estar corriendo pero sin permisos para tu usuario. Intentando con sudo."
        if sudo docker info >/dev/null 2>&1; then
            success "Acceso a Docker disponible vía sudo"
        else
            error "Docker no está disponible. Inícialo manualmente: sudo systemctl start docker"
            exit 1
        fi
    fi
}

# Función para instalar prerrequisitos
install_prerequisites() {
    log "Instalando prerrequisitos del sistema..."
    
    log "Actualizando sistema..."
    sudo apt update && sudo apt upgrade -y
    
    log "Instalando paquetes básicos..."
    sudo apt install -y curl wget git unzip software-properties-common apt-transport-https ca-certificates gnupg lsb-release netcat-openbsd
    
    if [ -f /etc/os-release ]; then
        . /etc/os-release
    fi
    DOCKER_DIST="ubuntu"
    DOCKER_CODENAME="${UBUNTU_CODENAME:-$(lsb_release -cs || true)}"
    if [ "${ID}" = "debian" ] || grep -qi debian /etc/os-release 2>/dev/null; then
        DOCKER_DIST="debian"
        DOCKER_CODENAME="${VERSION_CODENAME:-$(lsb_release -cs || true)}"
    fi

    if ! command_exists docker; then
        log "Instalando Docker (${DOCKER_DIST} ${DOCKER_CODENAME})..."
        curl -fsSL https://download.docker.com/linux/${DOCKER_DIST}/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
        if [ -f /etc/apt/sources.list.d/docker.list ]; then
            sudo rm -f /etc/apt/sources.list.d/docker.list
        fi
        echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/${DOCKER_DIST} ${DOCKER_CODENAME} stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
        sudo apt update
        sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
        sudo usermod -aG docker $USER || true
        success "Docker instalado. Si es tu primera instalación, reinicia sesión o ejecuta: newgrp docker"
    else
        success "Docker ya está instalado"
    fi
    
    if ! command_exists docker-compose; then
        if command_exists docker && docker compose version >/dev/null 2>&1; then
            success "Docker Compose (plugin) disponible"
        else
            log "Instalando Docker Compose standalone..."
            sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
            sudo chmod +x /usr/local/bin/docker-compose
            success "Docker Compose standalone instalado"
        fi
    else
        success "Docker Compose standalone ya está instalado"
    fi
    
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
    
    if ! command_exists python3; then
        log "Instalando Python..."
        sudo apt install -y python3 python3-pip python3-venv
        success "Python instalado"
    else
        success "Python ya está instalado"
    fi
    
    if ! command_exists pip3; then
        log "Instalando pip..."
        sudo apt install -y python3-pip
        success "pip instalado"
    else
        success "pip ya está instalado"
    fi
    
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
    
    if [ ! -f "docker-compose.yml" ]; then
        log "Creando archivo docker-compose.yml..."
        cat > docker-compose.yml << 'EOF'
services:
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
      retries: 20
      start_period: 30s

  influxdb:
    container_name: my-influxdb
    image: influxdb:2.7
    ports:
      - "8086:8086"
    environment:
      DOCKER_INFLUXDB_INIT_MODE: setup
      DOCKER_INFLUXDB_INIT_USERNAME: admin
      DOCKER_INFLUXDB_INIT_PASSWORD: Trodat74
      DOCKER_INFLUXDB_INIT_ORG: my-org
      DOCKER_INFLUXDB_INIT_BUCKET: my_app_raw_data
      DOCKER_INFLUXDB_INIT_ADMIN_TOKEN: PpCwdSIMJdtVNgnnghBtDll0Q7KKRWzOm-LrSyCAOEo5jaVix2-NP0VPNkCoM_ztd4ZzsZzuyPi5Iuk9CD0ZCg==
    volumes:
      - influxdb-data:/var/lib/influxdb2
      - influxdb-config:/etc/influxdb2
    healthcheck:
      test: ["CMD-SHELL", "curl -fsS http://localhost:8086/health || exit 1"]
      interval: 10s
      timeout: 5s
      retries: 60
      start_period: 180s

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
      retries: 20
      start_period: 10s

volumes:
  postgres-data:
  influxdb-data:
  influxdb-config:
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
DROP TYPE IF EXISTS gender_enum CASCADE;
DROP TYPE IF EXISTS role_enum CASCADE;
CREATE TYPE gender_enum AS ENUM ('Masculino', 'Femenino', 'Otro', 'Prefiero no decir');
CREATE TYPE role_enum AS ENUM ('Usuario', 'Administrador');
DROP TABLE IF EXISTS user_information CASCADE;
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
CREATE EXTENSION IF NOT EXISTS pgcrypto;
INSERT INTO user_information (
   patient_id, name, date_of_birth, gender, email, password, medical_history, rol_account
) VALUES (
   '20250831-5f21-4f32-8e12-28e441467a18', 'Juan', '1990-01-01', 'Masculino', 'juan@example.com', '1234', 'Sin antecedentes', 'Usuario'
);
INSERT INTO user_information (
   patient_id, name, date_of_birth, gender, email, password, medical_history, rol_account
) VALUES (
   gen_random_uuid(), 'Administrador', '1985-01-01', 'Masculino', 'admin@example.com', 'admin123', 'N/A', 'Administrador'
);
SELECT * FROM user_information;
EOF
    success "Script SQL personalizado creado"
}

wait_container_healthy() {
    local name=$1
    local timeout=${2:-300}
    local waited=0
    log "Esperando salud del contenedor '$name' (hasta ${timeout}s)..."
    while true; do
        status=$(_docker inspect --format='{{if .State.Health}}{{.State.Health.Status}}{{else}}unknown{{end}}' "$name" 2>/dev/null || echo "unknown")
        if [ "$status" = "healthy" ]; then
            success "Contenedor '$name' healthy"
            return 0
        fi
        if [ "$status" = "unhealthy" ]; then
            warning "Contenedor '$name' unhealthy"
            return 2
        fi
        sleep 2
        waited=$((waited+2))
        if [ $waited -ge $timeout ]; then
            warning "Timeout esperando salud del contenedor '$name' (estado: $status)"
            return 1
        fi
    done
}

recover_influx_if_needed() {
    warning "Intentando recuperación de InfluxDB (recrear volumen y contenedor)"
    _compose rm -fsv influxdb || true
    # eliminar cualquier volumen del proyecto que termine en _influxdb-data o _influxdb-config
    for vol in $(_docker volume ls --format '{{.Name}}' | grep -E '_influxdb-(data|config)$' || true); do
        _docker volume rm "$vol" || true
    done
    _compose up -d influxdb
    wait_container_healthy my-influxdb 480 || true
}

start_docker_containers() {
    log "Levantando contenedores Docker..."
    
    if _docker ps --format "table {{.Names}}" | grep -q "my-postgres\|my-influxdb\|my-redis"; then
        log "Deteniendo contenedores existentes..."
        _compose down || true
    fi
    
    log "Iniciando contenedores..."
    _compose up -d
    
    wait_container_healthy my-postgres 180 || true
    if ! wait_container_healthy my-influxdb 480; then
        recover_influx_if_needed
    fi
    wait_container_healthy my-redis 180 || true

    if _docker ps --format "table {{.Names}}\t{{.Status}}" | grep -q "my-postgres\|my-influxdb\|my-redis"; then
        success "Contenedores Docker iniciados correctamente"
    else
        error "Error al iniciar contenedores Docker"
        exit 1
    fi
}

setup_influxdb() {
    log "Configurando InfluxDB..."
    # Preferir estado healthy; luego validar puerto
    wait_container_healthy my-influxdb 180 || true
    wait_for_service "localhost" "8086" "InfluxDB" 180 || true
    success "InfluxDB configurado (bucket inicial creado por docker-compose)"
}

setup_postgresql() {
    log "Configurando PostgreSQL..."
    wait_for_service "localhost" "5432" "PostgreSQL" 180 || true
    log "Ejecutando script SQL personalizado..."
    _docker exec -i my-postgres psql -U hoonigans -d "General information users" < Inicializacion/custom_init.sql
    success "PostgreSQL configurado correctamente"
}

install_python_dependencies() {
    log "Instalando dependencias de Python..."
    if [ ! -d "venv" ]; then
        log "Creando entorno virtual de Python..."
        python3 -m venv venv
    fi
    source venv/bin/activate
    log "Instalando dependencias comunes..."
    pip install --upgrade pip
    pip install flask redis influxdb-client requests python-dotenv
    log "Instalando dependencias de microservicios..."
    if [ -f "microservicios/AltaDeDatos/requirements.txt" ]; then
        pip install -r microservicios/AltaDeDatos/requirements.txt
    fi
    if [ -f "microservicios/CalculoMetricas/requirements.txt" ]; then
        pip install -r microservicios/CalculoMetricas/requirements.txt
    fi
    if [ -f "microservicios/Dashboards/requirements.txt" ]; then
        pip install -r microservicios/Dashboards/requirements.txt
    fi
    if [ -f "microservicios/InicioSesion/requirements.txt" ]; then
        pip install -r microservicios/InicioSesion/requirements.txt
    fi
    success "Dependencias de Python instaladas"
}

fill_influxdb_data() {
    log "Llenando datos en InfluxDB..."
    source venv/bin/activate
    if [ -f "llenado_GPS_Vitals_30seg_InfluxBDbucket.py" ]; then
        log "Ejecutando script de GPS y Vitals..."
        python llenado_GPS_Vitals_30seg_InfluxBDbucket.py
        success "Datos de GPS y Vitals cargados"
    else
        warning "Script de GPS y Vitals no encontrado"
    fi
    if [ -f "llenado_KPIs_Risk_Diario_InfluxBDbucket.py" ]; then
        log "Ejecutando script de KPIs Risk Diario..."
        python llenado_KPIs_Risk_Diario_InfluxBDbucket.py
        success "Datos de KPIs Risk Diario cargados"
    else
        warning "Script de KPIs Risk Diario no encontrado"
    fi
}

compile_go_backend() {
    log "Compilando backend Go..."
    cd "backend administrador"
    if ! command_exists go; then
        export PATH=$PATH:/usr/local/go/bin
    fi
    if go build -o server ./cmd/server; then
        success "Backend Go compilado correctamente"
    else
        error "Error al compilar el backend Go"
        exit 1
    fi
    cd ..
}

start_microservices() {
    log "Iniciando microservicios..."
    source venv/bin/activate
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
    start_service "AltaDeDatos" "microservicios/AltaDeDatos" "5000"
    start_service "CalculoMetricas" "microservicios/CalculoMetricas" "5001"
    start_service "Dashboards" "microservicios/Dashboards" "5002"
    start_service "InicioSesion" "microservicios/InicioSesion" "5003"
    if [ -f "SimulacionSmartWatch_Microservicio.py" ]; then
        log "Iniciando simulador de reloj..."
        nohup python SimulacionSmartWatch_Microservicio.py > "SimuladorReloj.log" 2>&1 &
        success "Simulador de reloj iniciado"
    fi
}

start_go_backend() {
    log "Iniciando backend Go..."
    cd "backend administrador"
    nohup ./server > "../BackendGo.log" 2>&1 &
    cd ..
    wait_for_service "localhost" "5004" "Backend Go" 180 || true
    success "Backend Go iniciado en puerto 5004"
}

check_system_status() {
    log "Verificando estado del sistema..."
    echo ""
    echo "========================================"
    echo "    ESTADO DEL SISTEMA"
    echo "========================================"
    echo "🐳 Contenedores Docker:"
    _docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    echo ""
    echo "🔧 Servicios:"
    for port in 5000 5001 5002 5003 5004; do
        if nc -z localhost $port 2>/dev/null; then
            echo "  ✅ Puerto $port: Activo"
        else
            echo "  ❌ Puerto $port: Inactivo"
        fi
    done
    echo ""
    echo "🗄️ Bases de Datos:"
    if _docker exec my-postgres pg_isready -U hoonigans >/dev/null 2>&1; then
        echo "  ✅ PostgreSQL: Activo"
    else
        echo "  ❌ PostgreSQL: Inactivo"
    fi
    if curl -s "http://localhost:8086/health" >/dev/null 2>&1; then
        echo "  ✅ InfluxDB: Activo"
    else
        echo "  ❌ InfluxDB: Inactivo"
    fi
    if _docker exec my-redis redis-cli ping >/dev/null 2>&1; then
        echo "  ✅ Redis: Activo"
    else
        echo "  ❌ Redis: Activo"
    fi
}

main() {
    echo "========================================"
    echo "    SISTEMA COMPLETO HÍBRIDO - LINUX"
    echo "    Backend CRUD + Microservicios"
    echo "========================================"
    echo ""
    if [ "$EUID" -eq 0 ]; then
        error "No ejecutes este script como root. Usa un usuario normal con permisos sudo."
        exit 1
    fi
    if ! grep -q "Ubuntu\|Debian" /etc/os-release; then
        warning "Este script está optimizado para Ubuntu/Debian. Puede no funcionar en otros sistemas."
    fi
    install_prerequisites
    ensure_docker_running
    setup_docker_compose
    create_custom_sql
    start_docker_containers
    setup_influxdb
    setup_postgresql
    install_python_dependencies
    fill_influxdb_data
    compile_go_backend
    start_microservices
    start_go_backend
    check_system_status
    echo ""
    echo "========================================"
    echo "    🚀 SISTEMA COMPLETO INICIADO 🚀"
    echo "========================================"
    echo ""
    echo "🔧 Backend CRUD Integrado (Puerto 5004): http://localhost:5004/"
    echo "📱 Microservicios: 5000-5003"
    echo "🗄️ Bases de Datos: PostgreSQL 5432, InfluxDB 8086, Redis 6379"
}

main "$@"
