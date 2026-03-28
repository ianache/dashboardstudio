-- ============================================================
-- Modelo Dimensional: Global
-- Generado: 2026-03-28T18:12:50.168Z
-- ============================================================

-- ------------------------------------------------------------
-- TABLAS DE DIMENSIONES
-- ------------------------------------------------------------

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
