# 🚀 Instrucciones para Probar el Sistema

## **Paso 1: Verificar que Docker esté corriendo**
```bash
docker ps
```
Debes ver los contenedores de Redis, InfluxDB y PostgreSQL corriendo.

## **Paso 2: Iniciar el Sistema Completo**

### **Opción A: Usar el script automático (Recomendado)**
```bash
# Doble clic en el archivo:
iniciar_sistema.bat
```

### **Opción B: Iniciar manualmente (4 terminales)**
```bash
# Terminal 1 - AltaDeDatos
cd microservicios\AltaDeDatos
python app.py

# Terminal 2 - CalculoMetricas  
cd microservicios\CalculoMetricas
python app.py

# Terminal 3 - Dashboards
cd microservicios\Dashboards
python app.py

# Terminal 4 - InicioSesion
cd microservicios\InicioSesion
python app.py

# Terminal 5 - Simulador de Reloj
python SimulacionSmartWatch_Microservicio.py
```

## **Paso 3: Acceder al Sistema**

### **🌐 Abrir el navegador y ir a:**
- **Inicio de Sesión**: http://localhost:5003/
- **Dashboard**: http://localhost:5003/frontendUsuario.html

### **👤 Usuario de Prueba:**
- **Email**: `john.doe@example.com`
- **Contraseña**: `hashed_password`

## **Paso 4: Probar Funcionalidades**

### **✅ Autenticación:**
1. Ir a http://localhost:5003/
2. Iniciar sesión con las credenciales de prueba
3. Verificar que redirija al dashboard

### **✅ Registro de Usuario:**
1. Ir a http://localhost:5003/register
2. Llenar el formulario de registro
3. Verificar que se registre correctamente

### **✅ Dashboard en Tiempo Real:**
1. Ver métricas actuales (Frecuencia cardíaca, Presión arterial, etc.)
2. Observar gráficos interactivos
3. Verificar actualización automática cada 30 segundos

### **✅ Endpoints de API:**
```bash
# Verificar salud de microservicios
curl http://localhost:5000/health  # AltaDeDatos
curl http://localhost:5001/health  # CalculoMetricas
curl http://localhost:5002/health  # Dashboards
curl http://localhost:5003/health  # InicioSesion

# Obtener datos actuales
curl http://localhost:5002/api/current-vitals/20250831-5f21-4f32-8e12-28e441467a18

# Obtener datos históricos (XML)
curl http://localhost:5002/api/vitals-gps/20250831-5f21-4f32-8e12-28e441467a18
curl http://localhost:5002/api/kpis-risk/20250831-5f21-4f32-8e12-28e441467a18
```

## **Paso 5: Verificar Flujo de Datos**

### **📊 Flujo Completo:**
1. **Simulador de Reloj** → Envía datos cada 30 segundos
2. **AltaDeDatos** → Recibe y almacena en Redis + InfluxDB
3. **CalculoMetricas** → Procesa métricas diarias automáticamente
4. **Dashboards** → Sirve datos al frontend
5. **Frontend** → Muestra dashboard interactivo

### **🔍 Verificar en Redis:**
```bash
# Conectar a Redis
docker exec -it my-redis redis-cli

# Ver claves
KEYS *

# Ver datos de un paciente
HGETALL patient_vitals:20250831-5f21-4f32-8e12-28e441467a18
```

### **🔍 Verificar en InfluxDB:**
- Ir a http://localhost:8086
- Usuario: `admin`
- Contraseña: `my_password`
- Verificar buckets: `my_app_raw_data` y `my_app_processed_data`

## **Paso 6: Detener el Sistema**

### **Opción A: Usar script automático**
```bash
# Doble clic en:
detener_sistema.bat
```

### **Opción B: Detener manualmente**
- Cerrar todas las ventanas de terminal
- O usar Ctrl+C en cada terminal

## **🚨 Solución de Problemas**

### **Error de Conexión a Base de Datos:**
```bash
# Verificar que Docker esté corriendo
docker ps

# Reiniciar contenedores si es necesario
docker-compose restart
```

### **Error de Puerto en Uso:**
```bash
# Verificar puertos ocupados
netstat -ano | findstr :5000
netstat -ano | findstr :5001
netstat -ano | findstr :5002
netstat -ano | findstr :5003

# Matar proceso si es necesario
taskkill /f /pid [PID]
```

### **Error de Dependencias:**
```bash
# Reinstalar dependencias
cd microservicios\[nombre_microservicio]
pip install -r requirements.txt
```

## **📱 Características del Dashboard**

- ✅ **Métricas en Tiempo Real**: Frecuencia cardíaca, presión arterial, distancia, riesgo
- ✅ **Gráficos Interactivos**: Highcharts con datos históricos
- ✅ **Indicadores de Estado**: Normal, Advertencia, Peligro
- ✅ **Actualización Automática**: Cada 30 segundos
- ✅ **Diseño Responsive**: Funciona en móviles y desktop
- ✅ **Autenticación Segura**: Login/registro con PostgreSQL

## **🎯 Resultados Esperados**

1. **Sistema funcionando** con 4 microservicios + simulador
2. **Dashboard interactivo** mostrando datos en tiempo real
3. **Autenticación** funcionando correctamente
4. **Datos fluyendo** desde el simulador hasta el frontend
5. **Gráficos actualizándose** automáticamente
6. **Métricas calculándose** y mostrándose correctamente

¡El sistema está listo para usar! 🎉
