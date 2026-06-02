-- ============================================================
-- Modelo Dimensional: Gestion de Proyectos
-- Modelo Dimensional para Gestion de Proyectos
-- Generado: 2026-06-02T00:08:43.628Z
-- ============================================================

-- ------------------------------------------------------------
-- TABLAS DE DIMENSIONES
-- ------------------------------------------------------------

CREATE TABLE dim_tiempo (
    anio                           INTEGER,
    mes                            INTEGER,
    nombre_mes                     DT-1HZL3EODL,
    dia                            INTEGER,
    dia_semana                     DT-1HZL3EODL,
    nombre_dia                     DT-1HZL3EODL,
    trimestre                      INTEGER,
    semana_anio                    DT-1HZL3EODL,
    es_feriado                     BOOLEAN,
    temporada_comercial            DT-CP3YHL9GC,
    id_fecha                       DATE PRIMARY KEY
);

CREATE TABLE dim_colaborador (
    usuario                        VARCHAR(255) PRIMARY KEY,
    nombre                         VARCHAR(255),
    role                           TEXT,
    duracion_jornada               NUMERIC(18,4)
);

CREATE TABLE dim_producto_software (
    product                        VARCHAR(255) PRIMARY KEY,
    nombre                         VARCHAR(255)
);

CREATE TABLE dim_proyecto (
    id                             VARCHAR(255) PRIMARY KEY,
    nombre                         VARCHAR(255)
);

CREATE TABLE dim_tarea (
    tarea_id                       INTEGER PRIMARY KEY,  -- Identificador unico global de la tarea en GitLab
    nombre                         VARCHAR(255),  -- Titulo de la tarea
    estimacion                     NUMERIC(18,4),  -- Esfuerzo estimado en horas personas
    project_id                     INTEGER
);

CREATE TABLE dim_userstory (
    userstory_id                   DT-1HZL3EODL PRIMARY KEY,
    nombre                         VARCHAR(255)
);

CREATE TABLE dim_milestone (
    milestone_id                   SERIAL PRIMARY KEY,  -- Identificador único del hito.
    proyecto_id                    UUID,  -- Clave foránea a dim_proyecto.
    nombre                         VARCHAR(255),  -- Nombre del hito.
    descripcion                    TEXT,  -- Descripción detallada del hito.
    fecha_inicio_estimada          DATE,  -- Fecha estimada de inicio del hito.
    fecha_fin_estimada             DATE,  -- Fecha estimada de fin del hito.
    fecha_inicio_real              DATE,  -- Fecha real de inicio del hito.
    fecha_fin_real                 DATE,  -- Fecha real de fin del hito.
    estado                         DT-CP3YHL9GC,  -- Estado actual del hito (ej: Pendiente, En Progreso, Completado, Cancelado).
    creado_en                      TIMESTAMPTZ,  -- Timestamp de creación del registro.
    actualizado_en                 TIMESTAMPTZ  -- Timestamp de la última actualización del registro.
);

CREATE TABLE dim_sprint (
    sprint_id                      SERIAL PRIMARY KEY,  -- Identificador único del sprint.
    proyecto_id                    BIGINT,  -- Clave foránea a dim_proyecto.
    nombre                         VARCHAR(255),  -- Nombre descriptivo del sprint.
    fecha_inicio                   DATE,  -- Fecha de inicio del sprint.
    fecha_fin                      DATE,  -- Fecha de fin del sprint.
    estado                         VARCHAR(255)  -- Estado actual del sprint (e.g., 'Planificado', 'En Progreso', 'Completado').
);

-- ------------------------------------------------------------
-- TABLAS DE HECHOS
-- ------------------------------------------------------------

