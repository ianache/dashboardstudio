\connect analytics

-- Activar el search_path para el resto del script
SET search_path TO analytics;

-- ─────────────────────────────────────────────
--  Tabla: dim_vendedores
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS dim_vendedores (
     id_vendedor INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
     nombre VARCHAR(100),
     nivel VARCHAR(20), -- Junior, Senior, Master
     sucursal_id INT
);
COMMENT ON TABLE  dim_vendedores                IS 'Tabla dimensional de vendedores';
COMMENT ON COLUMN dim_vendedores.id_vendedor IS 'ID autogenerado de la concesionaria';
COMMENT ON COLUMN dim_vendedores.nombre IS 'Nombre de la concesionaria';
COMMENT ON COLUMN dim_vendedores.nivel IS 'Nivel de experiencia del vendedor';
COMMENT ON COLUMN dim_vendedores.sucursal_id IS 'ID de la sucursal a la que pertenece el vendedor';

-- ─────────────────────────────────────────────
--  Tabla: dim_concesionarias
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS dim_concesionarias (
    id_concesionaria INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY, 
    nombre VARCHAR(20), 
    razon_social VARCHAR(100),
    ruc VARCHAR(12)
);
COMMENT ON TABLE  dim_concesionarias                    IS 'Tabla dimensional de concesionarias';
COMMENT ON COLUMN dim_concesionarias.id_concesionaria   IS 'ID autogenerado de la concesionaria';
COMMENT ON COLUMN dim_concesionarias.nombre             IS 'Nombre de la concesionaria';
COMMENT ON COLUMN dim_concesionarias.razon_social       IS 'Razon social de la concesionaria';
COMMENT ON COLUMN dim_concesionarias.ruc                IS 'RUC de la concesionaria';

-- ─────────────────────────────────────────────
--  Tabla: dim_sucursales
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS dim_sucursales (
    id_sucursal INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY, 
    nombre VARCHAR(20), 
    ciudad VARCHAR(50), -- Lima, Arequipa, Trujillo, Cusco
    region VARCHAR(20), -- Costa, Sierra, Selva
    direccion TEXT,
    id_concesionaria INT
);
ALTER TABLE dim_sucursales 
    ADD CONSTRAINT fk_sucursales_concesionarias FOREIGN KEY (id_concesionaria) 
    REFERENCES dim_concesionarias(id_concesionaria) ON DELETE CASCADE ON UPDATE CASCADE; 

-- ─────────────────────────────────────────────
--  Tabla: dim_vehiculos
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS dim_tiempo (
    id_fecha DATE PRIMARY KEY,
    anio INT,
    mes INT,
    nombre_mes VARCHAR(10),
    dia INT,
    dia_semana INT,
    nombre_dia VARCHAR(10),
    trimestre INT,
    semana_anio INT,
    es_fin_semana BOOLEAN,
    es_feriado BOOLEAN,
    ultimo_dia_mes DATE,
    temporada_comercial VARCHAR(50) -- 'Regular', 'Liquidación', 'Cierre de Año'
);
COMMENT ON TABLE  dim_tiempo                    IS 'Tabla dimensional de tiempo';
COMMENT ON COLUMN dim_tiempo.id_fecha           IS 'ID autogenerado de la fecha';
COMMENT ON COLUMN dim_tiempo.anio             IS 'Año de la fecha';
COMMENT ON COLUMN dim_tiempo.mes              IS 'Mes de la fecha';
COMMENT ON COLUMN dim_tiempo.nombre_mes       IS 'Nombre del mes';
COMMENT ON COLUMN dim_tiempo.dia              IS 'Día de la fecha';
COMMENT ON COLUMN dim_tiempo.dia_semana       IS 'Día de la semana';
COMMENT ON COLUMN dim_tiempo.nombre_dia       IS 'Nombre del día de la semana';
COMMENT ON COLUMN dim_tiempo.trimestre        IS 'Trimestre de la fecha';
COMMENT ON COLUMN dim_tiempo.semana_anio      IS 'Semana del año';
COMMENT ON COLUMN dim_tiempo.es_fin_semana    IS 'Indica si la fecha es fin de semana';
COMMENT ON COLUMN dim_tiempo.es_feriado       IS 'Indica si la fecha es feriado';
COMMENT ON COLUMN dim_tiempo.ultimo_dia_mes   IS 'Indica si la fecha es el último día del mes';
COMMENT ON COLUMN dim_tiempo.temporada_comercial IS 'Temporada comercial de la fecha'; 


