from flask import Flask, request, jsonify
import redis
import time
import datetime
import random
import threading
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
import json
import logging
import os

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuración de Redis
REDIS_HOST = os.getenv("REDIS_HOST", "my-redis")
REDIS_PORT = 6379
REDIS_DB = 0

# Configuración de InfluxDB
INFLUX_BUCKET = "my_app_raw_data"
INFLUX_ORG = "my-org"
INFLUX_TOKEN = "PpCwdSIMJdtVNgnnghBtDll0Q7KKRWzOm-LrSyCAOEo5jaVix2-NP0VPNkCoM_ztd4ZzsZzuyPi5Iuk9CD0ZCg=="
INFLUX_URL = os.getenv("INFLUX_URL", "http://my-influxdb:8086")

class DataManager:
    def __init__(self):
        """Inicializar el gestor de datos"""
        self.redis_client = None
        self.influx_client = None
        self.influx_write_api = None
        self.setup_connections()
        self.start_influx_sync_thread()
    
    def setup_connections(self):
        """Configurar conexiones a Redis e InfluxDB"""
        try:
            # Configurar Redis
            self.redis_client = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                db=REDIS_DB,
                decode_responses=True
            )
            self.redis_client.ping()
            logger.info("✅ Conectado a Redis")
            
            # Configurar InfluxDB
            self.influx_client = InfluxDBClient(
                url=INFLUX_URL,
                token=INFLUX_TOKEN,
                org=INFLUX_ORG
            )
            self.influx_write_api = self.influx_client.write_api(
                write_options=SYNCHRONOUS
            )
            logger.info("✅ Conectado a InfluxDB")
            
        except Exception as e:
            logger.error(f"❌ Error configurando conexiones: {e}")
            raise
    
    def store_vitals_in_redis(self, vitals_data):
        """Almacenar datos vitales en Redis"""
        try:
            patient_id = vitals_data.get("patient_id")
            if not patient_id:
                raise ValueError("patient_id es requerido")
            
            key = f"patient_vitals:{patient_id}"
            
            # Almacenar como hash en Redis
            self.redis_client.hset(key, mapping={
                "patient_id": vitals_data["patient_id"],
                "heart_rate": vitals_data["heart_rate"],
                "systolic_blood_pressure": vitals_data["systolic_blood_pressure"],
                "diastolic_blood_pressure": vitals_data["diastolic_blood_pressure"],
                "timestamp": vitals_data["timestamp"],
                "last_updated": datetime.datetime.now().isoformat()
            })
            
            # Establecer TTL de 1 hora
            self.redis_client.expire(key, 3600)
            
            logger.info(f"📊 Datos almacenados en Redis para paciente {patient_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error almacenando en Redis: {e}")
            return False
    
    def get_vitals_from_redis(self, patient_id):
        """Obtener datos vitales desde Redis"""
        try:
            key = f"patient_vitals:{patient_id}"
            vitals = self.redis_client.hgetall(key)
            return vitals if vitals else None
        except Exception as e:
            logger.error(f"❌ Error obteniendo datos de Redis: {e}")
            return None
    
    def generate_gps_data(self, patient_id, timestamp):
        """Generar datos GPS realistas (basado en el script original)"""
        # Coordenadas base (Ciudad de México)
        base_lat = 19.432608
        base_lon = -99.133209
        
        # Determinar hora del día para simular patrones más realistas
        hour_of_day = timestamp.hour
        
        # GPS: simular movimiento más realista
        if 6 <= hour_of_day <= 22:  # Día activo
            lat_offset = random.uniform(-0.01, 0.01)  # ~1km de variación
            lon_offset = random.uniform(-0.01, 0.01)
        else:  # Noche, menos movimiento
            lat_offset = random.uniform(-0.001, 0.001)  # ~100m de variación
            lon_offset = random.uniform(-0.001, 0.001)
        
        lat = base_lat + lat_offset
        lon = base_lon + lon_offset
        
        return {
            "lat": lat,
            "lon": lon
        }
    
    def store_in_influxdb(self, vitals_data):
        """Almacenar datos en InfluxDB (vitals + GPS)"""
        try:
            patient_id = vitals_data["patient_id"]
            timestamp = datetime.datetime.fromisoformat(vitals_data["timestamp"])
            
            # Crear punto de datos para vitals
            vitals_point = Point("vitals") \
                .tag("patient_id", patient_id) \
                .field("heart_rate", int(vitals_data["heart_rate"])) \
                .field("systolic_bp", int(vitals_data["systolic_blood_pressure"])) \
                .field("diastolic_bp", int(vitals_data["diastolic_blood_pressure"])) \
                .time(timestamp, WritePrecision.S)
            
            # Generar datos GPS
            gps_data = self.generate_gps_data(patient_id, timestamp)
            
            # Crear punto de datos para GPS
            gps_point = Point("gps") \
                .tag("patient_id", patient_id) \
                .field("lat", gps_data["lat"]) \
                .field("lon", gps_data["lon"]) \
                .time(timestamp, WritePrecision.S)
            
            # Escribir en InfluxDB
            self.influx_write_api.write(
                bucket=INFLUX_BUCKET,
                org=INFLUX_ORG,
                record=[vitals_point, gps_point]
            )
            
            logger.info(f"📈 Datos almacenados en InfluxDB para paciente {patient_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error almacenando en InfluxDB: {e}")
            return False
    
    def sync_redis_to_influxdb(self):
        """Sincronizar datos de Redis a InfluxDB"""
        try:
            # Buscar todas las claves de pacientes en Redis
            pattern = "patient_vitals:*"
            keys = self.redis_client.keys(pattern)
            
            for key in keys:
                vitals_data = self.redis_client.hgetall(key)
                if vitals_data:
                    # Almacenar en InfluxDB
                    success = self.store_in_influxdb(vitals_data)
                    if success:
                        logger.info(f"✅ Sincronizado: {key}")
                    else:
                        logger.error(f"❌ Error sincronizando: {key}")
            
        except Exception as e:
            logger.error(f"❌ Error en sincronización: {e}")
    
    def start_influx_sync_thread(self):
        """Iniciar hilo para sincronización periódica con InfluxDB"""
        def sync_worker():
            while True:
                try:
                    time.sleep(60)  # Sincronizar cada minuto
                    logger.info("🔄 Iniciando sincronización Redis → InfluxDB")
                    self.sync_redis_to_influxdb()
                except Exception as e:
                    logger.error(f"❌ Error en hilo de sincronización: {e}")
        
        sync_thread = threading.Thread(target=sync_worker, daemon=True)
        sync_thread.start()
        logger.info("🔄 Hilo de sincronización iniciado")

