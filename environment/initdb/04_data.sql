\connect analytics

-- Activar el search_path para el resto del script
SET search_path TO analytics;

INSERT INTO dim_tiempo
SELECT
    datum AS id_fecha,
    EXTRACT(YEAR FROM datum) AS anio,
    EXTRACT(MONTH FROM datum) AS mes,
    TO_CHAR(datum, 'TMMonth') AS nombre_mes,
    EXTRACT(DAY FROM datum) AS dia,
    EXTRACT(ISODOW FROM datum) AS dia_semana,
    TO_CHAR(datum, 'TMDay') AS nombre_dia,
    EXTRACT(QUARTER FROM datum) AS trimestre,
    EXTRACT(WEEK FROM datum) AS semana_anio,
    CASE WHEN EXTRACT(ISODOW FROM datum) IN (6, 7) THEN TRUE ELSE FALSE END AS es_fin_semana,
    FALSE AS es_feriado,
    (date_trunc('MONTH', datum) + INTERVAL '1 MONTH - 1 day')::DATE AS ultimo_dia_mes,
    'regular' as temporada_comercial
FROM generate_series('2010-01-01'::DATE, '2030-12-31'::DATE, '1 day'::INTERVAL) datum;
