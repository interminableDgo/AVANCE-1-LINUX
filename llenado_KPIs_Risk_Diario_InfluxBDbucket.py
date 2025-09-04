import datetime
import math
import random
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

# InfluxDB Configuration
bucket_raw = "my_app_raw_data"
bucket_processed = "my_app_processed_data"
org = "my-org"
token = "PpCwdSIMJdtVNgnnghBtDll0Q7KKRWzOm-LrSyCAOEo5jaVix2-NP0VPNkCoM_ztd4ZzsZzuyPi5Iuk9CD0ZCg=="
url = "http://localhost:8086"

client = InfluxDBClient(url=url, token=token, org=org)
query_api = client.query_api()
write_api = client.write_api(write_options=SYNCHRONOUS)

# Patient UUID
patient_uuid = "20250831-5f21-4f32-8e12-28e441467a18"

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calcular distancia entre dos puntos GPS usando fórmula de Haversine"""
    R = 6371000  # Radio de la Tierra en metros
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = math.sin(delta_phi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def process_daily_data(day_offset):
    """Procesar datos de un día específico"""
    # Calcular el rango de fechas para el día específico
    end_date = datetime.datetime.utcnow() - datetime.timedelta(days=day_offset)
    start_date = end_date - datetime.timedelta(days=1)
    
    print(f"Procesando día {7-day_offset}: {start_date.strftime('%Y-%m-%d')} a {end_date.strftime('%Y-%m-%d')}")
    
    # Query para vitales del día específico
    vitals_query = f'''
from(bucket: "{bucket_raw}")
  |> range(start: {start_date.strftime('%Y-%m-%dT%H:%M:%SZ')}, stop: {end_date.strftime('%Y-%m-%dT%H:%M:%SZ')})
  |> filter(fn: (r) => r["_measurement"] == "vitals")
  |> filter(fn: (r) => r["patient_id"] == "{patient_uuid}")
  |> sort(columns: ["_time"])
'''

    # Query para GPS del día específico
    gps_query = f'''
from(bucket: "{bucket_raw}")
  |> range(start: {start_date.strftime('%Y-%m-%dT%H:%M:%SZ')}, stop: {end_date.strftime('%Y-%m-%dT%H:%M:%SZ')})
  |> filter(fn: (r) => r["_measurement"] == "gps")
  |> filter(fn: (r) => r["patient_id"] == "{patient_uuid}")
  |> sort(columns: ["_time"])
'''
    
    # Variables para cálculos
    heart_rates = []
    high_heart_rate_count = 0
    systolic_bps = []
    diastolic_bps = []
    
    gps_points = []
    total_distance = 0
    
    # Procesar datos vitales
    try:
        vitals_tables = query_api.query(query=vitals_query)
        for table in vitals_tables:
            for record in table.records:
                field = record.get_field()
                value = record.get_value()
                
                if field == "heart_rate" and value is not None:
                    heart_rates.append(value)
                    if value > 100:
                        high_heart_rate_count += 1
                elif field == "systolic_bp" and value is not None:
                    systolic_bps.append(value)
                elif field == "diastolic_bp" and value is not None:
                    diastolic_bps.append(value)
    except Exception as e:
        print(f"Error procesando vitales: {e}")
        heart_rates = []
    
    # Procesar datos GPS
    try:
        gps_tables = query_api.query(query=gps_query)
        temp_gps_data = {}  # Temporal para agrupar por timestamp
        
        for table in gps_tables:
            for record in table.records:
                timestamp = record.get_time()
                field = record.get_field()
                value = record.get_value()
                
                if timestamp not in temp_gps_data:
                    temp_gps_data[timestamp] = {}
                temp_gps_data[timestamp][field] = value
        
        # Convertir a lista ordenada con coordenadas completas
        for timestamp in sorted(temp_gps_data.keys()):
            data = temp_gps_data[timestamp]
            if 'lat' in data and 'lon' in data and data['lat'] is not None and data['lon'] is not None:
                gps_points.append((data['lat'], data['lon']))
        
    except Exception as e:
        print(f"Error procesando GPS: {e}")
        gps_points = []
    
    # Calcular distancia total
    for i in range(1, len(gps_points)):
        lat1, lon1 = gps_points[i-1]
        lat2, lon2 = gps_points[i]
        distance = haversine_distance(lat1, lon1, lat2, lon2)
        total_distance += distance
    
    # Calcular métricas de actividad
    movement_threshold = 10  # metros
    active_periods = 0
    sedentary_periods = 0
    
    for i in range(1, len(gps_points)):
        lat1, lon1 = gps_points[i-1]
        lat2, lon2 = gps_points[i]
        distance = haversine_distance(lat1, lon1, lat2, lon2)
        
        if distance > movement_threshold:
            active_periods += 1
        else:
            sedentary_periods += 1
    
    # Calcular KPIs si hay datos
    if len(heart_rates) > 0:
        avg_hr = sum(heart_rates) / len(heart_rates)
        high_hr_percentage = (high_heart_rate_count / len(heart_rates)) * 100
        
        # Presión arterial promedio
        avg_sbp = sum(systolic_bps) / len(systolic_bps) if systolic_bps else 120
        avg_dbp = sum(diastolic_bps) / len(diastolic_bps) if diastolic_bps else 80
        avg_ap = (avg_sbp + 2 * avg_dbp) / 3  # Fórmula correcta para presión arterial media
        
        # Tiempo activo/sedentario en minutos (cada punto = 30 segundos)
        time_active = active_periods * 0.5  # minutos
        time_sedentary = sedentary_periods * 0.5  # minutos
        
        # Generar score de riesgo basado en las métricas
        risk_factors = 0
        if avg_hr > 100:
            risk_factors += 1
        if high_hr_percentage > 10:
            risk_factors += 1
        if avg_sbp > 130:
            risk_factors += 1
        if time_sedentary > (12 * 60):  # Más de 12 horas sedentario
            risk_factors += 1
        
        risk_score = min(0.2 + (risk_factors * 0.2), 1.0)
        risk_label = "low" if risk_score < 0.3 else "medium" if risk_score < 0.7 else "high"
        
        # Timestamp para el día (medianoche del día procesado)
        day_timestamp = start_date.replace(hour=23, minute=59, second=59)
        
        # Crear punto KPI
        kpi_point = Point("KPI_daily") \
            .tag("patient_id", patient_uuid) \
            .field("average_heart_rate", round(avg_hr, 2)) \
            .field("total_distance_traveled", round(total_distance, 2)) \
            .field("high_heart_rate_percentage", round(high_hr_percentage, 2)) \
            .field("average_arterial_pressure", round(avg_ap, 2)) \
            .field("daily_alert_count", high_heart_rate_count) \
            .field("time_sedentary", round(time_sedentary, 2)) \
            .field("time_active", round(time_active, 2)) \
            .time(day_timestamp, WritePrecision.S)

        # Crear punto de riesgo
        risk_point = Point("Risk_inference") \
            .tag("patient_id", patient_uuid) \
            .tag("model_name", "daily_risk_model") \
            .tag("model_version", "1.0") \
            .tag("risk_label", risk_label) \
            .field("risk_score", round(risk_score, 3)) \
            .field("risk_level", 1 if risk_label == "high" else 2 if risk_label == "medium" else 3) \
            .time(day_timestamp, WritePrecision.S)
        
        return [kpi_point, risk_point], {
            'avg_hr': round(avg_hr, 2),
            'distance': round(total_distance, 2),
            'high_hr_pct': round(high_hr_percentage, 2),
            'alerts': high_heart_rate_count,
            'risk_score': round(risk_score, 3),
            'risk_label': risk_label
        }
    else:
        print(f"No se encontraron datos vitales para el día {7-day_offset}")
        return [], None

# Procesar cada día de la semana
print("Iniciando procesamiento de KPIs diarios...")
all_points = []
daily_summaries = []

for day in range(7):  # Día 0 = hoy-7, Día 6 = hoy-1
    points, summary = process_daily_data(6-day)  # Invertir orden para procesar del más antiguo al más reciente
    if points:
        all_points.extend(points)
        daily_summaries.append(f"Día {day+1}: HR={summary['avg_hr']}, Dist={summary['distance']}m, Riesgo={summary['risk_label']}")
    else:
        daily_summaries.append(f"Día {day+1}: Sin datos")

# Escribir todos los puntos
if all_points:
    print(f"Escribiendo {len(all_points)} registros procesados...")
    write_api.write(bucket=bucket_processed, org=org, record=all_points)
    print("✅ KPIs y datos de riesgo diarios insertados exitosamente.")
    
    print("\n📊 Resumen semanal:")
    for summary in daily_summaries:
        print(f"  {summary}")
else:
    print("❌ No se encontraron datos para procesar.")

# Cerrar conexión
client.close()