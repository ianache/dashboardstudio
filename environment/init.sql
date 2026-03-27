-- init.sql
-- Script de inicialización de PostgreSQL ejecutado al primer arranque

-- Tabla de ejemplo para probar CubeJS
CREATE TABLE IF NOT EXISTS orders (
    id          SERIAL PRIMARY KEY,
    status      VARCHAR(50) NOT NULL DEFAULT 'pending',
    amount      NUMERIC(12, 2) NOT NULL DEFAULT 0,
    created_at  TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Datos de prueba
INSERT INTO orders (status, amount, created_at) VALUES
    ('completed', 120.50, NOW() - INTERVAL '1 day'),
    ('completed', 340.00, NOW() - INTERVAL '2 days'),
    ('pending',    89.99, NOW() - INTERVAL '3 days'),
    ('cancelled',  55.00, NOW() - INTERVAL '4 days'),
    ('completed', 210.75, NOW() - INTERVAL '5 days');
