-- =============================================================
--  02_analytics.sql
--  Configura el schema analítico en la base "analytics"
--  y carga datos de ejemplo para CubeJS.
-- =============================================================

\connect analytics

-- ─────────────────────────────────────────────
--  Schema dedicado para los datos analíticos
-- ─────────────────────────────────────────────
CREATE SCHEMA IF NOT EXISTS analytics AUTHORIZATION cubeuser;

GRANT ALL PRIVILEGES ON SCHEMA analytics TO cubeuser;

-- cubeuser siempre busca primero en el schema analytics
ALTER ROLE cubeuser SET search_path TO analytics, public;

COMMENT ON SCHEMA analytics IS 'Datos analíticos expuestos por CubeJS';

-- Activar el search_path para el resto del script
SET search_path TO analytics;

-- ─────────────────────────────────────────────
--  Tabla: orders
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS orders (
    id             SERIAL PRIMARY KEY,
    tenant_id      VARCHAR(50)    NOT NULL DEFAULT 'tenant_a',
    owner_id       VARCHAR(50)    NOT NULL,
    region         VARCHAR(50)    NOT NULL,
    status         VARCHAR(50)    NOT NULL DEFAULT 'pending',
    amount         NUMERIC(12, 2) NOT NULL DEFAULT 0,
    customer_email TEXT,
    created_at     TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE  orders                IS 'Órdenes de venta — fuente principal para CubeJS';
COMMENT ON COLUMN orders.tenant_id      IS 'Identificador de organización (multi-tenant)';
COMMENT ON COLUMN orders.owner_id       IS 'ID del vendedor responsable';
COMMENT ON COLUMN orders.region         IS 'Región geográfica: LATAM, NA, EU, APAC';
COMMENT ON COLUMN orders.customer_email IS 'Dato sensible — solo visible para rol admin';

-- Índices para filtros frecuentes de CubeJS
CREATE INDEX IF NOT EXISTS idx_orders_tenant    ON orders (tenant_id);
CREATE INDEX IF NOT EXISTS idx_orders_owner     ON orders (owner_id);
CREATE INDEX IF NOT EXISTS idx_orders_region    ON orders (region);
CREATE INDEX IF NOT EXISTS idx_orders_status    ON orders (status);
CREATE INDEX IF NOT EXISTS idx_orders_created   ON orders (created_at DESC);

-- ─────────────────────────────────────────────
--  Datos de ejemplo
-- ─────────────────────────────────────────────
INSERT INTO orders (tenant_id, owner_id, region, status, amount, customer_email, created_at) VALUES
    ('tenant_a', 'u001', 'LATAM', 'completed', 120.50, 'cliente1@ejemplo.com', NOW() - INTERVAL  '1 day'),
    ('tenant_a', 'u003', 'LATAM', 'completed', 340.00, 'cliente2@ejemplo.com', NOW() - INTERVAL  '2 days'),
    ('tenant_a', 'u003', 'LATAM', 'pending',    89.99, 'cliente3@ejemplo.com', NOW() - INTERVAL  '3 days'),
    ('tenant_a', 'u001', 'NA',    'cancelled',  55.00, 'cliente4@ejemplo.com', NOW() - INTERVAL  '4 days'),
    ('tenant_b', 'u005', 'EU',    'completed', 210.75, 'cliente5@ejemplo.com', NOW() - INTERVAL  '5 days'),
    ('tenant_a', 'u003', 'LATAM', 'completed', 450.00, 'cliente6@ejemplo.com', NOW() - INTERVAL  '6 days'),
    ('tenant_b', 'u005', 'EU',    'pending',   180.25, 'cliente7@ejemplo.com', NOW() - INTERVAL  '7 days'),
    ('tenant_a', 'u001', 'NA',    'completed', 320.00, 'cliente8@ejemplo.com', NOW() - INTERVAL  '8 days'),
    ('tenant_a', 'u003', 'LATAM', 'completed',  75.50, 'cliente9@ejemplo.com', NOW() - INTERVAL  '9 days'),
    ('tenant_b', 'u005', 'APAC',  'cancelled', 290.00, 'cliente10@ejemplo.com',NOW() - INTERVAL '10 days');

-- ─────────────────────────────────────────────
--  Tabla: products (ejemplo adicional)
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS products (
    id         SERIAL PRIMARY KEY,
    tenant_id  VARCHAR(50) NOT NULL DEFAULT 'tenant_a',
    name       VARCHAR(200) NOT NULL,
    category   VARCHAR(100),
    price      NUMERIC(10, 2) NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE products IS 'Catálogo de productos por tenant';

CREATE INDEX IF NOT EXISTS idx_products_tenant   ON products (tenant_id);
CREATE INDEX IF NOT EXISTS idx_products_category ON products (category);

INSERT INTO products (tenant_id, name, category, price) VALUES
    ('tenant_a', 'Producto Alpha',  'Software',  99.00),
    ('tenant_a', 'Producto Beta',   'Hardware',  249.99),
    ('tenant_a', 'Producto Gamma',  'Software',  49.00),
    ('tenant_b', 'Producto Delta',  'Servicios', 500.00),
    ('tenant_b', 'Producto Epsilon','Hardware',  175.50);
