import time
import datetime
import random
import requests
import signal
import sys
import json

# Configuración del microservicio
MICROSERVICE_URL = "http://localhost:5000"
VITALS_ENDPOINT = f"{MICROSERVICE_URL}/vitals"

# Datos del paciente (mismo que en el script de InfluxDB)
PATIENT_ID = "20250831-5f21-4f32-8e12-28e441467a18"

# Configuración de la simulación
INTERVAL_SECONDS = 30  # Cada 30 segundos

class SmartWatchSimulator:
    def __init__(self):
        """Inicializar el simulador de reloj inteligente"""
        self.running = True
        self.setup_signal_handlers()
        self.test_microservice_connection()
    
    def setup_signal_handlers(self):
        """Configurar manejadores de señales para cierre graceful"""
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Manejador para cierre graceful del programa"""
        print(f"\n🛑 Recibida señal {signum}. Cerrando simulador...")
        self.running = False
    
    def test_microservice_connection(self):
        """Probar conexión con el microservicio"""
        try:
            response = requests.get(f"{MICROSERVICE_URL}/health", timeout=5)
            if response.status_code == 200:
                print("✅ Microservicio AltaDeDatos está disponible")
                return True
            else:
                print(f"❌ Microservicio respondió con código: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Error conectando al microservicio: {e}")
            print("Asegúrate de que el microservicio esté ejecutándose en http://localhost:5000")
            return False
    
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
    
    def send_vitals_to_microservice(self, vitals_data):
        """Enviar datos vitales al microservicio"""
        try:
            headers = {
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                VITALS_ENDPOINT,
                json=vitals_data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"📊 Datos enviados al microservicio - HR: {vitals_data['heart_rate']} bpm, "
                      f"SBP: {vitals_data['systolic_blood_pressure']}, "
                      f"DBP: {vitals_data['diastolic_blood_pressure']}")
                return True
            else:
                print(f"❌ Error del microservicio: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Error enviando datos al microservicio: {e}")
            return False
    
    def get_current_vitals_from_microservice(self):
        """Obtener datos vitales actuales desde el microservicio"""
        try:
            response = requests.get(f"{MICROSERVICE_URL}/vitals/{PATIENT_ID}", timeout=5)
            if response.status_code == 200:
                result = response.json()
                print(f"📋 Datos actuales en el microservicio: {result['data']}")
            elif response.status_code == 404:
                print("📋 No hay datos en el microservicio para este paciente")
            else:
                print(f"❌ Error obteniendo datos: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ Error obteniendo datos del microservicio: {e}")
    
    def run_simulation(self):
        """Ejecutar la simulación principal"""
        print("🚀 Iniciando simulador de reloj inteligente...")
        print(f"👤 Paciente: {PATIENT_ID}")
        print(f"⏱️  Intervalo: {INTERVAL_SECONDS} segundos")
        print(f"🌐 Microservicio: {MICROSERVICE_URL}")
        print("🛑 Presiona Ctrl+C para detener")
        print("-" * 60)
        
        # Mostrar datos actuales al inicio
        self.get_current_vitals_from_microservice()
        
        while self.running:
            try:
                # Generar nuevos datos vitales
                vitals_data = self.generate_realistic_vitals()
                
                # Enviar al microservicio
                success = self.send_vitals_to_microservice(vitals_data)
                
                if not success:
                    print("⚠️  Reintentando en 5 segundos...")
                    time.sleep(5)
                    continue
                
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

def main():
    """Función principal"""
    print("=" * 70)
    print("🏥 SIMULADOR DE RELOJ INTELIGENTE - MICROSERVICIO")
    print("=" * 70)
    
    simulator = SmartWatchSimulator()
    simulator.run_simulation()

if __name__ == "__main__":
    main()
