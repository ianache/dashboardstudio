-- ============================================================
-- Modelo Dimensional: Gestion de Proyectos
-- Modelo Dimensional para Gestion de Proyectos
-- Generado: 2026-03-28T07:29:21.897Z
-- ============================================================

-- ------------------------------------------------------------
-- TABLAS DE DIMENSIONES
-- ------------------------------------------------------------

CREATE TABLE dim_tiempo (
    anio                           INTEGER,
    mes                            INTEGER,
    nombre_mes                     VARCHAR(255),
    dia                            INTEGER,
    dia_semana                     VARCHAR(255),
    nombre_dia                     VARCHAR(255),
    trimestre                      INTEGER,
    semana_anio                    VARCHAR(255),
    es_feriado                     BOOLEAN,
    temporada_comercial            VARCHAR(50),
    id_fecha                       DATE PRIMARY KEY
);

CREATE TABLE dim_colaborador (
    usuario                        VARCHAR(20) PRIMARY KEY,
    nombre                         VARCHAR(50),
    role                           VARCHAR(255)
);

CREATE TABLE dim_producto (
    id                             VARCHAR(5) PRIMARY KEY,
    nombre                         VARCHAR(255)
);

CREATE TABLE dim_proyecto (
    id                             VARCHAR(5) PRIMARY KEY,
    nombre                         VARCHAR(255)
);

CREATE TABLE dim_tarea (
    id                             INTEGER PRIMARY KEY,
    nombre                         VARCHAR(255),
    estimacion                     NUMERIC(18,4)
);

CREATE TABLE dim_userstory (
    id                             VARCHAR(255) PRIMARY KEY,
    nombre                         VARCHAR(255)
);

-- ------------------------------------------------------------
-- TABLAS DE HECHOS
-- ------------------------------------------------------------

CREATE TABLE fct_horasreportadas (
    horas                          NUMERIC(18,4),
    dim_producto_id                VARCHAR(5),  -- FK → dim_producto.id
    dim_tarea_id                   INTEGER,  -- FK → dim_tarea.id
    dim_userstory_id               VARCHAR(255),  -- FK → dim_userstory.id
    costo                          NUMERIC(18,2),
    guid                           UUID,
    dim_tiempo_id_fecha            DATE,  -- FK → dim_tiempo.id_fecha
    dim_proyecto_id                VARCHAR(5),  -- FK → dim_proyecto.id
    dim_colaborador_usuario        VARCHAR(20),  -- FK → dim_colaborador.usuario
    CONSTRAINT fk_fct_horasreportadas_dim_producto_id FOREIGN KEY (dim_producto_id) REFERENCES dim_producto(id),
    CONSTRAINT fk_fct_horasreportadas_dim_tarea_id FOREIGN KEY (dim_tarea_id) REFERENCES dim_tarea(id),
    CONSTRAINT fk_fct_horasreportadas_dim_userstory_id FOREIGN KEY (dim_userstory_id) REFERENCES dim_userstory(id),
    CONSTRAINT fk_fct_horasreportadas_dim_tiempo_id_fecha FOREIGN KEY (dim_tiempo_id_fecha) REFERENCES dim_tiempo(id_fecha),
    CONSTRAINT fk_fct_horasreportadas_dim_proyecto_id FOREIGN KEY (dim_proyecto_id) REFERENCES dim_proyecto(id),
    CONSTRAINT fk_fct_horasreportadas_dim_colaborador_usuario FOREIGN KEY (dim_colaborador_usuario) REFERENCES dim_colaborador(usuario)
);
