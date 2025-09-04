from flask import Flask, request, jsonify
import datetime
import math
import random
import threading
import time
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
import logging
import os

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuración de InfluxDB
INFLUX_BUCKET_RAW = "my_app_raw_data"
INFLUX_BUCKET_PROCESSED = "my_app_processed_data"
INFLUX_ORG = "my-org"
INFLUX_TOKEN = "PpCwdSIMJdtVNgnnghBtDll0Q7KKRWzOm-LrSyCAOEo5jaVix2-NP0VPNkCoM_ztd4ZzsZzuyPi5Iuk9CD0ZCg=="
INFLUX_URL = os.getenv("INFLUX_URL", "http://localhost:8086")

# Paciente por defecto
DEFAULT_PATIENT_ID = "20250831-5f21-4f32-8e12-28e441467a18"

class MetricsCalculator:
    def __init__(self):
        """Inicializar el calculador de métricas"""
        self.influx_client = None
        self.query_api = None
        self.write_api = None
        self.setup_connections()
        self.start_daily_processing_thread()
    
    def setup_connections(self):
        """Configurar conexiones a InfluxDB"""
        try:
            self.influx_client = InfluxDBClient(
                url=INFLUX_URL,
                token=INFLUX_TOKEN,
                org=INFLUX_ORG
            )
            self.query_api = self.influx_client.query_api()
            self.write_api = self.influx_client.write_api(
                write_options=SYNCHRONOUS
            )
            logger.info("✅ Conectado a InfluxDB")
        except Exception as e:
            logger.error(f"❌ Error configurando conexiones: {e}")
            raise
    
    def haversine_distance(self, lat1, lon1, lat2, lon2):
        """Calcular distancia entre dos puntos GPS usando fórmula de Haversine"""
        R = 6371000  # Radio de la Tierra en metros
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)
        
        a = math.sin(delta_phi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c
    
    def calculate_daily_metrics(self, patient_id, target_date=None):
        """Calcular métricas diarias para un paciente específico"""
        try:
            # Si no se especifica fecha, usar ayer
            if target_date is None:
                target_date = datetime.datetime.utcnow() - datetime.timedelta(days=1)
            
            # Calcular el rango de fechas para el día específico
            end_date = target_date
            start_date = end_date - datetime.timedelta(days=1)
            
            logger.info(f"📊 Calculando métricas para {patient_id} - {start_date.strftime('%Y-%m-%d')} a {end_date.strftime('%Y-%m-%d')}")
            
            # Query para vitales del día específico
            vitals_query = f'''
            from(bucket: "{INFLUX_BUCKET_RAW}")
              |> range(start: {start_date.strftime('%Y-%m-%dT%H:%M:%SZ')}, stop: {end_date.strftime('%Y-%m-%dT%H:%M:%SZ')})
              |> filter(fn: (r) => r["_measurement"] == "vitals")
              |> filter(fn: (r) => r["patient_id"] == "{patient_id}")
              |> sort(columns: ["_time"])
            '''

            # Query para GPS del día específico
            gps_query = f'''
            from(bucket: "{INFLUX_BUCKET_RAW}")
              |> range(start: {start_date.strftime('%Y-%m-%dT%H:%M:%SZ')}, stop: {end_date.strftime('%Y-%m-%dT%H:%M:%SZ')})
              |> filter(fn: (r) => r["_measurement"] == "gps")
              |> filter(fn: (r) => r["patient_id"] == "{patient_id}")
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
                vitals_tables = self.query_api.query(query=vitals_query)
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
                logger.error(f"❌ Error procesando vitales: {e}")
                heart_rates = []
            
            # Procesar datos GPS
            try:
                gps_tables = self.query_api.query(query=gps_query)
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
                logger.error(f"❌ Error procesando GPS: {e}")
                gps_points = []
            
            # Calcular distancia total
            for i in range(1, len(gps_points)):
                lat1, lon1 = gps_points[i-1]
                lat2, lon2 = gps_points[i]
                distance = self.haversine_distance(lat1, lon1, lat2, lon2)
                total_distance += distance
            
            # Calcular métricas de actividad
            movement_threshold = 10  # metros
            active_periods = 0
            sedentary_periods = 0
            
            for i in range(1, len(gps_points)):
                lat1, lon1 = gps_points[i-1]
                lat2, lon2 = gps_points[i]
                distance = self.haversine_distance(lat1, lon1, lat2, lon2)
                
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
                    .tag("patient_id", patient_id) \
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
                    .tag("patient_id", patient_id) \
                    .tag("model_name", "daily_risk_model") \
                    .tag("model_version", "1.0") \
                    .field("risk_score", round(risk_score, 3)) \
                    .field("risk_label", risk_label) \
                    .time(day_timestamp, WritePrecision.S)
                
                return [kpi_point, risk_point], {
                    'avg_hr': round(avg_hr, 2),
                    'distance': round(total_distance, 2),
                    'high_hr_pct': round(high_hr_percentage, 2),
                    'alerts': high_heart_rate_count,
                    'risk_score': round(risk_score, 3),
                    'risk_label': risk_label,
                    'time_active': round(time_active, 2),
                    'time_sedentary': round(time_sedentary, 2)
                }
            else:
                logger.warning(f"⚠️ No se encontraron datos vitales para {patient_id} en {start_date.strftime('%Y-%m-%d')}")
                return [], None
                
        except Exception as e:
            logger.error(f"❌ Error calculando métricas para {patient_id}: {e}")
            return [], None
    
    def store_metrics_in_influxdb(self, points):
        """Almacenar métricas calculadas en InfluxDB"""
        try:
            if points:
                self.write_api.write(
                    bucket=INFLUX_BUCKET_PROCESSED,
                    org=INFLUX_ORG,
                    record=points
                )
                logger.info(f"📈 {len(points)} métricas almacenadas en InfluxDB")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Error almacenando métricas en InfluxDB: {e}")
            return False
    
    def process_daily_metrics(self, patient_id=None):
        """Procesar métricas diarias para un paciente"""
        if patient_id is None:
            patient_id = DEFAULT_PATIENT_ID
        
        try:
            points, summary = self.calculate_daily_metrics(patient_id)
            if points:
                success = self.store_metrics_in_influxdb(points)
                if success:
                    logger.info(f"✅ Métricas procesadas para {patient_id}: {summary}")
                    return True, summary
                else:
                    logger.error(f"❌ Error almacenando métricas para {patient_id}")
                    return False, None
            else:
                logger.warning(f"⚠️ No hay datos para procesar para {patient_id}")
                return False, None
        except Exception as e:
            logger.error(f"❌ Error procesando métricas diarias: {e}")
            return False, None
    
    def start_daily_processing_thread(self):
        """Iniciar hilo para procesamiento diario automático"""
        def daily_worker():
            while True:
                try:
                    # Esperar hasta las 2:00 AM para procesar el día anterior
                    now = datetime.datetime.now()
                    next_run = now.replace(hour=2, minute=0, second=0, microsecond=0)
                    if next_run <= now:
                        next_run += datetime.timedelta(days=1)
                    
                    sleep_seconds = (next_run - now).total_seconds()
                    logger.info(f"🕐 Próximo procesamiento diario en {sleep_seconds/3600:.1f} horas")
                    time.sleep(sleep_seconds)
                    
                    logger.info("🔄 Iniciando procesamiento diario automático")
                    self.process_daily_metrics()
                    
                except Exception as e:
                    logger.error(f"❌ Error en hilo de procesamiento diario: {e}")
                    time.sleep(3600)  # Esperar 1 hora antes de reintentar
        
        daily_thread = threading.Thread(target=daily_worker, daemon=True)
        daily_thread.start()
        logger.info("🔄 Hilo de procesamiento diario iniciado")

# Instancia global del calculador de métricas
metrics_calculator = MetricsCalculator()

@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint de salud del microservicio"""
    return jsonify({
        "status": "healthy",
        "service": "CalculoMetricas",
        "timestamp": datetime.datetime.now().isoformat()
    })

@app.route('/metrics/calculate', methods=['POST'])
def calculate_metrics():
    """Endpoint para calcular métricas de un paciente específico"""
    try:
        data = request.get_json() or {}
        patient_id = data.get('patient_id', DEFAULT_PATIENT_ID)
        target_date_str = data.get('target_date')
        
        target_date = None
        if target_date_str:
            try:
                target_date = datetime.datetime.fromisoformat(target_date_str.replace('Z', '+00:00'))
            except ValueError:
                return jsonify({
                    "error": "Formato de fecha inválido. Use ISO format (YYYY-MM-DDTHH:MM:SSZ)",
                    "status": "error"
                }), 400
        
        success, summary = metrics_calculator.process_daily_metrics(patient_id)
        
        if success:
            return jsonify({
                "message": "Métricas calculadas exitosamente",
                "patient_id": patient_id,
                "summary": summary,
                "status": "success"
            }), 200
        else:
            return jsonify({
                "error": "No se pudieron calcular las métricas",
                "patient_id": patient_id,
                "status": "error"
            }), 500
            
    except Exception as e:
        logger.error(f"❌ Error en endpoint /metrics/calculate: {e}")
        return jsonify({
            "error": "Error interno del servidor",
            "status": "error"
        }), 500

@app.route('/metrics/calculate/<patient_id>', methods=['POST'])
def calculate_metrics_for_patient(patient_id):
    """Endpoint para calcular métricas de un paciente específico"""
    try:
        data = request.get_json() or {}
        target_date_str = data.get('target_date')
        
        target_date = None
        if target_date_str:
            try:
                target_date = datetime.datetime.fromisoformat(target_date_str.replace('Z', '+00:00'))
            except ValueError:
                return jsonify({
                    "error": "Formato de fecha inválido. Use ISO format (YYYY-MM-DDTHH:MM:SSZ)",
                    "status": "error"
                }), 400
        
        success, summary = metrics_calculator.process_daily_metrics(patient_id)
        
        if success:
            return jsonify({
                "message": "Métricas calculadas exitosamente",
                "patient_id": patient_id,
                "summary": summary,
                "status": "success"
            }), 200
        else:
            return jsonify({
                "error": "No se pudieron calcular las métricas",
                "patient_id": patient_id,
                "status": "error"
            }), 500
            
    except Exception as e:
        logger.error(f"❌ Error calculando métricas para {patient_id}: {e}")
        return jsonify({
            "error": "Error interno del servidor",
            "status": "error"
        }), 500

@app.route('/metrics/batch', methods=['POST'])
def calculate_batch_metrics():
    """Endpoint para calcular métricas para múltiples días"""
    try:
        data = request.get_json() or {}
        patient_id = data.get('patient_id', DEFAULT_PATIENT_ID)
        days = data.get('days', 7)  # Por defecto, últimos 7 días
        
        results = []
        for day_offset in range(days):
            target_date = datetime.datetime.utcnow() - datetime.timedelta(days=day_offset+1)
            points, summary = metrics_calculator.calculate_daily_metrics(patient_id, target_date)
            
            if points:
                success = metrics_calculator.store_metrics_in_influxdb(points)
                if success:
                    results.append({
                        "date": target_date.strftime('%Y-%m-%d'),
                        "success": True,
                        "summary": summary
                    })
                else:
                    results.append({
                        "date": target_date.strftime('%Y-%m-%d'),
                        "success": False,
                        "error": "Error almacenando en InfluxDB"
                    })
            else:
                results.append({
                    "date": target_date.strftime('%Y-%m-%d'),
                    "success": False,
                    "error": "No hay datos disponibles"
                })
        
        return jsonify({
            "message": f"Procesamiento por lotes completado para {days} días",
            "patient_id": patient_id,
            "results": results,
            "status": "success"
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error en procesamiento por lotes: {e}")
        return jsonify({
            "error": "Error interno del servidor",
            "status": "error"
        }), 500

if __name__ == '__main__':
    logger.info("🚀 Iniciando microservicio CalculoMetricas...")
    logger.info("📡 Endpoints disponibles:")
    logger.info("  POST /metrics/calculate - Calcular métricas del día anterior")
    logger.info("  POST /metrics/calculate/<patient_id> - Calcular métricas para paciente específico")
    logger.info("  POST /metrics/batch - Calcular métricas para múltiples días")
    logger.info("  GET /health - Estado del servicio")
    logger.info("🔄 Procesamiento automático diario a las 2:00 AM")
    
    app.run(host='0.0.0.0', port=5001, debug=True)
