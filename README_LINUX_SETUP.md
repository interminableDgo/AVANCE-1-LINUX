# 🐧 SISTEMA COMPLETO HÍBRIDO - SETUP LINUX

## 📋 Descripción

Este proyecto es un sistema híbrido que combina un **Backend CRUD integrado** con **microservicios**, diseñado para funcionar en entornos Linux (Ubuntu/Debian). El sistema incluye bases de datos PostgreSQL, InfluxDB y Redis, junto con microservicios en Python y un backend en Go.

## 🚀 Instalación Automática

### Prerrequisitos

- **Sistema Operativo**: Ubuntu 20.04+ o Debian 11+
- **RAM**: Mínimo 4GB (recomendado 8GB+)
- **Almacenamiento**: Mínimo 20GB de espacio libre
- **Usuario**: Usuario normal con permisos sudo (NO ejecutar como root)

### Instalación en 3 Pasos

1. **Clonar el repositorio**
   ```bash
   git clone <tu-repositorio-github>
   cd <nombre-del-proyecto>
   ```

2. **Hacer ejecutable el script**
   ```bash
   chmod +x setup_and_run.sh
   ```

3. **Ejecutar el script de configuración**
   ```bash
   ./setup_and_run.sh
   ```

## 🔧 Qué Hace el Script Automáticamente

### 1. Instalación de Prerrequisitos
- ✅ Actualiza el sistema (`apt update && apt upgrade`)
- ✅ Instala paquetes básicos (curl, wget, git, netcat, etc.)
- ✅ Instala Docker y Docker Compose
- ✅ Instala Go 1.22
- ✅ Instala Python 3 y pip
- ✅ Configura enlaces simbólicos

### 2. Configuración de Contenedores
- ✅ Crea `docker-compose.yml` optimizado
- ✅ Levanta contenedores para PostgreSQL, InfluxDB y Redis
- ✅ Configura health checks y volúmenes persistentes
- ✅ Mapea puertos correctamente (5432, 8086, 6379)

### 3. Configuración de Bases de Datos
- ✅ **PostgreSQL**: Crea base de datos, tabla `user_information` con enums personalizados
- ✅ **InfluxDB**: Crea buckets `my_app_raw_data` y `my_app_processed_data`
- ✅ **Redis**: Configura con persistencia habilitada

### 4. Llenado de Datos
- ✅ Ejecuta script de GPS y Vitals (30 segundos)
- ✅ Ejecuta script de KPIs Risk Diario
- ✅ Crea datos de prueba para 1 semana completa

### 5. Inicio de Servicios
- ✅ Compila backend Go
- ✅ Inicia microservicios Python en puertos 5000-5003
- ✅ Inicia backend Go en puerto 5004
- ✅ Inicia simulador de reloj inteligente

## 🏗️ Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                    SISTEMA HÍBRIDO                         │
├─────────────────────────────────────────────────────────────┤
│  🔧 Backend CRUD Integrado (Puerto 5004)                   │
│     ├── Comunicación directa con bases de datos           │
│     ├── CRUD completo de usuarios                         │
│     └── Acceso directo a GPS, vitals, KPIs               │
├─────────────────────────────────────────────────────────────┤
│  📱 Microservicios (Puertos 5000-5003)                    │
│     ├── AltaDeDatos (5000)                                │
│     ├── CalculoMetricas (5001)                            │
│     ├── Dashboards (5002)                                 │
│     └── InicioSesion (5003)                               │
├─────────────────────────────────────────────────────────────┤
│  🗄️ Bases de Datos                                        │
│     ├── PostgreSQL (5432) - Usuarios                      │
│     ├── InfluxDB (8086) - Series de tiempo               │
│     └── Redis (6379) - Caché                              │
└─────────────────────────────────────────────────────────────┘
```

## 📊 Puertos y Servicios

| Puerto | Servicio | Descripción |
|--------|----------|-------------|
| 5000 | AltaDeDatos | Microservicio para ingesta de datos |
| 5001 | CalculoMetricas | Microservicio para procesamiento de métricas |
| 5002 | Dashboards | Microservicio para visualización |
| 5003 | InicioSesion | Microservicio de autenticación |
| 5004 | Backend Go | Backend CRUD integrado |
| 5432 | PostgreSQL | Base de datos relacional |
| 8086 | InfluxDB | Base de datos de series de tiempo |
| 6379 | Redis | Base de datos en memoria |

## 🧪 Pruebas del Sistema

### Verificar Estado General
```bash
# Verificar contenedores Docker
docker ps

# Verificar servicios activos
netstat -tlnp | grep -E ':(5000|5001|5002|5003|5004|5432|8086|6379)'
```

### Probar Backend CRUD
```bash
# Health check
curl http://localhost:5004/health

