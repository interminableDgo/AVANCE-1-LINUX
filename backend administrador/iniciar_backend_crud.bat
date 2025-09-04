@echo off
echo ========================================
echo    Backend Administrador CRUD
echo ========================================
echo.
echo Iniciando el backend CRUD que se comunica
echo directamente con las bases de datos...
echo.

REM Verificar si el ejecutable existe
if not exist "server.exe" (
    echo Compilando el backend...
    go build -o server.exe ./cmd/server
    if errorlevel 1 (
        echo Error al compilar el backend
        pause
        exit /b 1
    )
    echo Compilacion exitosa!
    echo.
)

REM Verificar que las bases de datos esten corriendo
echo Verificando conexiones a bases de datos...
echo.

REM Verificar PostgreSQL
echo - Verificando PostgreSQL (puerto 5432)...
netstat -an | findstr ":5432" >nul
if errorlevel 1 (
    echo   WARNING: PostgreSQL no parece estar corriendo en puerto 5432
    echo   Asegurate de que el contenedor Docker este activo
) else (
    echo   OK: PostgreSQL detectado en puerto 5432
)

REM Verificar InfluxDB
echo - Verificando InfluxDB (puerto 8086)...
netstat -an | findstr ":8086" >nul
if errorlevel 1 (
    echo   WARNING: InfluxDB no parece estar corriendo en puerto 8086
    echo   Asegurate de que el contenedor Docker este activo
) else (
    echo   OK: InfluxDB detectado en puerto 8086
)

echo.
echo Iniciando el servidor en puerto 5004...
echo.
echo Endpoints disponibles:
echo   - Health Check: http://localhost:5004/health
echo   - API Usuarios: http://localhost:5004/api/users
echo   - API GPS: http://localhost:5004/api/gps
echo   - API Vitals: http://localhost:5004/api/vitals
echo   - API KPIs: http://localhost:5004/api/kpis
echo   - Dashboard: http://localhost:5004/api/dashboard
echo   - UI Admin: http://localhost:5004/
echo.
echo Presiona Ctrl+C para detener el servidor
echo ========================================
echo.

REM Iniciar el servidor
server.exe

echo.
echo Servidor detenido.
pause
