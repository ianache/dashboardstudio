-- ============================================================
-- Modelo Dimensional: Concesionarias
-- Modelo Dimensional para Concesionarias
-- Generado: 2026-03-28T08:11:39.205Z
-- ============================================================

-- ------------------------------------------------------------
-- TABLAS DE DIMENSIONES
-- ------------------------------------------------------------

CREATE TABLE dim_concesionarias (
    id                             UUID PRIMARY KEY,
    nombre                         VARCHAR(20),
    razonsocial                    VARCHAR(255)
);

CREATE TABLE dim_tiendas (
    id                             SERIAL PRIMARY KEY,
    nombre                         VARCHAR(50),
    distrito                       VARCHAR(50),
    provincia                      VARCHAR(50),
    departamento                   VARCHAR(50),
    direccion                      VARCHAR(255)
);

CREATE TABLE dim_vendedores (
    id                             INTEGER PRIMARY KEY,
    nombre                         VARCHAR(50)
);

-- ------------------------------------------------------------
-- TABLAS DE HECHOS
-- ------------------------------------------------------------

CREATE TABLE fct_ventas (
    precio_venta                   NUMERIC(18,2),
    comision_vendedor              INTEGER,
    id                             UUID,
    dim_concesionarias_id          UUID,  -- FK → dim_concesionarias.id
    dim_tiendas_id                 INTEGER,  -- FK → dim_tiendas.id
    dim_vendedores_id              INTEGER,  -- FK → dim_vendedores.id
    CONSTRAINT fk_fct_ventas_dim_concesionarias_id FOREIGN KEY (dim_concesionarias_id) REFERENCES dim_concesionarias(id),
    CONSTRAINT fk_fct_ventas_dim_tiendas_id FOREIGN KEY (dim_tiendas_id) REFERENCES dim_tiendas(id),
    CONSTRAINT fk_fct_ventas_dim_vendedores_id FOREIGN KEY (dim_vendedores_id) REFERENCES dim_vendedores(id)
);

CREATE TABLE fact_cierre_mes (
    id                             UUID PRIMARY KEY,
    cuota_unidades                 INTEGER,
    monto_premio_meta              NUMERIC(18,2),
    bono_tienda                    NUMERIC(18,2)
);
