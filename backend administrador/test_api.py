#!/usr/bin/env python3
"""
Script de prueba para la API CRUD del Backend Administrador
Prueba todas las funcionalidades: CRUD de usuarios, GPS, vitals, KPIs y dashboard
"""

import requests
import json
import time
from datetime import datetime

# Configuración
BASE_URL = "http://localhost:5004"
TEST_PATIENT_ID = "test-patient-123"

def test_health_check():
    """Prueba el endpoint de health check"""
    print("🔍 Probando Health Check...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health Check OK: {data}")
            return True
        else:
            print(f"❌ Health Check falló: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error en Health Check: {e}")
        return False

def test_create_user():
    """Prueba la creación de un usuario"""
    print("\n🔍 Probando Crear Usuario...")
    
    user_data = {
        "patient_id": TEST_PATIENT_ID,
        "name": "Test User",
        "date_of_birth": "1990-01-01T00:00:00Z",
        "gender": "male",
        "email": "test@example.com",
        "password": "test123",
        "medical_history": "No known conditions",
        "rol_account": "patient"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/users",
            json=user_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 201:
            data = response.json()
            print(f"✅ Usuario creado: {data}")
            return True
        else:
            print(f"❌ Error creando usuario: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error en creación de usuario: {e}")
        return False

def test_get_users():
    """Prueba obtener todos los usuarios"""
    print("\n🔍 Probando Obtener Usuarios...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/users")
        
        if response.status_code == 200:
            data = response.json()
            users = data.get("users", [])
            print(f"✅ Usuarios obtenidos: {len(users)} usuarios")
            for user in users[:3]:  # Mostrar solo los primeros 3
                print(f"   - {user['name']} ({user['patient_id']})")
            return True
        else:
            print(f"❌ Error obteniendo usuarios: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error obteniendo usuarios: {e}")
        return False

def test_get_user():
    """Prueba obtener un usuario específico"""
    print("\n🔍 Probando Obtener Usuario Específico...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/users/{TEST_PATIENT_ID}")
        
        if response.status_code == 200:
            user = response.json()
            print(f"✅ Usuario obtenido: {user['name']} ({user['email']})")
            return True
        else:
            print(f"❌ Error obteniendo usuario: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error obteniendo usuario: {e}")
        return False

def test_update_user():
    """Prueba actualizar un usuario"""
    print("\n🔍 Probando Actualizar Usuario...")
    
    update_data = {
        "name": "Test User Updated",
        "email": "test.updated@example.com",
        "medical_history": "Updated medical history",
        "rol_account": "patient"
    }
    
    try:
        response = requests.put(
            f"{BASE_URL}/api/users/{TEST_PATIENT_ID}",
            json=update_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Usuario actualizado: {data}")
            return True
        else:
            print(f"❌ Error actualizando usuario: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error actualizando usuario: {e}")
        return False

def test_get_gps_data():
    """Prueba obtener datos GPS"""
    print("\n🔍 Probando Obtener Datos GPS...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/gps?patient_id={TEST_PATIENT_ID}&limit=10")
        
        if response.status_code == 200:
            data = response.json()
            gps_data = data.get("gps_data", [])
            print(f"✅ Datos GPS obtenidos: {len(gps_data)} registros")
            return True
        else:
            print(f"❌ Error obteniendo GPS: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error obteniendo GPS: {e}")
        return False

def test_get_vital_signs():
    """Prueba obtener signos vitales"""
    print("\n🔍 Probando Obtener Signos Vitales...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/vitals?patient_id={TEST_PATIENT_ID}&limit=10")
        
        if response.status_code == 200:
            data = response.json()
            vitals = data.get("vital_signs", [])
            print(f"✅ Signos vitales obtenidos: {len(vitals)} registros")
            return True
        else:
            print(f"❌ Error obteniendo vitals: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error obteniendo vitals: {e}")
        return False

def test_get_kpis():
    """Prueba obtener KPIs de riesgo"""
    print("\n🔍 Probando Obtener KPIs...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/kpis?patient_id={TEST_PATIENT_ID}&limit=10")
        
        if response.status_code == 200:
            data = response.json()
            kpis = data.get("kpi_risk", [])
            print(f"✅ KPIs obtenidos: {len(kpis)} registros")
            return True
        else:
            print(f"❌ Error obteniendo KPIs: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error obteniendo KPIs: {e}")
        return False

def test_dashboard():
    """Prueba obtener dashboard del usuario"""
    print("\n🔍 Probando Obtener Dashboard...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/dashboard?patient_id={TEST_PATIENT_ID}")
        
        if response.status_code == 200:
            data = response.json()
            user_info = data.get("user_info", {})
            summary = data.get("summary", {})
            print(f"✅ Dashboard obtenido para: {user_info.get('name', 'N/A')}")
            print(f"   Resumen: {summary}")
            return True
        else:
            print(f"❌ Error obteniendo dashboard: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error obteniendo dashboard: {e}")
        return False

def test_delete_user():
    """Prueba eliminar un usuario"""
    print("\n🔍 Probando Eliminar Usuario...")
    
    try:
        response = requests.delete(f"{BASE_URL}/api/users/{TEST_PATIENT_ID}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Usuario eliminado: {data}")
            return True
        else:
            print(f"❌ Error eliminando usuario: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error eliminando usuario: {e}")
        return False

def main():
    """Función principal que ejecuta todas las pruebas"""
    print("🚀 Iniciando Pruebas de la API CRUD del Backend Administrador")
    print("=" * 60)
    
    # Lista de pruebas a ejecutar
    tests = [
        ("Health Check", test_health_check),
        ("Crear Usuario", test_create_user),
        ("Obtener Usuarios", test_get_users),
        ("Obtener Usuario Específico", test_get_user),
        ("Actualizar Usuario", test_update_user),
        ("Obtener Datos GPS", test_get_gps_data),
        ("Obtener Signos Vitales", test_get_vital_signs),
        ("Obtener KPIs", test_get_kpis),
        ("Obtener Dashboard", test_dashboard),
        ("Eliminar Usuario", test_delete_user),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
            time.sleep(0.5)  # Pequeña pausa entre pruebas
        except Exception as e:
            print(f"❌ Error ejecutando {test_name}: {e}")
            results.append((test_name, False))
    
    # Resumen de resultados
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE PRUEBAS")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASÓ" if success else "❌ FALLÓ"
        print(f"{status} - {test_name}")
        if success:
            passed += 1
    
    print(f"\n🎯 Resultado: {passed}/{total} pruebas pasaron")
    
    if passed == total:
        print("🎉 ¡Todas las pruebas pasaron exitosamente!")
    else:
        print("⚠️  Algunas pruebas fallaron. Revisa los logs arriba.")

if __name__ == "__main__":
    main()
