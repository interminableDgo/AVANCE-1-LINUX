import time
import datetime
import random
import redis
import json
import signal
import sys

# Configuración de Redis
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 0

# Datos del paciente (mismo que en el script de InfluxDB)
PATIENT_ID = "20250831-5f21-4f32-8e12-28e441467a18"

# Configuración de la simulación
INTERVAL_SECONDS = 30  # Cada 30 segundos

class SmartWatchSimulator:
    def __init__(self):
        """Inicializar el simulador de reloj inteligente"""
        self.redis_client = None
        self.running = True
        self.setup_redis_connection()
        self.setup_signal_handlers()
    
    def setup_redis_connection(self):
        """Configurar conexión a Redis"""
        try:
            self.redis_client = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                db=REDIS_DB,
                decode_responses=True
            )
            # Probar la conexión
            self.redis_client.ping()
            print(f"✅ Conectado a Redis en {REDIS_HOST}:{REDIS_PORT}")
        except redis.ConnectionError as e:
            print(f"❌ Error conectando a Redis: {e}")
            print("Asegúrate de que Redis esté ejecutándose en Docker")
            sys.exit(1)
    
    def setup_signal_handlers(self):
        """Configurar manejadores de señales para cierre graceful"""
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Manejador para cierre graceful del programa"""
        print(f"\n🛑 Recibida señal {signum}. Cerrando simulador...")
        self.running = False
    
    def generate_realistic_vitals(self):
        """Generar datos vitales realistas basados en la hora del día"""
        current_time = datetime.datetime.now()
        hour_of_day = current_time.hour
        
        # Frecuencia cardíaca: más baja durante la noche
        if 22 <= hour_of_day or hour_of_day <= 6:  # Noche
            base_hr = 65
        elif 6 < hour_of_day < 12:  # Mañana
            base_hr = 75
        else:  # Tarde/noche
            base_hr = 80
        
        heart_rate = base_hr + random.randint(-10, 15)
        heart_rate = max(50, min(120, heart_rate))  # Mantener en rango realista
        
        # Presión arterial sistólica
        systolic_bp = random.randint(110, 140)
        
        # Presión arterial diastólica
        diastolic_bp = random.randint(70, 90)
        
        return {
            "patient_id": PATIENT_ID,
            "heart_rate": heart_rate,
            "systolic_blood_pressure": systolic_bp,
            "diastolic_blood_pressure": diastolic_bp,
            "timestamp": current_time.isoformat()
        }
    
    def store_vitals_in_redis(self, vitals_data):
        """Almacenar datos vitales en Redis"""
        try:
            # Usar el patient_id como clave principal
            key = f"patient_vitals:{PATIENT_ID}"
            
            # Almacenar como hash en Redis
            self.redis_client.hset(key, mapping={
                "patient_id": vitals_data["patient_id"],
                "heart_rate": vitals_data["heart_rate"],
                "systolic_blood_pressure": vitals_data["systolic_blood_pressure"],
                "diastolic_blood_pressure": vitals_data["diastolic_blood_pressure"],
                "timestamp": vitals_data["timestamp"],
                "last_updated": datetime.datetime.now().isoformat()
            })
            
            # Establecer TTL de 1 hora (opcional, para limpiar datos antiguos)
            self.redis_client.expire(key, 3600)
            
            print(f"📊 Datos almacenados en Redis - HR: {vitals_data['heart_rate']} bpm, "
                  f"SBP: {vitals_data['systolic_blood_pressure']}, "
                  f"DBP: {vitals_data['diastolic_blood_pressure']}")
            
        except redis.RedisError as e:
            print(f"❌ Error almacenando en Redis: {e}")
    
    def get_current_vitals(self):
        """Obtener datos vitales actuales desde Redis"""
        try:
            key = f"patient_vitals:{PATIENT_ID}"
            vitals = self.redis_client.hgetall(key)
            if vitals:
                print(f"📋 Datos actuales en Redis: {vitals}")
            else:
                print("📋 No hay datos en Redis para este paciente")
        except redis.RedisError as e:
            print(f"❌ Error obteniendo datos de Redis: {e}")
    
    def run_simulation(self):
        """Ejecutar la simulación principal"""
        print("🚀 Iniciando simulador de reloj inteligente...")
        print(f"👤 Paciente: {PATIENT_ID}")
        print(f"⏱️  Intervalo: {INTERVAL_SECONDS} segundos")
        print("🛑 Presiona Ctrl+C para detener")
        print("-" * 50)
        
        # Mostrar datos actuales al inicio
        self.get_current_vitals()
        
        while self.running:
            try:
                # Generar nuevos datos vitales
                vitals_data = self.generate_realistic_vitals()
                
                # Almacenar en Redis
                self.store_vitals_in_redis(vitals_data)
                
                # Esperar el intervalo especificado
                for _ in range(INTERVAL_SECONDS):
                    if not self.running:
                        break
                    time.sleep(1)
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ Error en la simulación: {e}")
                time.sleep(5)  # Esperar antes de reintentar
        
        print("\n✅ Simulador detenido correctamente")
        self.cleanup()
    
    def cleanup(self):
        """Limpiar recursos al cerrar"""
        if self.redis_client:
            try:
                self.redis_client.close()
                print("🔌 Conexión a Redis cerrada")
            except:
                pass

def main():
    """Función principal"""
    print("=" * 60)
    print("🏥 SIMULADOR DE RELOJ INTELIGENTE - DATOS VITALES")
    print("=" * 60)
    
    simulator = SmartWatchSimulator()
    simulator.run_simulation()

if __name__ == "__main__":
    main()