# Instancia global del gestor de datos
data_manager = DataManager()

@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint de salud del microservicio"""
    return jsonify({
        "status": "healthy",
        "service": "AltaDeDatos",
        "timestamp": datetime.datetime.now().isoformat()
    })

@app.route('/vitals', methods=['POST'])
def receive_vitals():
    """Endpoint para recibir datos vitales del reloj inteligente"""
    try:
        data = request.get_json()
        
        # Validar datos requeridos
        required_fields = ['patient_id', 'heart_rate', 'systolic_blood_pressure', 'diastolic_blood_pressure']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "error": f"Campo requerido faltante: {field}",
                    "status": "error"
                }), 400
        
        # Agregar timestamp si no viene
        if 'timestamp' not in data:
            data['timestamp'] = datetime.datetime.now().isoformat()
        
        # Almacenar en Redis
        success = data_manager.store_vitals_in_redis(data)
        
        if success:
            return jsonify({
                "message": "Datos vitales almacenados correctamente",
                "patient_id": data['patient_id'],
                "status": "success"
            }), 200
        else:
            return jsonify({
                "error": "Error almacenando datos en Redis",
                "status": "error"
            }), 500
            
    except Exception as e:
        logger.error(f"❌ Error en endpoint /vitals: {e}")
        return jsonify({
            "error": "Error interno del servidor",
            "status": "error"
        }), 500

@app.route('/vitals/<patient_id>', methods=['GET'])
def get_vitals(patient_id):
    """Endpoint para obtener datos vitales de un paciente desde Redis"""
    try:
        vitals = data_manager.get_vitals_from_redis(patient_id)
        
        if vitals:
            return jsonify({
                "patient_id": patient_id,
                "data": vitals,
                "status": "success"
            }), 200
        else:
            return jsonify({
                "message": f"No se encontraron datos para el paciente {patient_id}",
                "status": "not_found"
            }), 404
            
    except Exception as e:
        logger.error(f"❌ Error obteniendo datos del paciente {patient_id}: {e}")
        return jsonify({
            "error": "Error interno del servidor",
            "status": "error"
        }), 500

@app.route('/sync', methods=['POST'])
def manual_sync():
    """Endpoint para sincronización manual de Redis a InfluxDB"""
    try:
        data_manager.sync_redis_to_influxdb()
        return jsonify({
            "message": "Sincronización manual completada",
            "status": "success"
        }), 200
    except Exception as e:
        logger.error(f"❌ Error en sincronización manual: {e}")
        return jsonify({
            "error": "Error en sincronización",
            "status": "error"
        }), 500

if __name__ == '__main__':
    logger.info("🚀 Iniciando microservicio AltaDeDatos...")
    logger.info("📡 Endpoints disponibles:")
    logger.info("  POST /vitals - Recibir datos del reloj")
    logger.info("  GET /vitals/<patient_id> - Obtener datos de un paciente")
    logger.info("  POST /sync - Sincronización manual")
    logger.info("  GET /health - Estado del servicio")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
