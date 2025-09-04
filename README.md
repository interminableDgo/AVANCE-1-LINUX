# 🚀 SISTEMA HÍBRIDO: Backend CRUD + Microservicios

## 📋 Descripción del Proyecto

Este es un **sistema híbrido completo** que combina un **Backend CRUD integrado** desarrollado en **Go** con **microservicios** implementados en **Python**. El sistema está diseñado para manejar datos de salud y monitoreo en tiempo real, incluyendo métricas GPS, signos vitales y KPIs de riesgo.

## 🏗️ Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                    SISTEMA HÍBRIDO                         │
├─────────────────────────────────────────────────────────────┤
│  🔧 Backend CRUD Integrado (Puerto 5004)                   │
│     ├── Comunicación directa con bases de datos           │
│     ├── CRUD completo de usuarios                         │
│     ├── Acceso directo a GPS, vitals, KPIs               │
│     └── API REST completa                                 │
├─────────────────────────────────────────────────────────────┤
│  📱 Microservicios (Puertos 5000-5003)                    │
│     ├── AltaDeDatos (5000) - Ingesta de datos            │
│     ├── CalculoMetricas (5001) - Procesamiento           │
│     ├── Dashboards (5002) - Visualización                 │
│     └── InicioSesion (5003) - Autenticación              │
├─────────────────────────────────────────────────────────────┤
│  🗄️ Bases de Datos                                        │
│     ├── PostgreSQL (5432) - Usuarios y datos relacionales │
│     ├── InfluxDB (8086) - Series de tiempo               │
│     └── Redis (6379) - Caché y sesiones                  │
└─────────────────────────────────────────────────────────────┘
```

## ✨ Características Principales

- 🔧 **Backend CRUD Integrado**: API completa en Go con acceso directo a bases de datos
- 📱 **Microservicios Modulares**: Arquitectura distribuida en Python para funcionalidades específicas
- 🗄️ **Múltiples Bases de Datos**: PostgreSQL, InfluxDB y Redis para diferentes tipos de datos
- 📊 **Datos en Tiempo Real**: Monitoreo continuo de GPS, signos vitales y métricas
- 🧪 **Simulación Inteligente**: Generador de datos de prueba realistas
- 🐳 **Dockerizado**: Contenedores para fácil despliegue y escalabilidad
- 🌐 **Multiplataforma**: Funciona en Windows y Linux

## 🚀 Instalación Rápida

### Para Windows (Desarrollo Local)
```bash
# Ejecutar el script de inicio
iniciar_sistema_completo.bat
```

### Para Linux/Ubuntu (Producción)
```bash
# 1. Clonar el repositorio
git clone https://github.com/tu-usuario/sistema-hibrido-backend-microservicios.git
cd sistema-hibrido-backend-microservicios

# 2. Hacer ejecutable y ejecutar
chmod +x setup_and_run.sh
./setup_and_run.sh

# 3. Verificar funcionamiento
./test_linux_setup.sh
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

### Verificar Estado
```bash
# Ver contenedores Docker
docker ps

# Verificar servicios
netstat -tlnp | grep -E ':(5000|5001|5002|5003|5004|5432|8086|6379)'
```

### Probar APIs
```bash
# Backend CRUD
curl http://localhost:5004/health

# Microservicios
curl http://localhost:5000/  # AltaDeDatos
curl http://localhost:5001/  # CalculoMetricas
curl http://localhost:5002/  # Dashboards
curl http://localhost:5003/  # InicioSesion
```

## 🛠️ Tecnologías Utilizadas

### Backend
- **Go 1.22** - Backend CRUD principal
- **Python 3** - Microservicios
- **Flask** - Framework web para microservicios

### Bases de Datos
- **PostgreSQL** - Datos relacionales y usuarios
- **InfluxDB** - Series de tiempo y métricas
- **Redis** - Caché y sesiones

### Infraestructura
- **Docker** - Contenedores
- **Docker Compose** - Orquestación
- **Nginx** - Proxy reverso (opcional)

