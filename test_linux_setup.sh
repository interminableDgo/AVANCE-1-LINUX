#!/bin/bash

# ========================================
#    SCRIPT DE PRUEBA - LINUX SETUP
# ========================================
# Script para verificar que todos los servicios estén funcionando

set -e

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

# Función para verificar puerto
check_port() {
    local port=$1
    local service_name=$2
    
    if nc -z localhost $port 2>/dev/null; then
        success "$service_name (puerto $port): Activo"
        return 0
    else
        error "$service_name (puerto $port): Inactivo"
        return 1
    fi
}

# Función para verificar contenedor Docker
check_container() {
    local container_name=$1
    local service_name=$2
    
    if docker ps --format "{{.Names}}" | grep -q "^$container_name$"; then
        success "$service_name ($container_name): Activo"
        return 0
    else
        error "$service_name ($container_name): Inactivo"
        return 1
    fi
}

# Función principal de pruebas
main() {
    echo "========================================"
    echo "    PRUEBAS DEL SISTEMA LINUX"
    echo "========================================"
    echo ""
    
    local all_tests_passed=true
    
    log "Verificando contenedores Docker..."
    echo ""
    
    # Verificar contenedores Docker
    check_container "my-postgres" "PostgreSQL" || all_tests_passed=false
    check_container "my-influxdb" "InfluxDB" || all_tests_passed=false
    check_container "my-redis" "Redis" || all_tests_passed=false
    
    echo ""
    log "Verificando puertos de servicios..."
    echo ""
    
    # Verificar puertos de servicios
    check_port "5000" "AltaDeDatos" || all_tests_passed=false
    check_port "5001" "CalculoMetricas" || all_tests_passed=false
    check_port "5002" "Dashboards" || all_tests_passed=false
    check_port "5003" "InicioSesion" || all_tests_passed=false
    check_port "5004" "Backend Go" || all_tests_passed=false
    
    echo ""
    log "Verificando puertos de bases de datos..."
    echo ""
    
    # Verificar puertos de bases de datos
    check_port "5432" "PostgreSQL" || all_tests_passed=false
    check_port "8086" "InfluxDB" || all_tests_passed=false
    check_port "6379" "Redis" || all_tests_passed=false
    
    echo ""
    log "Verificando APIs..."
    echo ""
    
    # Verificar APIs con curl y timeout integrado
    curl --silent --show-error --max-time 5 http://localhost:5004/health >/dev/null && success "Backend Go Health: Responde correctamente" || { warning "Backend Go Health: No responde"; all_tests_passed=false; }
    curl --silent --show-error --max-time 5 http://localhost:5000/ >/dev/null && success "AltaDeDatos: Responde correctamente" || { warning "AltaDeDatos: No responde"; all_tests_passed=false; }
    curl --silent --show-error --max-time 5 http://localhost:5001/ >/dev/null && success "CalculoMetricas: Responde correctamente" || { warning "CalculoMetricas: No responde"; all_tests_passed=false; }
    curl --silent --show-error --max-time 5 http://localhost:5002/ >/dev/null && success "Dashboards: Responde correctamente" || { warning "Dashboards: No responde"; all_tests_passed=false; }
    curl --silent --show-error --max-time 5 http://localhost:5003/ >/dev/null && success "InicioSesion: Responde correctamente" || { warning "InicioSesion: No responde"; all_tests_passed=false; }
    
    echo ""
    log "Verificando bases de datos..."
    echo ""
    
    # Verificar PostgreSQL
    if docker exec my-postgres pg_isready -U hoonigans >/dev/null 2>&1; then
        success "PostgreSQL: Conexión exitosa"
    else
        error "PostgreSQL: Error de conexión"
        all_tests_passed=false
    fi
    
    # Verificar InfluxDB
    if curl -s "http://localhost:8086/health" >/dev/null 2>&1; then
        success "InfluxDB: Health check exitoso"
    else
        error "InfluxDB: Health check falló"
        all_tests_passed=false
    fi
    
    # Verificar Redis
    if docker exec my-redis redis-cli ping >/dev/null 2>&1; then
        success "Redis: Ping exitoso"
    else
        error "Redis: Ping falló"
        all_tests_passed=false
    fi
    
    echo ""
    log "Verificando archivos de log..."
    echo ""
    
    # Verificar archivos de log
    if [ -f "BackendGo.log" ]; then
        success "BackendGo.log: Existe"
    else
        warning "BackendGo.log: No encontrado"
    fi
    
    if [ -f "SimuladorReloj.log" ]; then
        success "SimuladorReloj.log: Existe"
    else
        warning "SimuladorReloj.log: No encontrado"
    fi
    
    # Verificar logs de microservicios
    for service in AltaDeDatos CalculoMetricas Dashboards InicioSesion; do
        if [ -f "microservicios/${service}.log" ]; then
            success "${service}.log: Existe"
        else
            warning "${service}.log: No encontrado"
        fi
    done
    
    echo ""
    echo "========================================"
    echo "    RESUMEN DE PRUEBAS"
    echo "========================================"
    echo ""
    
    if [ "$all_tests_passed" = true ]; then
        success "🎉 ¡TODAS LAS PRUEBAS PASARON! El sistema está funcionando correctamente."
        echo ""
        echo "🔧 Servicios activos:"
        echo "   - Backend CRUD (Puerto 5004): http://localhost:5004/"
        echo "   - Microservicios (Puertos 5000-5003): Funcionando"
        echo "   - Bases de datos: PostgreSQL, InfluxDB, Redis"
        echo ""
        echo "🧪 Para probar manualmente:"
        echo "   curl http://localhost:5004/health"
        echo "   curl http://localhost:5000/"
        echo "   curl http://localhost:5001/"
        echo "   curl http://localhost:5002/"
        echo "   curl http://localhost:5003/"
    else
        error "❌ ALGUNAS PRUEBAS FALLARON. Revisa los errores arriba."
        echo ""
        echo "🔍 Para diagnosticar problemas:"
        echo "   docker ps                    # Ver contenedores"
        echo "   docker logs my-postgres      # Logs de PostgreSQL"
        echo "   docker logs my-influxdb     # Logs de InfluxDB"
        echo "   docker logs my-redis        # Logs de Redis"
        echo "   tail -f BackendGo.log       # Logs del backend"
        echo "   tail -f microservicios/*.log # Logs de microservicios"
    fi
    
    echo ""
    echo "========================================"
}

# Ejecutar función principal
main "$@"
