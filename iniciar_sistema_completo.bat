@echo off
echo ========================================
echo    SISTEMA COMPLETO HÍBRIDO
echo    Backend CRUD + Microservicios
echo ========================================
echo.
echo Iniciando sistema completo con ambas arquitecturas...
echo.

echo [1/6] Verificando que Docker esté corriendo...
docker ps >nul 2>&1
if errorlevel 1 (
    echo   ERROR: Docker no está corriendo
    echo   Por favor inicia Docker Desktop y vuelve a ejecutar este script
    pause
    exit /b 1
) else (
    echo   OK: Docker está corriendo
)

echo.
echo [2/6] Verificando estado de contenedores existentes...
echo   Verificando si las bases de datos ya están corriendo...
docker ps --filter "name=my-postgres" --filter "name=my-influxdb" --filter "name=my-redis" --format "table {{.Names}}\t{{.Status}}" 2>nul

echo.
echo [3/6] Iniciando bases de datos (si no están corriendo)...
cd Inicializacion
docker-compose -f docker.yaml up -d 2>nul
if errorlevel 1 (
    echo   INFO: Algunos contenedores ya estaban corriendo (esto es normal)
) else (
    echo   OK: Bases de datos iniciadas
)
cd ..

echo   Esperando que las bases de datos estén listas...
timeout /t 5 /nobreak >nul

echo.
echo [4/6] Verificando conexiones a bases de datos...
echo   - Verificando PostgreSQL (puerto 5432)...
netstat -an | findstr ":5432" >nul
if errorlevel 1 (
    echo     WARNING: PostgreSQL no responde aún, esperando...
    timeout /t 5 /nobreak >nul
) else (
    echo     OK: PostgreSQL está respondiendo
)

echo   - Verificando InfluxDB (puerto 8086)...
netstat -an | findstr ":8086" >nul
if errorlevel 1 (
    echo     WARNING: InfluxDB no responde aún, esperando...
    timeout /t 5 /nobreak >nul
) else (
    echo     OK: InfluxDB está respondiendo
)

echo.
echo [5/6] Iniciando Backend Administrador CRUD (Puerto 5004)...
echo   Compilando backend Go...
cd "backend administrador"
go build -o server.exe ./cmd/server
if errorlevel 1 (
    echo   ERROR: No se pudo compilar el backend
    echo   Verifica que Go esté instalado y configurado
    pause
    exit /b 1
)

echo   Iniciando servidor CRUD...
start "AdminBackend-CRUD" cmd /k "server.exe"
cd ..

echo.
echo [6/6] Iniciando Microservicios en paralelo...
echo   Iniciando AltaDeDatos (Puerto 5000)...
start "AltaDeDatos" cmd /k "cd "%~dp0microservicios\AltaDeDatos" && python app.py"

timeout /t 2 /nobreak >nul

echo   Iniciando CalculoMetricas (Puerto 5001)...
start "CalculoMetricas" cmd /k "cd "%~dp0microservicios\CalculoMetricas" && python app.py"

timeout /t 2 /nobreak >nul

echo   Iniciando Dashboards (Puerto 5002)...
start "Dashboards" cmd /k "cd "%~dp0microservicios\Dashboards" && python app.py"

timeout /t 2 /nobreak >nul

echo   Iniciando InicioSesion (Puerto 5003)...
start "InicioSesion" cmd /k "cd "%~dp0microservicios\InicioSesion" && python app.py"

timeout /t 2 /nobreak >nul

echo   Iniciando Simulador de Reloj...
start "SimuladorReloj" cmd /k "cd "%~dp0" && python SimulacionSmartWatch_Microservicio.py"

echo.
echo ========================================
echo    SISTEMA COMPLETO HÍBRIDO INICIADO
echo ========================================
echo.
echo 🚀 **SISTEMA FUNCIONANDO EN MODO HÍBRIDO** 🚀
echo.
echo El sistema ahora tiene ambas arquitecturas funcionando:
echo.
echo 🔧 **Backend CRUD Integrado (Puerto 5004):**
echo   - Comunicación directa con bases de datos
echo   - CRUD completo de usuarios
echo   - Acceso directo a GPS, vitals, KPIs
echo   - Health Check: http://localhost:5004/health
echo   - API Usuarios: http://localhost:5004/api/users
echo   - UI Admin: http://localhost:5004/
echo.
echo 📱 **Microservicios (Puertos 5000-5003):**
echo   - AltaDeDatos: http://localhost:5000/
echo   - CalculoMetricas: http://localhost:5001/
echo   - Dashboards: http://localhost:5002/
echo   - InicioSesion: http://localhost:5003/
echo   - Simulador de Reloj: Funcionando
echo.
echo 🗄️ **Bases de Datos:**
echo   - PostgreSQL: localhost:5432 (usuarios)
echo   - InfluxDB: localhost:8086 (datos de series de tiempo)
echo   - Redis: localhost:6379 (caché)
echo.
echo 🧪 **Para Probar el Sistema:**
echo.
echo **Backend CRUD:**
echo   1. Abre http://localhost:5004/health
echo   2. Ejecuta: cd "backend administrador" && python test_api.py
echo.
echo **Microservicios:**
echo   1. Verifica que todos los puertos estén activos
echo   2. Prueba cada microservicio individualmente
echo.
echo 💡 **Ventajas del Modo Híbrido:**
echo   ✅ Puedes usar el backend CRUD para operaciones directas
echo   ✅ Mantienes los microservicios para funcionalidades específicas
echo   ✅ Flexibilidad para elegir qué usar según la necesidad
echo   ✅ Comparación de rendimiento entre ambas arquitecturas
echo.
echo ⚠️  **Nota:** Ahora tienes dos formas de acceder a los datos:
echo    - Directamente a través del backend CRUD (más rápido)
echo    - A través de los microservicios (más modular)
echo.
echo Presiona cualquier tecla para cerrar...
pause >nul
