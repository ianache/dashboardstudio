-- ============================================================
-- Modelo Dimensional: Concesionarias
-- Modelo Dimensional para Concesionarias
-- Generado: 2026-03-28T18:57:48.056Z
-- ============================================================

-- ------------------------------------------------------------
-- TABLAS DE DIMENSIONES
-- ------------------------------------------------------------

CREATE TABLE dim_tiendas (
    id                             SERIAL PRIMARY KEY,
    nombre                         VARCHAR(50),
    distrito                       VARCHAR(50),
    provincia                      VARCHAR(50),
    departamento                   VARCHAR(50),
    direccion                      VARCHAR(255)
);

CREATE TABLE dim_date (
    date_key                       DATE PRIMARY KEY,  -- Identificacion de la fecha
    day_of_week                    INTEGER,  -- Dia de la semana (numero 0 a 6)
    week_number                    INTEGER,  -- Numero de la semana en el año
    month                          VARCHAR(255),  -- Nombre dle mes
    quarter                        INTEGER,  -- Numero del cuarto
    fiscal_year                    NUMERIC(18,4),  -- año de la fecha
    is_weekend                     BOOLEAN,  -- Define si es fin de semana
    is_holiday                     BOOLEAN,  -- Define si es fecha feriada o no laborable
    is_business_day                BOOLEAN  -- Define si es dia laborable
);

CREATE TABLE dim_person (
    id                             SERIAL PRIMARY KEY,
    fullname                       VARCHAR(50),
    docid                          VARCHAR(20)
);

CREATE TABLE dim_company (
    id                             INTEGER PRIMARY KEY,  -- ID interno
    businessname                   VARCHAR(20),  -- Razon Social
    comercialname                  VARCHAR(50),  -- Nombre comercial
    taxnumber                      VARCHAR(20)  -- Codigo de registro tributario
);

-- ------------------------------------------------------------
-- TABLAS DE HECHOS
-- ------------------------------------------------------------

CREATE TABLE fct_ventas (
    precio_venta                   NUMERIC(18,2),
    comision_vendedor              INTEGER,
    id                             UUID,
    tiendas_id                     INTEGER,  -- FK → dim_tiendas.id
    date_date_key                  INTEGER,  -- FK → dim_date.date_key
    person_id                      INTEGER,  -- FK → dim_person.id
    company_id                     INTEGER,  -- FK → dim_company.id
    CONSTRAINT fk_fct_ventas_tiendas_id FOREIGN KEY (tiendas_id) REFERENCES dim_tiendas(id),
    CONSTRAINT fk_fct_ventas_date_date_key FOREIGN KEY (date_date_key) REFERENCES dim_date(date_key),
    CONSTRAINT fk_fct_ventas_person_id FOREIGN KEY (person_id) REFERENCES dim_person(id),
    CONSTRAINT fk_fct_ventas_company_id FOREIGN KEY (company_id) REFERENCES dim_company(id)
);

CREATE TABLE fact_cierre_mes (
    id                             UUID PRIMARY KEY,
    cuota_unidades                 INTEGER,
    monto_premio_meta              NUMERIC(18,2),
    bono_tienda                    NUMERIC(18,2),
    dim_date_date_key              INTEGER,  -- FK → dim_date.date_key
    CONSTRAINT fk_fact_cierre_mes_dim_date_date_key FOREIGN KEY (dim_date_date_key) REFERENCES dim_date(date_key)
);
