-- Archivo: init.sql
-- Crea las tablas y el esquema para la base de datos de PostgreSQL

-- Define el tipo ENUM para el género
CREATE TYPE gender_enum AS ENUM ('male', 'female', 'other');

-- Define el tipo ENUM para el rol de la cuenta
CREATE TYPE rol_enum AS ENUM ('patient', 'doctor', 'admin');

-- Tabla para almacenar la información de los usuarios (pacientes)
CREATE TABLE IF NOT EXISTS users (
    patient_id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255),
    date_of_birth DATE,
    gender gender_enum,
    email VARCHAR(255),
    password VARCHAR(255),
    medical_history TEXT,
    rol_account rol_enum
);

-- Inserta un paciente de ejemplo
INSERT INTO users (patient_id, name, date_of_birth, gender, email, password, medical_history, rol_account) VALUES
('20250831-5f21-4f32-8e12-28e441467a18', 'John Doe', '1980-01-01', 'male', 'john.doe@example.com', 'hashed_password', 'Hypertension', 'patient');