cube(`dim_tiempo`, {
    sql_table: `public.dim_tiempo`,

    data_source: `default`,

    joins: {

    },

    dimensions: {
        es_feriado: {
            sql: `es_feriado`,
            type: `boolean`
        },

        es_fin_semana: {
            sql: `es_fin_semana`,
            type: `boolean`
        },

        nombre_dia: {
            sql: `nombre_dia`,
            type: `string`
        },

        nombre_mes: {
            sql: `nombre_mes`,
            type: `string`
        },

        temporada_comercial: {
            sql: `temporada_comercial`,
            type: `string`
        },

        id_fecha: {
            sql: `id_fecha`,
            type: `time`
        },

        ultimo_dia_mes: {
            sql: `ultimo_dia_mes`,
            type: `time`
        }
    },

    measures: {
        count: {
            type: `count`
        }
    },

    pre_aggregations: {
        // Pre-aggregation definitions go here.
        // Learn more in the documentation: https://cube.dev/docs/caching/pre-aggregations/getting-started
    }
});
