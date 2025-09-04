import time
import datetime
import random
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

# Configuración de InfluxDB
bucket = "my_app_raw_data"
org = "my-org"
token = "PpCwdSIMJdtVNgnnghBtDll0Q7KKRWzOm-LrSyCAOEo5jaVix2-NP0VPNkCoM_ztd4ZzsZzuyPi5Iuk9CD0ZCg=="
url = "http://localhost:8086"

client = InfluxDBClient(url=url, token=token, org=org)
write_api = client.write_api(write_options=SYNCHRONOUS)

# Datos de prueba del paciente
patient_uuid = "20250831-5f21-4f32-8e12-28e441467a18"

# Duración de la simulación: 1 semana completa con intervalos de 30 segundos
# 7 días * 24 horas * 60 minutos * 2 mediciones por minuto (cada 30s)
total_points = 7 * 24 * 60 * 2
print(f"Generando datos para 1 semana completa: {total_points} puntos de datos")

# Punto de inicio: hace 1 semana desde ahora
start_time = datetime.datetime.utcnow() - datetime.timedelta(days=7)

# Lista para almacenar todos los puntos de datos
points_list = []

# Coordenadas base (Ciudad de México)
base_lat = 19.432608
base_lon = -99.133209

print("Generando datos...")

for i in range(total_points):
    # Generar marca de tiempo: desde hace 1 semana hasta ahora, cada 30 segundos
    timestamp = start_time + datetime.timedelta(seconds=i * 30)
    
    # Determinar hora del día para simular patrones más realistas
    hour_of_day = timestamp.hour
    
    # Generar valores más realistas basados en la hora
    # Frecuencia cardíaca: más baja durante la noche
    if 22 <= hour_of_day or hour_of_day <= 6:  # Noche
        base_hr = 65
    elif 6 < hour_of_day < 12:  # Mañana
        base_hr = 75
    else:  # Tarde/noche
        base_hr = 80
    
    hr = base_hr + random.randint(-10, 15)
    hr = max(50, min(120, hr))  # Mantener en rango realista
    
    # Presión arterial
    sbp = random.randint(110, 140)
    dbp = random.randint(70, 90)
    
    # GPS: simular movimiento más realista
    # Más movimiento durante el día, menos durante la noche
    if 6 <= hour_of_day <= 22:  # Día activo
        lat_offset = random.uniform(-0.01, 0.01)  # ~1km de variación
        lon_offset = random.uniform(-0.01, 0.01)
    else:  # Noche, menos movimiento
        lat_offset = random.uniform(-0.001, 0.001)  # ~100m de variación
        lon_offset = random.uniform(-0.001, 0.001)
    
    lat = base_lat + lat_offset
    lon = base_lon + lon_offset
    
    # Crear los puntos de datos para InfluxDB
    vitals_point = Point("vitals") \
        .tag("patient_id", patient_uuid) \
        .field("heart_rate", hr) \
        .field("systolic_bp", sbp) \
        .field("diastolic_bp", dbp) \
        .time(timestamp, WritePrecision.S)

    gps_point = Point("gps") \
        .tag("patient_id", patient_uuid) \
        .field("lat", lat) \
        .field("lon", lon) \
        .time(timestamp, WritePrecision.S)

    # Agregar los puntos a la lista
    points_list.append(vitals_point)
    points_list.append(gps_point)
    
    # Mostrar progreso cada 1000 puntos
    if (i + 1) % 1000 == 0:
        print(f"Generados {i + 1}/{total_points} puntos...")

print("Datos generados. Escribiendo en InfluxDB...")

# Escribir en lotes para mejor rendimiento
batch_size = 5000
total_batches = len(points_list) // batch_size + (1 if len(points_list) % batch_size > 0 else 0)

for batch_num in range(total_batches):
    start_idx = batch_num * batch_size
    end_idx = min((batch_num + 1) * batch_size, len(points_list))
    batch_points = points_list[start_idx:end_idx]
    
    write_api.write(bucket=bucket, org=org, record=batch_points)
    print(f"Lote {batch_num + 1}/{total_batches} escrito en InfluxDB")

print(f"Simulación completada. {total_points * 2} registros enviados a InfluxDB.")
print(f"Datos desde: {start_time}")
print(f"Datos hasta: {start_time + datetime.timedelta(seconds=(total_points-1) * 30)}")

# Cerrar conexión
client.close()