### Herramientas de Desarrollo
- **Git** - Control de versiones
- **Bash** - Scripts de automatización
- **Make** - Automatización de build

## 📁 Estructura del Proyecto

```
sistema-hibrido/
├── 📁 backend administrador/     # Backend Go CRUD
│   ├── cmd/server/               # Punto de entrada
│   ├── internal/                 # Lógica interna
│   └── go.mod                    # Dependencias Go
├── 📁 microservicios/            # Microservicios Python
│   ├── AltaDeDatos/             # Puerto 5000
│   ├── CalculoMetricas/         # Puerto 5001
│   ├── Dashboards/              # Puerto 5002
│   └── InicioSesion/            # Puerto 5003
├── 📁 Inicializacion/            # Scripts de BD y Docker
├── 📁 5 consultas complejas/     # Consultas SQL avanzadas
├── 🐳 docker-compose.yml         # Configuración de contenedores
├── 🐧 setup_and_run.sh           # Script de configuración Linux
├── 🧪 test_linux_setup.sh        # Script de pruebas Linux
├── 🚀 iniciar_sistema_completo.bat # Script de inicio Windows
└── 📚 README.md                  # Este archivo
```

## 🔧 Configuración

### Variables de Entorno
```bash
# PostgreSQL
POSTGRES_USER=hoonigans
POSTGRES_PASSWORD=666
POSTGRES_DB="General information users"

# InfluxDB
DOCKER_INFLUXDB_INIT_USERNAME=admin
DOCKER_INFLUXDB_INIT_PASSWORD=Trodat74
DOCKER_INFLUXDB_INIT_ORG=my-org
```

### Dependencias
- **Go**: 1.22 o superior
- **Python**: 3.8 o superior
- **Docker**: 20.10 o superior
- **Docker Compose**: 2.0 o superior

## 📈 Casos de Uso

### 🏥 Aplicaciones de Salud
- Monitoreo de signos vitales en tiempo real
- Seguimiento de actividad GPS de pacientes
- Cálculo de KPIs de riesgo cardiovascular
- Dashboard médico para profesionales de la salud

### 🏃‍♂️ Aplicaciones de Fitness
- Seguimiento de actividad física
- Análisis de patrones de movimiento
- Métricas de rendimiento deportivo
- Recomendaciones personalizadas

### 🏢 Aplicaciones Empresariales
- Monitoreo de flotas de vehículos
- Análisis de patrones de comportamiento
- Métricas de productividad
- Dashboard ejecutivo

## 🚨 Solución de Problemas

### Problemas Comunes
1. **Puertos ocupados**: Verificar que los puertos 5000-5004 estén libres
2. **Docker no inicia**: Verificar que Docker Desktop esté corriendo
3. **Errores de base de datos**: Verificar que los contenedores estén activos
4. **Dependencias faltantes**: Ejecutar `pip install -r requirements.txt`

### Logs y Debugging
```bash
# Ver logs de contenedores
docker-compose logs -f

# Ver logs de microservicios
tail -f microservicios/*.log

# Ver logs del backend
tail -f BackendGo.log
```

## 🤝 Contribuir

¡Las contribuciones son bienvenidas! Para contribuir:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 👥 Autores

- **Tu Nombre** - *Desarrollo inicial* - [TuUsuario](https://github.com/TuUsuario)

## 🙏 Agradecimientos

- Profesores del curso de Integración de Aplicaciones Computacionales
- Comunidad de desarrolladores de Go y Python
- Documentación de Docker y bases de datos

## 📞 Contacto

- **GitHub**: [@TuUsuario](https://github.com/TuUsuario)
- **Email**: tu-email@example.com
- **Proyecto**: [https://github.com/TuUsuario/sistema-hibrido-backend-microservicios](https://github.com/TuUsuario/sistema-hibrido-backend-microservicios)

---

⭐ **Si este proyecto te ayuda, ¡dale una estrella en GitHub!** ⭐

**Sistema Híbrido: Backend CRUD + Microservicios** - Desarrollado con ❤️ para la comunidad de desarrolladores.
