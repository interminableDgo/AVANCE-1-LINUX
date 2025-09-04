# Microservicio AltaDeDatos

Este microservicio se encarga de recibir datos vitales de relojes inteligentes y gestionar su almacenamiento en Redis e InfluxDB.

## Funcionalidades

- **Recibir datos**: Endpoint REST para recibir datos vitales del reloj inteligente
- **Almacenar en Redis**: Los datos se almacenan temporalmente en Redis
- **Sincronizar con InfluxDB**: Los datos se sincronizan automáticamente a InfluxDB cada minuto
- **Generar GPS**: Genera datos GPS realistas basados en la ubicación del paciente

## Endpoints

### POST /vitals
Recibe datos vitales del reloj inteligente.

**Request Body:**
```json
{
    "patient_id": "20250831-5f21-4f32-8e12-28e441467a18",
    "heart_rate": 75,
    "systolic_blood_pressure": 120,
    "diastolic_blood_pressure": 80,
    "timestamp": "2025-01-09T23:21:00"
}
```

### GET /vitals/{patient_id}
Obtiene los datos vitales actuales de un paciente desde Redis.

### POST /sync
Ejecuta una sincronización manual de Redis a InfluxDB.

### GET /health
Verifica el estado del microservicio.

## Instalación y Uso

1. **Instalar dependencias:**
   ```bash
   cd microservicios/AltaDeDatos
   pip install -r requirements.txt
   ```

2. **Asegurar que los servicios estén corriendo:**
   ```bash
   # Redis
   docker-compose up -d redis
   
   # InfluxDB
   docker-compose up -d influxdb
   ```

3. **Ejecutar el microservicio:**
   ```bash
   python app.py
   ```

4. **Ejecutar el simulador de reloj:**
   ```bash
   python SimulacionSmartWatch_Microservicio.py
   ```

## Arquitectura

```
Reloj Inteligente → Microservicio AltaDeDatos → Redis
                                      ↓
                                 InfluxDB
```

- Los datos llegan al microservicio cada 30 segundos
- Se almacenan inmediatamente en Redis
- Se sincronizan automáticamente a InfluxDB cada minuto
- Se generan datos GPS realistas para cada medición
