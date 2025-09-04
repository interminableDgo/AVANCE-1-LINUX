# Microservicio CalculoMetricas

Este microservicio se encarga de calcular métricas diarias basadas en los datos de GPS y Vitals almacenados en InfluxDB, generando KPIs y análisis de riesgo.

## Funcionalidades

- **Cálculo de métricas diarias**: Procesa datos de GPS y Vitals de InfluxDB
- **Generación de KPIs**: Calcula métricas como frecuencia cardíaca promedio, distancia recorrida, etc.
- **Análisis de riesgo**: Genera scores de riesgo basados en las métricas
- **Procesamiento automático**: Ejecuta cálculos diarios automáticamente a las 2:00 AM
- **Procesamiento por lotes**: Permite calcular métricas para múltiples días

## Métricas Calculadas

### KPIs Diarios
- `average_heart_rate`: Frecuencia cardíaca promedio
- `total_distance_traveled`: Distancia total recorrida (metros)
- `high_heart_rate_percentage`: Porcentaje de tiempo con frecuencia cardíaca alta (>100 bpm)
- `average_arterial_pressure`: Presión arterial promedio
- `daily_alert_count`: Número de alertas por frecuencia cardíaca alta
- `time_sedentary`: Tiempo sedentario (minutos)
- `time_active`: Tiempo activo (minutos)

### Risk Inference
- `risk_score`: Score de riesgo (0-1)
- `risk_label`: Etiqueta de riesgo (low/medium/high)
- `model_name`: Nombre del modelo de riesgo
- `model_version`: Versión del modelo

## Endpoints

### POST /metrics/calculate
Calcula métricas del día anterior para el paciente por defecto.

**Request Body (opcional):**
```json
{
    "patient_id": "20250831-5f21-4f32-8e12-28e441467a18",
    "target_date": "2025-01-08T00:00:00Z"
}
```

### POST /metrics/calculate/{patient_id}
Calcula métricas para un paciente específico.

**Request Body (opcional):**
```json
{
    "target_date": "2025-01-08T00:00:00Z"
}
```

### POST /metrics/batch
Calcula métricas para múltiples días.

**Request Body:**
```json
{
    "patient_id": "20250831-5f21-4f32-8e12-28e441467a18",
    "days": 7
}
```

### GET /health
Verifica el estado del microservicio.

## Instalación y Uso

1. **Instalar dependencias:**
   ```bash
   cd microservicios/CalculoMetricas
   pip install -r requirements.txt
   ```

2. **Asegurar que InfluxDB esté corriendo:**
   ```bash
   docker-compose up -d influxdb
   ```

3. **Ejecutar el microservicio:**
   ```bash
   python app.py
   ```

4. **Probar el microservicio:**
   ```bash
   # Calcular métricas del día anterior
   curl -X POST http://localhost:5001/metrics/calculate
   
   # Calcular métricas para múltiples días
   curl -X POST http://localhost:5001/metrics/batch \
        -H "Content-Type: application/json" \
        -d '{"days": 7}'
   ```

## Arquitectura

```
InfluxDB (raw_data) → CalculoMetricas → InfluxDB (processed_data)
```

- Lee datos de GPS y Vitals desde `my_app_raw_data`
- Calcula métricas y KPIs
- Genera análisis de riesgo
- Almacena resultados en `my_app_processed_data`

## Procesamiento Automático

El microservicio ejecuta automáticamente el cálculo de métricas diarias a las 2:00 AM para procesar los datos del día anterior.

## Algoritmo de Riesgo

El score de riesgo se calcula basado en:
- Frecuencia cardíaca promedio > 100 bpm
- Porcentaje de tiempo con frecuencia cardíaca alta > 10%
- Presión arterial sistólica > 130 mmHg
- Tiempo sedentario > 12 horas

Cada factor contribuye 0.2 al score base de 0.2, con un máximo de 1.0.
