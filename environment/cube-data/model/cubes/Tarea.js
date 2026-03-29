// ============================================================
// CubeJS cube: Tarea
// Tabla: dim_tarea  |  Modelo: Gestion de Proyectos
// Generado: 2026-03-28T21:22:42.429Z
// ============================================================

cube(`Tarea`, {
  sql_table: `dim_tarea`,

  measures: {
    count: {
      type: `count`,
    },
  },

  dimensions: {
    id: {
      sql: `${CUBE}.id`,
      type: `number`,
      primary_key: true,
    },
    nombre: {
      sql: `${CUBE}.nombre`,
      type: `string`,
    },
    estimacion: {
      sql: `${CUBE}.estimacion`,
      type: `number`,
    },
  },
});