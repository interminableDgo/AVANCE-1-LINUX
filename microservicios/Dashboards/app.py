from flask import Flask, request, jsonify, Response, send_from_directory
import os
from flask_cors import CORS
import redis
import datetime
import xml.etree.ElementTree as ET
from influxdb_client import InfluxDBClient
import logging

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
# Habilitar CORS para permitir peticiones desde el origen actual
CORS(app, resources={r"/api/*": {"origins": ["*", "http://localhost:5003", "http://127.0.0.1:5003"]}})

# (XSL habilitado): servir archivos XSL para que los XML apliquen estilo en el navegador
@app.route('/xsl/<path:filename>')
def serve_xsl(filename):
    try:
        xsl_dir = os.path.join(os.path.dirname(__file__), 'xsl')
        resp = send_from_directory(xsl_dir, filename)
        # Forzar content-type adecuado para XSL
        resp.mimetype = 'text/xsl'
        resp.charset = 'utf-8'
        return resp
    except Exception as e:
        logger.error(f"❌ Error sirviendo XSL {filename}: {e}")
        return Response('<error>No se pudo cargar la hoja de estilo</error>', mimetype='application/xml'), 404

# Configuración de Redis
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = 6379
REDIS_DB = 0

# Configuración de InfluxDB
INFLUX_BUCKET_RAW = "my_app_raw_data"
INFLUX_BUCKET_PROCESSED = "my_app_processed_data"
INFLUX_ORG = "my-org"
INFLUX_TOKEN = "PpCwdSIMJdtVNgnnghBtDll0Q7KKRWzOm-LrSyCAOEo5jaVix2-NP0VPNkCoM_ztd4ZzsZzuyPi5Iuk9CD0ZCg=="
INFLUX_URL = os.getenv("INFLUX_URL", "http://localhost:8086")

