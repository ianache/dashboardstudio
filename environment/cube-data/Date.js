// ============================================================
// CubeJS cube: Date
// Tabla: dim_date  |  Modelo: Global
// Generado: 2026-03-28T18:12:36.812Z
// ============================================================

cube(`Date`, {
  sql_table: `dim_date`,

  measures: {
    count: {
      type: `count`,
    },
  },

  dimensions: {
    dateKey: {
      sql: `${CUBE}.date_key`,
      type: `time`,
      primary_key: true,
    },
    dayOfWeek: {
      sql: `${CUBE}.day_of_week`,
      type: `number`,
      title: `Dia de la semana (numero 0 a 6)`,
    },
    weekNumber: {
      sql: `${CUBE}.week_number`,
      type: `number`,
      title: `Numero de la semana en el año`,
    },
    month: {
      sql: `${CUBE}.month`,
      type: `string`,
      title: `Nombre dle mes`,
    },
    quarter: {
      sql: `${CUBE}.quarter`,
      type: `number`,
      title: `Numero del cuarto`,
    },
    fiscalYear: {
      sql: `${CUBE}.fiscal_year`,
      type: `number`,
      title: `año de la fecha`,
    },
    isWeekend: {
      sql: `${CUBE}.is_weekend`,
      type: `boolean`,
      title: `Define si es fin de semana`,
    },
    isHoliday: {
      sql: `${CUBE}.is_holiday`,
      type: `boolean`,
      title: `Define si es fecha feriada o no laborable`,
    },
    isBusinessDay: {
      sql: `${CUBE}.is_business_day`,
      type: `boolean`,
      title: `Define si es dia laborable`,
    },
  },
});