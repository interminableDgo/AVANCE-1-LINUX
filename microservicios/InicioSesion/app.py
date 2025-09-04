from flask import Flask, request, jsonify, render_template_string, send_file
import psycopg2
import hashlib
import datetime
import logging
import os

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuración de PostgreSQL
POSTGRES_HOST = "localhost"
POSTGRES_PORT = 5432
POSTGRES_DB = "General information users"
POSTGRES_USER = "hoonigans"
POSTGRES_PASSWORD = "666"

class AuthService:
    def __init__(self):
        """Inicializar el servicio de autenticación"""
        self.connection = None
        self.setup_connection()
    
    def setup_connection(self):
        """Configurar conexión a PostgreSQL"""
        try:
            self.connection = psycopg2.connect(
                host=POSTGRES_HOST,
                port=POSTGRES_PORT,
                database=POSTGRES_DB,
                user=POSTGRES_USER,
                password=POSTGRES_PASSWORD
            )
            # Evita bloquear la sesión cuando ocurre un error en una transacción
            self.connection.autocommit = True
            logger.info("✅ Conectado a PostgreSQL")
        except Exception as e:
            logger.error(f"❌ Error conectando a PostgreSQL: {e}")
            raise

    def ensure_connection(self):
        """Reestablece la conexión si está cerrada o en mal estado."""
        try:
            if self.connection is None or self.connection.closed:
                self.setup_connection()
        except Exception as e:
            logger.error(f"❌ Error reestableciendo conexión a PostgreSQL: {e}")
            raise
    
    def hash_password(self, password):
        """Hashear contraseña usando SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_user(self, email, password):
        """Verificar credenciales de usuario (acepta hash o texto plano)"""
        try:
            self.ensure_connection()
            cursor = self.connection.cursor()
            input_email = (email or "").strip().lower()
            # La tabla real en Postgres es user_information
            # Columnas esperadas: patient_id, name, date_of_birth, gender, email, password, medical_history, rol_account
            query = """
            SELECT patient_id, name, email, rol_account, medical_history, date_of_birth, gender, password
            FROM user_information 
            WHERE LOWER(email) = %s
            """
            cursor.execute(query, (input_email,))
            row = cursor.fetchone()
            cursor.close()

            if not row:
                logger.warning(f"⚠️ Usuario no encontrado: {email}")
                return None

            stored_password = (row[7] or "").strip()
            hashed_input = self.hash_password(password)

            if stored_password == password or stored_password == hashed_input:
                user_data = {
                    'patient_id': row[0],
                    'name': row[1],
                    'email': row[2],
                    'rol_account': row[3],
                    'medical_history': row[4],
                    'date_of_birth': row[5].isoformat() if row[5] else None,
                    'gender': row[6]
                }
                logger.info(f"✅ Usuario autenticado: {email}")
                return user_data

            logger.warning(f"⚠️ Contraseña inválida para: {email}")
            return None

        except Exception as e:
            logger.error(f"❌ Error verificando usuario: {e}")
            try:
                # En caso de error, garantizar que la conexión no quede en estado abortado
                if self.connection and not self.connection.closed:
                    self.connection.rollback()
            except Exception:
                pass
            return None
    
    def register_user(self, user_data):
        """Registrar nuevo usuario"""
        try:
            cursor = self.connection.cursor()
            
            # Verificar si el email ya existe
            check_query = "SELECT patient_id FROM user_information WHERE email = %s"
            cursor.execute(check_query, (user_data['email'],))
            if cursor.fetchone():
                cursor.close()
                return False, "El email ya está registrado"
            
            # Generar nuevo patient_id (UUID simple)
            import uuid
            patient_id = str(uuid.uuid4())
            
            # Hashear contraseña
            hashed_password = self.hash_password(user_data['password'])
            
            # Insertar nuevo usuario
            insert_query = """
            INSERT INTO user_information (patient_id, name, date_of_birth, gender, email, password, medical_history, rol_account)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            cursor.execute(insert_query, (
                patient_id,
                user_data['name'],
                user_data['date_of_birth'],
                user_data['gender'],
                user_data['email'],
                hashed_password,
                user_data.get('medical_history', ''),
                'patient'  # Por defecto es paciente
            ))
            
            self.connection.commit()
            cursor.close()
            
            logger.info(f"✅ Usuario registrado: {user_data['email']}")
            return True, "Usuario registrado exitosamente"
            
        except Exception as e:
            logger.error(f"❌ Error registrando usuario: {e}")
            return False, f"Error registrando usuario: {str(e)}"