CREATE TABLE fct_horasreportadas (
    horas                          NUMERIC(18,4),
    product                        VARCHAR(255),  -- FK → dim_producto.id
    tarea_id                       INTEGER,  -- FK → dim_tarea.id
    userstory_id                   INTEGER,  -- FK → dim_userstory.id
    costo                          NUMERIC(18,2),
    guid                           UUID PRIMARY KEY,
    tiempo_id_fecha                DATE,  -- FK → dim_tiempo.id_fecha
    proyecto_id                    INTEGER,  -- FK → dim_proyecto.id
    reporter                       VARCHAR(255),  -- FK → dim_colaborador.usuario
    milestone_milestone_id         INTEGER,  -- FK → dim_milestone.milestone_id
    CONSTRAINT fk_fct_horasreportadas_tarea_id FOREIGN KEY (tarea_id) REFERENCES dim_tarea(id),
    CONSTRAINT fk_fct_horasreportadas_userstory_id FOREIGN KEY (userstory_id) REFERENCES dim_userstory(id),
    CONSTRAINT fk_fct_horasreportadas_tiempo_id_fecha FOREIGN KEY (tiempo_id_fecha) REFERENCES dim_tiempo(id_fecha),
    CONSTRAINT fk_fct_horasreportadas_proyecto_id FOREIGN KEY (proyecto_id) REFERENCES dim_proyecto(id),
    CONSTRAINT fk_fct_horasreportadas_reporter FOREIGN KEY (reporter) REFERENCES dim_colaborador(usuario),
    CONSTRAINT fk_fct_horasreportadas_milestone_milestone_id FOREIGN KEY (milestone_milestone_id) REFERENCES dim_milestone(milestone_id)
);

CREATE TABLE fct_asignaciontareas (
    id_asignacion                  UUID PRIMARY KEY,
    horas_restantes                INTEGER,
    horas_estimadas                INTEGER,
    horas_ejecutadas               INTEGER,
    condicion                      VARCHAR(255),
    tarea_id                       INTEGER,  -- FK → dim_tarea.id
    producto_id                    VARCHAR(255),  -- FK → dim_producto.id
    usuario                        VARCHAR(255),  -- FK → dim_colaborador.usuario
    proyecto_id                    INTEGER,  -- FK → dim_proyecto.id
    tiempo_id_fecha                DATE,  -- FK → dim_tiempo.id_fecha
    sprint_id                      INTEGER,  -- FK → dim_sprint.sprint_id
    CONSTRAINT fk_fct_asignaciontareas_tarea_id FOREIGN KEY (tarea_id) REFERENCES dim_tarea(id),
    CONSTRAINT fk_fct_asignaciontareas_usuario FOREIGN KEY (usuario) REFERENCES dim_colaborador(usuario),
    CONSTRAINT fk_fct_asignaciontareas_proyecto_id FOREIGN KEY (proyecto_id) REFERENCES dim_proyecto(id),
    CONSTRAINT fk_fct_asignaciontareas_tiempo_id_fecha FOREIGN KEY (tiempo_id_fecha) REFERENCES dim_tiempo(id_fecha),
    CONSTRAINT fk_fct_asignaciontareas_sprint_id FOREIGN KEY (sprint_id) REFERENCES dim_sprint(sprint_id)
);

CREATE TABLE fct_tareas_por_sprint (
    tarea_sprint_id                SERIAL PRIMARY KEY,
    sprint_id                      BIGINT,  -- Clave foránea a dim_sprint.
    proyecto_id                    BIGINT,  -- Clave foránea a dim_proyecto.
    colaborador_id                 BIGINT,  -- Clave foránea a dim_colaborador (si aplica a la asignación).
    userstory_id                   BIGINT,  -- Clave foránea a dim_userstory (si la tarea pertenece a una user story).
    puntos_estimados               NUMERIC(18,4),  -- Puntos de historia estimados para la tarea dentro del sprint.
    puntos_completados             NUMERIC(18,4),  -- Puntos de historia completados para la tarea dentro del sprint.
    fecha_asignacion               DATE,  -- Fecha en la que la tarea fue asignada al sprint.
    tiempo_estimado_horas          NUMERIC(18,4),  -- Tiempo estimado en horas para completar la tarea en el sprint.
    tiempo_realizado_horas         NUMERIC(18,4),  -- Tiempo real en horas invertido en la tarea dentro del sprint.
    tarea_id                       INTEGER,  -- FK → dim_tarea.id
    CONSTRAINT fk_fct_tareas_por_sprint_tarea_id FOREIGN KEY (tarea_id) REFERENCES dim_tarea(id)
);
