// ============================================================
// CubeJS cube: Horasreportadas
// Tabla: fct_horasreportadas  |  Modelo: Gestion de Proyectos
// Generado: 2026-03-28T21:22:42.428Z
// ============================================================

cube(`Horasreportadas`, {
  sql_table: `fct_horasreportadas`,

  joins: {
    Producto: {
      sql: `${CUBE}.dim_producto_id = ${Producto}.id`,
      relationship: `many_to_one`,
    },
    Tarea: {
      sql: `${CUBE}.dim_tarea_id = ${Tarea}.id`,
      relationship: `many_to_one`,
    },
    Userstory: {
      sql: `${CUBE}.dim_userstory_id = ${Userstory}.id`,
      relationship: `many_to_one`,
    },
    Tiempo: {
      sql: `${CUBE}.dim_tiempo_id_fecha = ${Tiempo}.id_fecha`,
      relationship: `many_to_one`,
    },
    Proyecto: {
      sql: `${CUBE}.dim_proyecto_id = ${Proyecto}.id`,
      relationship: `many_to_one`,
    },
    Colaborador: {
      sql: `${CUBE}.dim_colaborador_usuario = ${Colaborador}.usuario`,
      relationship: `many_to_one`,
    },
  },

  measures: {
    count: {
      type: `count`,
    },
    horas: {
      sql: `${CUBE}.horas`,
      type: `sum`,
    },
    costo: {
      sql: `${CUBE}.costo`,
      type: `sum`,
    },
  },

  dimensions: {
    dimProductoId: {
      sql: `${CUBE}.dim_producto_id`,
      type: `string`,
    },
    dimTareaId: {
      sql: `${CUBE}.dim_tarea_id`,
      type: `number`,
    },
    dimUserstoryId: {
      sql: `${CUBE}.dim_userstory_id`,
      type: `string`,
    },
    guid: {
      sql: `${CUBE}.guid`,
      type: `string`,
      primary_key: true,
    },
    dimTiempoIdFecha: {
      sql: `${CUBE}.dim_tiempo_id_fecha`,
      type: `time`,
    },
    dimProyectoId: {
      sql: `${CUBE}.dim_proyecto_id`,
      type: `string`,
    },
    dimColaboradorUsuario: {
      sql: `${CUBE}.dim_colaborador_usuario`,
      type: `string`,
    },
  },

  pre_aggregations: {
    main: {
      type: `rollup`,
      measures: [CUBE.count, CUBE.horas, CUBE.costo],
      refresh_key: {
        every: `1 hour`,
      },
    },
  },
});