# Instancia global del servicio de autenticación
auth_service = AuthService()

# Plantillas HTML
LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Inicio de Sesión - Sistema de Monitoreo</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            --secondary-gradient: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            --success-gradient: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            --card-shadow: 0 20px 60px rgba(0, 0, 0, 0.1);
            --card-shadow-hover: 0 30px 80px rgba(0, 0, 0, 0.15);
            --border-radius: 24px;
            --transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }

        body {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            padding: 20px 0;
        }

        .login-card {
            background: rgba(255, 255, 255, 0.98);
            backdrop-filter: blur(20px);
            border-radius: var(--border-radius);
            box-shadow: var(--card-shadow);
            border: 1px solid rgba(255, 255, 255, 0.2);
            transition: var(--transition);
        }

        .login-card:hover {
            transform: translateY(-5px);
            box-shadow: var(--card-shadow-hover);
        }

        .card-body {
            padding: 3rem 2.5rem;
        }

        .brand-section {
            text-align: center;
            margin-bottom: 2.5rem;
        }

        .brand-icon {
            width: 80px;
            height: 80px;
            background: var(--primary-gradient);
            border-radius: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 1.5rem;
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
        }

        .brand-icon i {
            font-size: 2.5rem;
            color: white;
        }

        .brand-title {
            font-weight: 700;
            color: #2d3748;
            margin-bottom: 0.5rem;
            font-size: 1.75rem;
        }

        .brand-subtitle {
            color: #718096;
            font-weight: 400;
            font-size: 1rem;
        }

        .form-label {
            font-weight: 600;
            color: #4a5568;
            margin-bottom: 0.75rem;
            font-size: 0.95rem;
        }

        .input-group {
            border-radius: 16px;
            overflow: hidden;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
            transition: var(--transition);
        }

        .input-group:focus-within {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.15);
        }

        .input-group-text {
            background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
            border: none;
            color: #667eea;
            font-size: 1.1rem;
            padding: 0.875rem 1rem;
            min-width: 50px;
            justify-content: center;
        }

        .form-control {
            border: none;
            padding: 0.875rem 1rem;
            font-size: 1rem;
            background: #f8fafc;
            color: #2d3748;
            font-weight: 500;
        }

        .form-control:focus {
            background: white;
            box-shadow: none;
            outline: none;
        }

        .form-control::placeholder {
            color: #a0aec0;
            font-weight: 400;
        }

        .btn-login {
            background: var(--primary-gradient);
            border: none;
            border-radius: 16px;
            padding: 1rem;
            font-weight: 600;
            font-size: 1rem;
            color: white;
            transition: var(--transition);
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
            width: 100%;
            margin-bottom: 1.5rem;
        }

        .btn-login:hover {
            transform: translateY(-3px);
            box-shadow: 0 12px 35px rgba(102, 126, 234, 0.4);
            color: white;
        }

        .btn-login:active {
            transform: translateY(-1px);
        }

        .register-link {
            text-align: center;
            margin-top: 1rem;
        }

        .register-link a {
            color: #667eea;
            text-decoration: none;
            font-weight: 600;
            transition: var(--transition);
        }

        .register-link a:hover {
            color: #764ba2;
            text-decoration: underline;
        }

        .alert {
            border: none;
            border-radius: 16px;
            font-weight: 500;
            margin-top: 1rem;
        }

        .alert-success {
            background: var(--success-gradient);
            color: white;
        }

        .alert-danger {
            background: var(--secondary-gradient);
            color: white;
        }

        /* Animaciones */
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .login-card {
            animation: fadeInUp 0.8s ease-out;
        }

        /* Responsive */
        @media (max-width: 768px) {
            .card-body {
                padding: 2rem 1.5rem;
            }
            
            .brand-icon {
                width: 60px;
                height: 60px;
            }
            
            .brand-icon i {
                font-size: 2rem;
            }
            
            .brand-title {
                font-size: 1.5rem;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="row justify-content-center">
            <div class="col-md-6 col-lg-4">
                <div class="card login-card border-0">
                    <div class="card-body">
                        <div class="brand-section">
                            <div class="brand-icon">
                                <i class="fas fa-heartbeat"></i>
                            </div>
                            <h3 class="brand-title">Sistema de Monitoreo</h3>
                            <p class="brand-subtitle">Inicia sesión para acceder a tu dashboard</p>
                        </div>
                        
                        <form id="loginForm">
                            <div class="mb-4">
                                <label for="email" class="form-label">Email</label>
                                <div class="input-group">
                                    <span class="input-group-text">
                                        <i class="fas fa-envelope"></i>
                                    </span>
                                    <input type="email" class="form-control" id="email" name="email" placeholder="tu@email.com" required>
                                </div>
                            </div>
                            
                            <div class="mb-4">
                                <label for="password" class="form-label">Contraseña</label>
                                <div class="input-group">
                                    <span class="input-group-text">
                                        <i class="fas fa-lock"></i>
                                    </span>
                                    <input type="password" class="form-control" id="password" name="password" placeholder="••••••••" required>
                                </div>
                            </div>
                            
                            <button type="submit" class="btn btn-login">
                                <i class="fas fa-sign-in-alt me-2"></i>Iniciar Sesión
                            </button>
                        </form>
                        
                        <div class="register-link">
                            <a href="/register">¿No tienes cuenta? Regístrate aquí</a>
                        </div>
                        
                        <div id="alertContainer"></div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        document.getElementById('loginForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const data = Object.fromEntries(formData);
            
            try {
                const response = await fetch('/api/login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                if (result.success) {
                    // Guardar datos del usuario en localStorage
                    localStorage.setItem('user', JSON.stringify(result.user));
                    // Redirigir según rol
                    if (result.redirect) {
                        window.location.href = result.redirect;
                    } else {
                        window.location.href = '/frontendUsuario.html';
                    }
                } else {
                    showAlert(result.message, 'danger');
                }
            } catch (error) {
                showAlert('Error de conexión. Intenta nuevamente.', 'danger');
            }
        });
        
        function showAlert(message, type) {
            const alertContainer = document.getElementById('alertContainer');
            alertContainer.innerHTML = `
                <div class="alert alert-${type} alert-dismissible fade show" role="alert">
                    ${message}
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                </div>
            `;
        }
    </script>
</body>
</html>
'''

REGISTER_TEMPLATE = '''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Registro - Sistema de Monitoreo</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            --secondary-gradient: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            --success-gradient: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            --card-shadow: 0 20px 60px rgba(0, 0, 0, 0.1);
            --card-shadow-hover: 0 30px 80px rgba(0, 0, 0, 0.15);
            --border-radius: 24px;
            --transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }

        body {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            padding: 20px 0;
        }

        .register-card {
            background: rgba(255, 255, 255, 0.98);
            backdrop-filter: blur(20px);
            border-radius: var(--border-radius);
            box-shadow: var(--card-shadow);
            border: 1px solid rgba(255, 255, 255, 0.2);
            transition: var(--transition);
        }

        .register-card:hover {
            transform: translateY(-5px);
            box-shadow: var(--card-shadow-hover);
        }

        .card-body {
            padding: 3rem 2.5rem;
        }

        .brand-section {
            text-align: center;
            margin-bottom: 2.5rem;
        }

        .brand-icon {
            width: 80px;
            height: 80px;
            background: var(--secondary-gradient);
            border-radius: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 1.5rem;
            box-shadow: 0 8px 25px rgba(240, 147, 251, 0.3);
        }

        .brand-icon i {
            font-size: 2.5rem;
            color: white;
        }

        .brand-title {
            font-weight: 700;
            color: #2d3748;
            margin-bottom: 0.5rem;
            font-size: 1.75rem;
        }

        .brand-subtitle {
            color: #718096;
            font-weight: 400;
            font-size: 1rem;
        }

        .form-label {
            font-weight: 600;
            color: #4a5568;
            margin-bottom: 0.75rem;
            font-size: 0.95rem;
        }

        .input-group {
            border-radius: 16px;
            overflow: hidden;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
            transition: var(--transition);
        }

        .input-group:focus-within {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.15);
        }

        .input-group-text {
            background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
            border: none;
            color: #667eea;
            font-size: 1.1rem;
            padding: 0.875rem 1rem;
            min-width: 50px;
            justify-content: center;
        }

        .form-control, .form-select {
            border: none;
            padding: 0.875rem 1rem;
            font-size: 1rem;
            background: #f8fafc;
            color: #2d3748;
            font-weight: 500;
        }

        .form-control:focus, .form-select:focus {
            background: white;
            box-shadow: none;
            outline: none;
        }

        .form-control::placeholder {
            color: #a0aec0;
            font-weight: 400;
        }

        .btn-register {
            background: var(--secondary-gradient);
            border: none;
            border-radius: 16px;
            padding: 1rem;
            font-weight: 600;
            font-size: 1rem;
            color: white;
            transition: var(--transition);
            box-shadow: 0 8px 25px rgba(240, 147, 251, 0.3);
            width: 100%;
            margin-bottom: 1.5rem;
        }

        .btn-register:hover {
            transform: translateY(-3px);
            box-shadow: 0 12px 35px rgba(240, 147, 251, 0.4);
            color: white;
        }

        .btn-register:active {
            transform: translateY(-1px);
        }

        .login-link {
            text-align: center;
            margin-top: 1rem;
        }

        .login-link a {
            color: #f093fb;
            text-decoration: none;
            font-weight: 600;
            transition: var(--transition);
        }

        .login-link a:hover {
            color: #f5576c;
            text-decoration: underline;
        }

        .alert {
            border: none;
            border-radius: 16px;
            font-weight: 500;
            margin-top: 1rem;
        }

        .alert-success {
            background: var(--success-gradient);
            color: white;
        }

        .alert-danger {
            background: var(--secondary-gradient);
            color: white;
        }

        /* Animaciones */
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .register-card {
            animation: fadeInUp 0.8s ease-out;
        }

        /* Responsive */
        @media (max-width: 768px) {
            .card-body {
                padding: 2rem 1.5rem;
            }
            
            .brand-icon {
                width: 60px;
                height: 60px;
            }
            
            .brand-icon i {
                font-size: 2rem;
            }
            
            .brand-title {
                font-size: 1.5rem;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="row justify-content-center">
            <div class="col-md-8 col-lg-6">
                <div class="card register-card border-0">
                    <div class="card-body">
                        <div class="brand-section">
                            <div class="brand-icon">
                                <i class="fas fa-user-plus"></i>
                            </div>
                            <h3 class="brand-title">Registro de Usuario</h3>
                            <p class="brand-subtitle">Crea tu cuenta para acceder al sistema</p>
                        </div>
                        
                        <form id="registerForm">
                            <div class="row">
                                <div class="col-md-6 mb-4">
                                    <label for="name" class="form-label">Nombre Completo</label>
                                    <div class="input-group">
                                        <span class="input-group-text">
                                            <i class="fas fa-user"></i>
                                        </span>
                                        <input type="text" class="form-control" id="name" name="name" placeholder="Tu nombre completo" required>
                                    </div>
                                </div>
                                
                                <div class="col-md-6 mb-4">
                                    <label for="email" class="form-label">Email</label>
                                    <div class="input-group">
                                        <span class="input-group-text">
                                            <i class="fas fa-envelope"></i>
                                        </span>
                                        <input type="email" class="form-control" id="email" name="email" placeholder="tu@email.com" required>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="row">
                                <div class="col-md-6 mb-4">
                                    <label for="date_of_birth" class="form-label">Fecha de Nacimiento</label>
                                    <div class="input-group">
                                        <span class="input-group-text">
                                            <i class="fas fa-calendar"></i>
                                        </span>
                                        <input type="date" class="form-control" id="date_of_birth" name="date_of_birth" required>
                                    </div>
                                </div>
                                
                                <div class="col-md-6 mb-4">
                                    <label for="gender" class="form-label">Género</label>
                                    <div class="input-group">
                                        <span class="input-group-text">
                                            <i class="fas fa-venus-mars"></i>
                                        </span>
                                        <select class="form-select" id="gender" name="gender" required>
                                            <option value="">Seleccionar...</option>
                                            <option value="Masculino">Masculino</option>
                                            <option value="Femenino">Femenino</option>
                                            <option value="Prefiero no decirlo">Prefiero no decirlo</option>
                                            <option value="Otro">Otro</option>
                                        </select>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="mb-4">
                                <label for="password" class="form-label">Contraseña</label>
                                <div class="input-group">
                                    <span class="input-group-text">
                                        <i class="fas fa-lock"></i>
                                    </span>
                                    <input type="password" class="form-control" id="password" name="password" placeholder="••••••••" required>
                                </div>
                            </div>
                            
                            <div class="mb-4">
                                <label for="medical_history" class="form-label">Historial Médico (Opcional)</label>
                                <div class="input-group">
                                    <span class="input-group-text">
                                        <i class="fas fa-stethoscope"></i>
                                    </span>
                                    <textarea class="form-control" id="medical_history" name="medical_history" rows="3" placeholder="Describe tu historial médico..."></textarea>
                                </div>
                            </div>
                            
                            <button type="submit" class="btn btn-register">
                                <i class="fas fa-user-plus me-2"></i>Registrarse
                            </button>
                        </form>
                        
                        <div class="login-link">
                            <a href="/">¿Ya tienes cuenta? Inicia sesión aquí</a>
                        </div>
                        
                        <div id="alertContainer"></div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        document.getElementById('registerForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const data = Object.fromEntries(formData);
            
            try {
                const response = await fetch('/api/register', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                if (result.success) {
                    showAlert(result.message, 'success');
                    setTimeout(() => {
                        window.location.href = '/';
                    }, 2000);
                } else {
                    showAlert(result.message, 'danger');
                }
            } catch (error) {
                showAlert('Error de conexión. Intenta nuevamente.', 'danger');
            }
        });
        
        function showAlert(message, type) {
            const alertContainer = document.getElementById('alertContainer');
            alertContainer.innerHTML = `
                <div class="alert alert-${type} alert-dismissible fade show" role="alert">
                    ${message}
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                </div>
            `;
        }
    </script>
</body>
</html>
'''

@app.route('/')
def login_page():
    """Página de inicio de sesión"""
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/register')
def register_page():
    """Página de registro"""
    return render_template_string(REGISTER_TEMPLATE)

@app.route('/frontendUsuario.html')
def serve_frontend_usuario():
    """Servir el dashboard del usuario"""
    try:
        return send_file(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'frontendUsuario.html'))
    except Exception:
        # Fallback si falla la ruta relativa
        return send_file(os.path.abspath(os.path.join(os.getcwd(), '..', '..', 'frontendUsuario.html')))

@app.route('/api/login', methods=['POST'])
def login():
    """Endpoint para autenticación de usuarios"""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({
                "success": False,
                "message": "Email y contraseña son requeridos"
            }), 400
        
        user = auth_service.verify_user(email, password)
        
        if user:
            # Redirección sugerida para front: si es admin, abrir admin UI
            redirect_url = None
            if str(user.get('rol_account','')).lower() in ['admin','administrador']:
                redirect_url = 'http://localhost:5004/'
            else:
                redirect_url = 'http://localhost:5003/frontendUsuario.html'
            return jsonify({
                "success": True,
                "message": "Autenticación exitosa",
                "user": user,
                "redirect": redirect_url
            }), 200
        else:
            return jsonify({
                "success": False,
                "message": "Credenciales inválidas"
            }), 401
            
    except Exception as e:
        logger.error(f"❌ Error en login: {e}")
        return jsonify({
            "success": False,
            "message": "Error interno del servidor"
        }), 500

@app.route('/api/register', methods=['POST'])
def register():
    """Endpoint para registro de usuarios"""
    try:
        data = request.get_json()
        
        # Validar campos requeridos
        required_fields = ['name', 'email', 'password', 'date_of_birth', 'gender']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    "success": False,
                    "message": f"El campo {field} es requerido"
                }), 400
        
        success, message = auth_service.register_user(data)
        
        return jsonify({
            "success": success,
            "message": message
        }), 200 if success else 400
            
    except Exception as e:
        logger.error(f"❌ Error en registro: {e}")
        return jsonify({
            "success": False,
            "message": "Error interno del servidor"
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint de salud del microservicio"""
    return jsonify({
        "status": "healthy",
        "service": "InicioSesion",
        "timestamp": datetime.datetime.now().isoformat()
    })

if __name__ == '__main__':
    logger.info("🚀 Iniciando microservicio InicioSesion...")
    logger.info("📡 Endpoints disponibles:")
    logger.info("  GET / - Página de inicio de sesión")
    logger.info("  GET /register - Página de registro")
    logger.info("  POST /api/login - Autenticación")
    logger.info("  POST /api/register - Registro de usuarios")
    logger.info("  GET /health - Estado del servicio")
    
    app.run(host='0.0.0.0', port=5003, debug=True)
