// ============================================================
// CubeJS cube: Asignaciontareas
// Tabla: fct_asignaciontareas  |  Modelo: Gestion de Proyectos
// Generado: 2026-03-28T21:22:42.429Z
// ============================================================

cube(`Asignaciontareas`, {
  sql_table: `fct_asignaciontareas`,

  joins: {
    Tarea: {
      sql: `${CUBE}.dim_tarea_id = ${Tarea}.id`,
      relationship: `many_to_one`,
    },
    Producto: {
      sql: `${CUBE}.dim_producto_id = ${Producto}.id`,
      relationship: `many_to_one`,
    },
    Colaborador: {
      sql: `${CUBE}.dim_colaborador_usuario = ${Colaborador}.usuario`,
      relationship: `many_to_one`,
    },
    Proyecto: {
      sql: `${CUBE}.dim_proyecto_id = ${Proyecto}.id`,
      relationship: `many_to_one`,
    },
    Tiempo: {
      sql: `${CUBE}.dim_tiempo_id_fecha = ${Tiempo}.id_fecha`,
      relationship: `many_to_one`,
    },
  },

  measures: {
    count: {
      type: `count`,
    },
    horasRestantes: {
      sql: `${CUBE}.horas_restantes`,
      type: `sum`,
    },
    horasEstimadas: {
      sql: `${CUBE}.horas_estimadas`,
      type: `sum`,
    },
    horasEjecutadas: {
      sql: `${CUBE}.horas_ejecutadas`,
      type: `sum`,
    },
    condicion: {
      sql: `${CUBE}.condicion`,
      type: `count`,
    },
  },

  dimensions: {
    nuevoCampo: {
      sql: `${CUBE}.nuevo_campo`,
      type: `string`,
      primary_key: true,
    },
    dimTareaId: {
      sql: `${CUBE}.dim_tarea_id`,
      type: `number`,
    },
    dimProductoId: {
      sql: `${CUBE}.dim_producto_id`,
      type: `string`,
    },
    dimColaboradorUsuario: {
      sql: `${CUBE}.dim_colaborador_usuario`,
      type: `string`,
    },
    dimProyectoId: {
      sql: `${CUBE}.dim_proyecto_id`,
      type: `string`,
    },
    dimTiempoIdFecha: {
      sql: `${CUBE}.dim_tiempo_id_fecha`,
      type: `time`,
    },
  },

  pre_aggregations: {
    main: {
      type: `rollup`,
      measures: [CUBE.count, CUBE.horasRestantes, CUBE.horasEstimadas, CUBE.horasEjecutadas, CUBE.condicion],
      refresh_key: {
        every: `1 hour`,
      },
    },
  },
});