-- ─────────────────────────────────────────────
--  Tabla: fact_ventas
COMMENT ON TABLE  dim_sucursales                IS 'Tabla dimensional de sucursales';
COMMENT ON COLUMN dim_sucursales.id_sucursal    IS 'ID autogenerado de la sucursal';
COMMENT ON COLUMN dim_sucursales.nombre         IS 'Nombre de la sucursal';
COMMENT ON COLUMN dim_sucursales.ciudad         IS 'Ciudad de la sucursal';
COMMENT ON COLUMN dim_sucursales.region         IS 'Region de la sucursal';
COMMENT ON COLUMN dim_sucursales.direccion      IS 'Direccion de la sucursal';
COMMENT ON COLUMN dim_sucursales.id_concesionaria IS 'ID de la concesionaria a la que pertenece la sucursal';   
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS fact_ventas (
    id_venta INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    fecha_venta DATE NOT NULL,
    fk_vendedor INT REFERENCES dim_vendedores(id_vendedor),
    fk_vehiculo INT REFERENCES dim_vehiculos(id_vehiculo),
    fk_tienda INT REFERENCES dim_concesionarias(id_concesionaria),
    
    -- Métricas financieras
    precio_venta NUMERIC(15, 2) NOT NULL,
    costo_unidad NUMERIC(15, 2),
    comision_vendedor NUMERIC(15, 2), -- Calculada al momento de la venta
    impuestos NUMERIC(15, 2)
);
COMMENT ON TABLE  fact_ventas                   IS 'Tabla de hechos de ventas';
COMMENT ON COLUMN fact_ventas.id_venta          IS 'ID autogenerado de la venta';
COMMENT ON COLUMN fact_ventas.fecha_venta       IS 'Fecha de la venta';
COMMENT ON COLUMN fact_ventas.fk_vendedor       IS 'ID del vendedor';
COMMENT ON COLUMN fact_ventas.fk_vehiculo       IS 'ID del vehiculo';
COMMENT ON COLUMN fact_ventas.fk_tienda         IS 'ID de la concesionaria';
COMMENT ON COLUMN fact_ventas.precio_venta      IS 'Precio de venta';
COMMENT ON COLUMN fact_ventas.costo_unidad      IS 'Costo de la unidad';
COMMENT ON COLUMN fact_ventas.comision_vendedor IS 'Comision del vendedor';
COMMENT ON COLUMN fact_ventas.impuestos         IS 'Impuestos';

CREATE TABLE IF NOT EXISTS fact_cierre_mes (
    id_cierre SERIAL PRIMARY KEY,
    mes_referencia DATE, -- Primer día del mes
    fk_vendedor INT REFERENCES dim_vendedores(id_vendedor),
    cuota_unidades INT,
    monto_premio_meta NUMERIC(15,2),
    bono_tienda NUMERIC(15,2)
);
COMMENT ON TABLE  fact_cierre_mes                   IS 'Tabla de hechos de cierre de mes';
COMMENT ON COLUMN fact_cierre_mes.id_cierre          IS 'ID autogenerado de la venta';
COMMENT ON COLUMN fact_cierre_mes.mes_referencia       IS 'Fecha de la venta';
COMMENT ON COLUMN fact_cierre_mes.fk_vendedor       IS 'ID del vendedor';
COMMENT ON COLUMN fact_cierre_mes.fk_vehiculo       IS 'ID del vehiculo';
COMMENT ON COLUMN fact_cierre_mes.fk_tienda         IS 'ID de la concesionaria';
COMMENT ON COLUMN fact_cierre_mes.precio_venta      IS 'Precio de venta';
COMMENT ON COLUMN fact_cierre_mes.costo_unidad      IS 'Costo de la unidad';
COMMENT ON COLUMN fact_cierre_mes.comision_vendedor IS 'Comision del vendedor';
COMMENT ON COLUMN fact_cierre_mes.impuestos         IS 'Impuestos';

CREATE TABLE IF NOT EXISTS dim_vehiculos (
    id_vehiculo INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    vin VARCHAR(17) UNIQUE NOT NULL, -- Número de chasis
    marca VARCHAR(20),
    modelo VARCHAR(20),
    tipo_vehiculo VARCHAR(20), -- SUV, Sedan, Pick-up
    estado_unidad VARCHAR(10), -- Nuevo, Usado
    anio_fabricacion INT
);
COMMENT ON TABLE  dim_vehiculos                   IS 'Tabla dimensional de vehiculos';
COMMENT ON COLUMN dim_vehiculos.id_vehiculo          IS 'ID autogenerado de la venta';

-- ─────────────────────────────────────────────
--  Tabla: fact_inventario
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS fact_inventario (
    id_inventario INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    fecha_inventario DATE NOT NULL,
    fk_vehiculo INT REFERENCES dim_vehiculos(id_vehiculo),
    fk_tienda INT REFERENCES dim_concesionarias(id_concesionaria),
    
    -- Métricas financieras
    precio_venta NUMERIC(15, 2) NOT NULL,
    costo_unidad NUMERIC(15, 2),
    comision_vendedor NUMERIC(15, 2), -- Calculada al momento de la venta
    impuestos NUMERIC(15, 2)
);