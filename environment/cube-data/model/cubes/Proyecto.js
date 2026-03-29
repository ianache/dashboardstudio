// ============================================================
// CubeJS cube: Proyecto
// Tabla: dim_proyecto  |  Modelo: Gestion de Proyectos
// Generado: 2026-03-28T21:22:42.429Z
// ============================================================

cube(`Proyecto`, {
  sql_table: `dim_proyecto`,

  measures: {
    count: {
      type: `count`,
    },
  },

  dimensions: {
    id: {
      sql: `${CUBE}.id`,
      type: `string`,
      primary_key: true,
    },
    nombre: {
      sql: `${CUBE}.nombre`,
      type: `string`,
    },
  },
});