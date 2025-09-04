# 🚀 QUICK START - LINUX

## ⚡ Instalación Rápida en 3 Comandos

```bash
# 1. Hacer ejecutable el script
chmod +x setup_and_run.sh

# 2. Ejecutar configuración automática
./setup_and_run.sh

# 3. Verificar que todo funcione
./test_linux_setup.sh
```

## 🔍 Verificar Estado del Sistema

```bash
# Ver contenedores Docker
docker ps

# Ver servicios activos
netstat -tlnp | grep -E ':(5000|5001|5002|5003|5004|5432|8086|6379)'

# Ver logs en tiempo real
docker-compose logs -f
```

## 🧪 Pruebas Rápidas

```bash
# Backend CRUD
curl http://localhost:5004/health

# Microservicios
curl http://localhost:5000/  # AltaDeDatos
curl http://localhost:5001/  # CalculoMetricas
curl http://localhost:5002/  # Dashboards
curl http://localhost:5003/  # InicioSesion
```

## 🆘 Si Algo Falla

```bash
# Reiniciar todo
docker-compose down
./setup_and_run.sh

# Ver logs de errores
docker logs my-postgres
docker logs my-influxdb
docker logs my-redis
tail -f BackendGo.log
```

## 📱 Acceso Web

- **Backend Admin**: http://localhost:5004/
- **AltaDeDatos**: http://localhost:5000/
- **CalculoMetricas**: http://localhost:5001/
- **Dashboards**: http://localhost:5002/
- **InicioSesion**: http://localhost:5003/

¡Listo! 🎉
