// ============================================================
// CubeJS cube: Tiempo
// Tabla: dim_tiempo  |  Modelo: Gestion de Proyectos
// Generado: 2026-03-28T21:22:42.427Z
// ============================================================

cube(`Tiempo`, {
  sql_table: `dim_tiempo`,

  measures: {
    count: {
      type: `count`,
    },
  },

  dimensions: {
    anio: {
      sql: `${CUBE}.anio`,
      type: `number`,
    },
    mes: {
      sql: `${CUBE}.mes`,
      type: `number`,
    },
    nombreMes: {
      sql: `${CUBE}.nombre_mes`,
      type: `string`,
    },
    dia: {
      sql: `${CUBE}.dia`,
      type: `number`,
    },
    diaSemana: {
      sql: `${CUBE}.dia_semana`,
      type: `string`,
    },
    nombreDia: {
      sql: `${CUBE}.nombre_dia`,
      type: `string`,
    },
    trimestre: {
      sql: `${CUBE}.trimestre`,
      type: `number`,
    },
    semanaAnio: {
      sql: `${CUBE}.semana_anio`,
      type: `string`,
    },
    esFeriado: {
      sql: `${CUBE}.es_feriado`,
      type: `boolean`,
    },
    temporadaComercial: {
      sql: `${CUBE}.temporada_comercial`,
      type: `string`,
    },
    idFecha: {
      sql: `${CUBE}.id_fecha`,
      type: `time`,
      primary_key: true,
    },
  },
});