# Listar usuarios
curl http://localhost:5004/api/users

# Probar UI Admin
# Abrir en navegador: http://localhost:5004/
```

### Probar Microservicios
```bash
# AltaDeDatos
curl http://localhost:5000/

# CalculoMetricas
curl http://localhost:5001/

# Dashboards
curl http://localhost:5002/

# InicioSesion
curl http://localhost:5003/
```

### Probar Bases de Datos
```bash
# PostgreSQL
docker exec -it my-postgres psql -U hoonigans -d "General information users" -c "SELECT * FROM user_information;"

# InfluxDB
curl "http://localhost:8086/health"

# Redis
docker exec -it my-redis redis-cli ping
```

## 📋 Logs y Monitoreo

### Archivos de Log
- `BackendGo.log` - Logs del backend Go
- `microservicios/*.log` - Logs de cada microservicio
- `SimuladorReloj.log` - Logs del simulador

### Monitoreo en Tiempo Real
```bash
# Ver logs de contenedores Docker
docker-compose logs -f

# Ver logs de microservicios
tail -f microservicios/*.log

# Ver logs del backend
tail -f BackendGo.log
```

## 🔄 Reinstalación y Mantenimiento

### Reiniciar Todo el Sistema
```bash
# Detener todos los servicios
docker-compose down
pkill -f "python.*app.py"
pkill -f "server"

# Ejecutar script nuevamente
./setup_and_run.sh
```

### Actualizar Solo Microservicios
```bash
# Detener microservicios
pkill -f "python.*app.py"

# Reinstalar dependencias
source venv/bin/activate
pip install -r microservicios/*/requirements.txt

# Reiniciar microservicios
./setup_and_run.sh
```

### Limpiar Datos
```bash
# Eliminar contenedores y volúmenes
docker-compose down -v

# Eliminar entorno virtual
rm -rf venv

# Ejecutar script completo
./setup_and_run.sh
```

## 🚨 Solución de Problemas

### Error: Docker no está corriendo
```bash
# Iniciar Docker
sudo systemctl start docker
sudo systemctl enable docker

# Agregar usuario al grupo docker
sudo usermod -aG docker $USER
newgrp docker
```

### Error: Puerto ya en uso
```bash
# Ver qué proceso usa el puerto
sudo netstat -tlnp | grep :5000

# Terminar proceso
sudo kill -9 <PID>
```

### Error: Permisos de archivo
```bash
# Hacer ejecutable el script
chmod +x setup_and_run.sh

# Verificar permisos
ls -la setup_and_run.sh
```

### Error: Dependencias Python
```bash
# Recrear entorno virtual
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r microservicios/*/requirements.txt
```

## 📚 Estructura de Archivos

```
proyecto/
├── setup_and_run.sh              # Script principal de configuración
├── docker-compose.yml            # Configuración de contenedores
├── README_LINUX_SETUP.md         # Este archivo
├── Inicializacion/
│   ├── custom_init.sql           # Script SQL personalizado
│   └── init.sql                  # Script SQL original
├── backend administrador/        # Backend Go
├── microservicios/               # Microservicios Python
├── venv/                         # Entorno virtual Python
└── logs/                         # Archivos de log
```

## 🎯 Características del Script

- ✅ **Idempotente**: Puede ejecutarse múltiples veces sin problemas
- ✅ **Manejo de errores**: Verifica cada paso y muestra mensajes claros
- ✅ **Colores**: Output colorido para mejor legibilidad
- ✅ **Logs detallados**: Registra cada acción del proceso
- ✅ **Verificaciones**: Confirma que cada servicio esté funcionando
- ✅ **Compatibilidad**: Optimizado para Ubuntu/Debian
- ✅ **Seguridad**: No ejecuta como root, usa usuario normal

## 🆘 Soporte

Si encuentras problemas:

1. **Verifica los logs**: Revisa los archivos de log para errores específicos
2. **Verifica el estado**: Usa `docker ps` y `netstat` para diagnosticar
3. **Revisa permisos**: Asegúrate de que el usuario tenga permisos sudo
4. **Verifica puertos**: Confirma que los puertos no estén en uso
5. **Revisa dependencias**: Verifica que Docker, Go y Python estén instalados

## 🎉 ¡Listo!

Una vez ejecutado el script, tendrás un sistema completo funcionando con:

- 🔧 Backend CRUD integrado en Go
- 📱 Microservicios en Python
- 🗄️ Bases de datos configuradas y llenas de datos
- 📊 Dashboard y APIs funcionando
- 🧪 Datos de prueba para desarrollo

¡El sistema está listo para usar en modo híbrido! 🚀
