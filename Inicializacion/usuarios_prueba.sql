-- Script para insertar usuarios de prueba en la base de datos
-- Ejecutar después de que la base de datos esté inicializada

-- Insertar usuario Juan para pruebas
INSERT INTO users (patient_id, name, date_of_birth, gender, email, password, medical_history, rol_account) VALUES
('juan-test-123', 'Juan Pérez', '1990-05-15', 'male', 'juan@test.com', 'juan123', 'Sin condiciones médicas conocidas', 'patient')
ON CONFLICT (patient_id) DO NOTHING;

-- Insertar usuario María para pruebas
INSERT INTO users (patient_id, name, date_of_birth, gender, email, password, medical_history, rol_account) VALUES
('maria-test-456', 'María García', '1985-08-22', 'female', 'maria@test.com', 'maria123', 'Alergia a penicilina', 'patient')
ON CONFLICT (patient_id) DO NOTHING;

-- Insertar usuario Admin para pruebas
INSERT INTO users (patient_id, name, date_of_birth, gender, email, password, medical_history, rol_account) VALUES
('admin-test-789', 'Admin Test', '1980-01-01', 'male', 'admin@test.com', 'admin123', 'Sin condiciones médicas', 'admin')
ON CONFLICT (patient_id) DO NOTHING;

-- Verificar usuarios insertados
SELECT patient_id, name, email, rol_account FROM users ORDER BY name;