class DashboardService:
    def __init__(self):
        """Inicializar el servicio de dashboard"""
        self.redis_client = None
        self.influx_client = None
        self.query_api = None
        self.setup_connections()
    
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
            self.query_api = self.influx_client.query_api()
            logger.info("✅ Conectado a InfluxDB")
            
        except Exception as e:
            logger.error(f"❌ Error configurando conexiones: {e}")
            # No bloquear el arranque del servicio; se intentará operar en modo degradado
            self.redis_client = None
            self.influx_client = None
            self.query_api = None
    
    def get_current_vitals_from_redis(self, patient_id):
        """Obtener datos vitales actuales desde Redis"""
        try:
            key = f"patient_vitals:{patient_id}"
            vitals = self.redis_client.hgetall(key)
            if vitals:
                # Convertir strings a números donde sea apropiado
                processed_vitals = {}
                for k, v in vitals.items():
                    if k in ['heart_rate', 'systolic_blood_pressure', 'diastolic_blood_pressure']:
                        try:
                            processed_vitals[k] = float(v)
                        except ValueError:
                            processed_vitals[k] = v
                    else:
                        processed_vitals[k] = v
                return processed_vitals
            return None
        except Exception as e:
            logger.error(f"❌ Error obteniendo datos de Redis: {e}")
            return None
    
    def get_vitals_gps_data_from_influxdb(self, patient_id, hours=24):
        """Obtener datos de Vitals y GPS desde InfluxDB"""
        try:
            # Calcular rango de tiempo (últimas X horas)
            end_time = datetime.datetime.utcnow()
            start_time = end_time - datetime.timedelta(hours=hours)
            
            # Query para vitales
            vitals_query = f'''
            from(bucket: "{INFLUX_BUCKET_RAW}")
              |> range(start: {start_time.strftime('%Y-%m-%dT%H:%M:%SZ')}, stop: {end_time.strftime('%Y-%m-%dT%H:%M:%SZ')})
              |> filter(fn: (r) => r["_measurement"] == "vitals")
              |> filter(fn: (r) => r["patient_id"] == "{patient_id}")
              |> sort(columns: ["_time"])
            '''
            
            # Query para GPS
            gps_query = f'''
            from(bucket: "{INFLUX_BUCKET_RAW}")
              |> range(start: {start_time.strftime('%Y-%m-%dT%H:%M:%SZ')}, stop: {end_time.strftime('%Y-%m-%dT%H:%M:%SZ')})
              |> filter(fn: (r) => r["_measurement"] == "gps")
              |> filter(fn: (r) => r["patient_id"] == "{patient_id}")
              |> sort(columns: ["_time"])
            '''
            
            # Procesar datos de vitales
            vitals_data = []
            try:
                vitals_tables = self.query_api.query(query=vitals_query)
                temp_vitals = {}
                
                for table in vitals_tables:
                    for record in table.records:
                        timestamp = record.get_time()
                        field = record.get_field()
                        value = record.get_value()
                        
                        if timestamp not in temp_vitals:
                            temp_vitals[timestamp] = {'timestamp': timestamp.isoformat()}
                        temp_vitals[timestamp][field] = value
                
                # Convertir a lista ordenada
                for timestamp in sorted(temp_vitals.keys()):
                    vitals_data.append(temp_vitals[timestamp])
                    
            except Exception as e:
                logger.error(f"❌ Error procesando vitales: {e}")
            
            # Procesar datos de GPS
            gps_data = []
            try:
                gps_tables = self.query_api.query(query=gps_query)
                temp_gps = {}
                
                for table in gps_tables:
                    for record in table.records:
                        timestamp = record.get_time()
                        field = record.get_field()
                        value = record.get_value()
                        
                        if timestamp not in temp_gps:
                            temp_gps[timestamp] = {'timestamp': timestamp.isoformat()}
                        temp_gps[timestamp][field] = value
                
                # Convertir a lista ordenada
                for timestamp in sorted(temp_gps.keys()):
                    gps_data.append(temp_gps[timestamp])
                    
            except Exception as e:
                logger.error(f"❌ Error procesando GPS: {e}")
            
            return {
                'vitals': vitals_data,
                'gps': gps_data,
                'time_range': {
                    'start': start_time.isoformat(),
                    'end': end_time.isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo datos de InfluxDB: {e}")
            return None
    
    def get_kpis_risk_data_from_influxdb(self, patient_id, days=7):
        """Obtener datos de KPIs y Risk Inference desde InfluxDB"""
        try:
            # Calcular rango de tiempo (últimos X días)
            end_time = datetime.datetime.utcnow()
            start_time = end_time - datetime.timedelta(days=days)
            
            # Query para KPIs
            kpis_query = f'''
            from(bucket: "{INFLUX_BUCKET_PROCESSED}")
              |> range(start: {start_time.strftime('%Y-%m-%dT%H:%M:%SZ')}, stop: {end_time.strftime('%Y-%m-%dT%H:%M:%SZ')})
              |> filter(fn: (r) => r["_measurement"] == "KPI_daily")
              |> filter(fn: (r) => r["patient_id"] == "{patient_id}")
              |> sort(columns: ["_time"])
            '''
            
            # Query para Risk Inference
            risk_query = f'''
            from(bucket: "{INFLUX_BUCKET_PROCESSED}")
              |> range(start: {start_time.strftime('%Y-%m-%dT%H:%M:%SZ')}, stop: {end_time.strftime('%Y-%m-%dT%H:%M:%SZ')})
              |> filter(fn: (r) => r["_measurement"] == "Risk_inference")
              |> filter(fn: (r) => r["patient_id"] == "{patient_id}")
              |> sort(columns: ["_time"])
            '''
            
            # Procesar datos de KPIs
            kpis_data = []
            try:
                kpis_tables = self.query_api.query(query=kpis_query)
                temp_kpis = {}
                
                for table in kpis_tables:
                    for record in table.records:
                        timestamp = record.get_time()
                        field = record.get_field()
                        value = record.get_value()
                        
                        if timestamp not in temp_kpis:
                            temp_kpis[timestamp] = {'timestamp': timestamp.isoformat()}
                        temp_kpis[timestamp][field] = value
                
                # Convertir a lista ordenada
                for timestamp in sorted(temp_kpis.keys()):
                    kpis_data.append(temp_kpis[timestamp])
                    
            except Exception as e:
                logger.error(f"❌ Error procesando KPIs: {e}")
            
            # Procesar datos de Risk
            risk_data = []
            try:
                risk_tables = self.query_api.query(query=risk_query)
                temp_risk = {}
                
                for table in risk_tables:
                    for record in table.records:
                        timestamp = record.get_time()
                        field = record.get_field()
                        value = record.get_value()
                        
                        if timestamp not in temp_risk:
                            temp_risk[timestamp] = {
                                'timestamp': timestamp.isoformat(),
                                'model_name': record.values.get('model_name', ''),
                                'model_version': record.values.get('model_version', '')
                            }
                        temp_risk[timestamp][field] = value
                
                # Convertir a lista ordenada
                for timestamp in sorted(temp_risk.keys()):
                    risk_data.append(temp_risk[timestamp])
                    
            except Exception as e:
                logger.error(f"❌ Error procesando Risk: {e}")
            
            return {
                'kpis': kpis_data,
                'risk': risk_data,
                'time_range': {
                    'start': start_time.isoformat(),
                    'end': end_time.isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo datos de KPIs/Risk: {e}")
            return None
    
    def create_xml_response(self, data, root_name):
        """Crear respuesta XML desde datos"""
        try:
            root = ET.Element(root_name)
            root.set('timestamp', datetime.datetime.now().isoformat())
            
            if isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, list):
                        list_elem = ET.SubElement(root, key)
                        for item in value:
                            if isinstance(item, dict):
                                item_elem = ET.SubElement(list_elem, 'item')
                                for k, v in item.items():
                                    elem = ET.SubElement(item_elem, k)
                                    elem.text = str(v)
                            else:
                                elem = ET.SubElement(list_elem, 'item')
                                elem.text = str(item)
                    else:
                        elem = ET.SubElement(root, key)
                        elem.text = str(value)
            
            xml_str = ET.tostring(root, encoding='unicode')
            return xml_str
            
        except Exception as e:
            logger.error(f"❌ Error creando XML: {e}")
            return f"<error>Error generando XML: {str(e)}</error>"

# Instancia global del servicio de dashboard
dashboard_service = DashboardService()

@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint de salud del microservicio"""
    return jsonify({
        "status": "healthy",
        "service": "Dashboards",
        "timestamp": datetime.datetime.now().isoformat()
    })

@app.route('/api/current-vitals/<patient_id>', methods=['GET'])
def get_current_vitals(patient_id):
    """Endpoint para obtener datos vitales actuales desde Redis (JSON)"""
    try:
        vitals = dashboard_service.get_current_vitals_from_redis(patient_id)
        
        if vitals:
            return jsonify({
                "patient_id": patient_id,
                "data": vitals,
                "status": "success",
                "timestamp": datetime.datetime.now().isoformat()
            }), 200
        else:
            return jsonify({
                "message": f"No se encontraron datos actuales para el paciente {patient_id}",
                "status": "not_found"
            }), 404
            
    except Exception as e:
        logger.error(f"❌ Error obteniendo datos actuales para {patient_id}: {e}")
        return jsonify({
            "error": "Error interno del servidor",
            "status": "error"
        }), 500

@app.route('/api/vitals-gps/<patient_id>', methods=['GET'])
def get_vitals_gps_xml(patient_id):
    """Endpoint para obtener datos de Vitals y GPS desde InfluxDB (XML)"""
    try:
        hours = request.args.get('hours', 24, type=int)
        fmt = request.args.get('format', request.args.get('fmt', 'html'))
        data = dashboard_service.get_vitals_gps_data_from_influxdb(patient_id, hours)
        
        if data:
            if fmt.lower() == 'xml':
                xml_response = dashboard_service.create_xml_response(data, 'vitals_gps_data')
                styled_xml = (
                    '<?xml version="1.0" encoding="UTF-8"?>\n'
                    '<?xml-stylesheet type="text/xsl" href="/xsl/vitals_gps.xsl"?>\n'
                    f'{xml_response}'
                )
                return Response(styled_xml, content_type='text/xml; charset=UTF-8'), 200
            # HTML por defecto
            with app.test_request_context(query_string={'hours': hours}):
                return view_vitals_gps_html(patient_id)
        else:
            return Response('<error>No se encontraron datos de Vitals/GPS</error>', 
                          mimetype='application/xml'), 404
            
    except Exception as e:
        logger.error(f"❌ Error obteniendo datos Vitals/GPS para {patient_id}: {e}")
        return Response(f'<error>Error interno del servidor: {str(e)}</error>', 
                      mimetype='application/xml'), 500

@app.route('/view/vitals-gps/<patient_id>', methods=['GET'])
def view_vitals_gps_html(patient_id):
    try:
        hours = request.args.get('hours', 24, type=int)
        data = dashboard_service.get_vitals_gps_data_from_influxdb(patient_id, hours)
        if not data:
            return Response('<h3 style="font-family:Segoe UI">Sin datos</h3>', mimetype='text/html'), 200
        # Render HTML simple con estilos inline
        html_parts = []
        html_parts.append('<!DOCTYPE html><html><head><meta charset="utf-8"><title>Vitals & GPS</title>')
        html_parts.append('<style>body{font-family:Segoe UI,Tahoma,Arial,sans-serif;background:#f5f7fb;margin:0;padding:20px}.card{background:#fff;border-radius:12px;box-shadow:0 5px 14px rgba(0,0,0,.05);padding:20px;margin:auto;max-width:1100px}h2{margin:0 0 10px}.muted{color:#6c757d;font-size:12px}table{width:100%;border-collapse:collapse;margin-top:16px}th,td{padding:10px;border-bottom:1px solid #eee;text-align:left}th{background:#fafbff}.tag{display:inline-block;padding:2px 8px;border-radius:10px;background:#eef2ff;color:#4338ca;font-size:12px}</style></head><body>')
        html_parts.append('<div class="card">')
        html_parts.append(f'<h2>Vitals & GPS <span class="tag">Últimas {hours}h</span></h2>')
        tr = data.get('time_range', {})
        html_parts.append(f'<div class="muted">Rango: {tr.get("start","-")} — {tr.get("end","-")}</div>')
        # Vitals
        html_parts.append('<h3>Vitals</h3><table><thead><tr><th>Timestamp</th><th>HR</th><th>Sys BP</th><th>Dia BP</th></tr></thead><tbody>')
        for item in data.get('vitals', [])[:500]:
            html_parts.append(f'<tr><td>{item.get("timestamp","-")}</td><td>{item.get("heart_rate","-")}</td><td>{item.get("systolic_bp","-")}</td><td>{item.get("diastolic_bp","-")}</td></tr>')
        html_parts.append('</tbody></table>')
        # GPS
        html_parts.append('<h3 style="margin-top:24px">GPS</h3><table><thead><tr><th>Timestamp</th><th>Lat</th><th>Lon</th></tr></thead><tbody>')
        for item in data.get('gps', [])[:500]:
            html_parts.append(f'<tr><td>{item.get("timestamp","-")}</td><td>{item.get("lat","-")}</td><td>{item.get("lon","-")}</td></tr>')
        html_parts.append('</tbody></table></div></body></html>')
        return Response(''.join(html_parts), mimetype='text/html'), 200
    except Exception as e:
        logger.error(f"❌ Error renderizando vista HTML Vitals/GPS: {e}")
        return Response('<h3>Error interno</h3>', mimetype='text/html'), 500

@app.route('/api/kpis-risk/<patient_id>', methods=['GET'])
def get_kpis_risk_xml(patient_id):
    """Endpoint para obtener datos de KPIs y Risk Inference desde InfluxDB (XML)"""
    try:
        days = request.args.get('days', 7, type=int)
        fmt = request.args.get('format', request.args.get('fmt', 'html'))
        data = dashboard_service.get_kpis_risk_data_from_influxdb(patient_id, days)
        
        if data:
            if fmt.lower() == 'xml':
                xml_response = dashboard_service.create_xml_response(data, 'kpis_risk_data')
                styled_xml = (
                    '<?xml version="1.0" encoding="UTF-8"?>\n'
                    '<?xml-stylesheet type="text/xsl" href="/xsl/kpis_risk.xsl"?>\n'
                    f'{xml_response}'
                )
                return Response(styled_xml, content_type='text/xml; charset=UTF-8'), 200
            # HTML por defecto
            with app.test_request_context(query_string={'days': days}):
                return view_kpis_risk_html(patient_id)
        else:
            return Response('<error>No se encontraron datos de KPIs/Risk</error>', 
                          mimetype='application/xml'), 404
            
    except Exception as e:
        logger.error(f"❌ Error obteniendo datos KPIs/Risk para {patient_id}: {e}")
        return Response(f'<error>Error interno del servidor: {str(e)}</error>', 
                      mimetype='application/xml'), 500

@app.route('/view/kpis-risk/<patient_id>', methods=['GET'])
def view_kpis_risk_html(patient_id):
    try:
        days = request.args.get('days', 7, type=int)
        data = dashboard_service.get_kpis_risk_data_from_influxdb(patient_id, days)
        if not data:
            return Response('<h3 style="font-family:Segoe UI">Sin datos</h3>', mimetype='text/html'), 200
        html = []
        html.append('<!DOCTYPE html><html><head><meta charset="utf-8"><title>KPIs & Risk</title>')
        html.append('<style>body{font-family:Segoe UI,Tahoma,Arial,sans-serif;background:#f5f7fb;margin:0;padding:20px}.grid{display:grid;grid-template-columns:1fr 1fr;gap:20px;max-width:1100px;margin:auto}.card{background:#fff;border-radius:12px;box-shadow:0 5px 14px rgba(0,0,0,.05);padding:20px}h2,h3{margin:0 0 10px}table{width:100%;border-collapse:collapse;margin-top:16px}th,td{padding:10px;border-bottom:1px solid #eee;text-align:left}th{background:#fafbff}.muted{color:#6c757d;font-size:12px}</style></head><body>')
        html.append('<div class="grid">')
        # KPIs
        html.append('<div class="card">')
        tr = data.get('time_range', {})
        html.append(f'<h2>KPIs diarios</h2><div class="muted">Rango: {tr.get("start","-")} — {tr.get("end","-")}</div>')
        html.append('<table><thead><tr><th>Timestamp</th><th>Avg HR</th><th>Distancia (m)</th><th>% HR Alto</th><th>Presión Prom.</th><th>Alertas</th><th>Activo (min)</th><th>Sedentario (min)</th></tr></thead><tbody>')
        for item in data.get('kpis', [])[:500]:
            html.append(f'<tr><td>{item.get("timestamp","-")}</td><td>{item.get("average_heart_rate","-")}</td><td>{item.get("total_distance_traveled","-")}</td><td>{item.get("high_heart_rate_percentage","-")}</td><td>{item.get("average_arterial_pressure","-")}</td><td>{item.get("daily_alert_count","-")}</td><td>{item.get("time_active","-")}</td><td>{item.get("time_sedentary","-")}</td></tr>')
        html.append('</tbody></table></div>')
        # Risk
        html.append('<div class="card">')
        html.append('<h2>Risk Inference</h2><table><thead><tr><th>Timestamp</th><th>Modelo</th><th>Versión</th><th>Score</th><th>Label</th></tr></thead><tbody>')
        for item in data.get('risk', [])[:500]:
            html.append(f'<tr><td>{item.get("timestamp","-")}</td><td>{item.get("model_name","-")}</td><td>{item.get("model_version","-")}</td><td>{item.get("risk_score","-")}</td><td>{item.get("risk_label","-")}</td></tr>')
        html.append('</tbody></table></div></div></body></html>')
        return Response(''.join(html), mimetype='text/html'), 200
    except Exception as e:
        logger.error(f"❌ Error renderizando vista HTML KPIs/Risk: {e}")
        return Response('<h3>Error interno</h3>', mimetype='text/html'), 500

if __name__ == '__main__':
    logger.info("🚀 Iniciando microservicio Dashboards...")
    logger.info("📡 Endpoints disponibles:")
    logger.info("  GET /api/current-vitals/<patient_id> - Datos actuales desde Redis (JSON)")
    logger.info("  GET /api/vitals-gps/<patient_id> - Datos Vitals/GPS desde InfluxDB (XML)")
    logger.info("  GET /api/kpis-risk/<patient_id> - Datos KPIs/Risk desde InfluxDB (XML)")
    logger.info("  GET /health - Estado del servicio")
    
    app.run(host='0.0.0.0', port=5002, debug=True)
