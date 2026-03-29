// ============================================================
// CubeJS cube: Colaborador
// Tabla: dim_colaborador  |  Modelo: Gestion de Proyectos
// Generado: 2026-03-28T21:22:42.428Z
// ============================================================

cube(`Colaborador`, {
  sql_table: `dim_colaborador`,

  measures: {
    count: {
      type: `count`,
    },
  },

  dimensions: {
    usuario: {
      sql: `${CUBE}.usuario`,
      type: `string`,
      primary_key: true,
    },
    nombre: {
      sql: `${CUBE}.nombre`,
      type: `string`,
    },
    role: {
      sql: `${CUBE}.role`,
      type: `string`,
    },
  },
});