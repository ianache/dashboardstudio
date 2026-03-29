// ============================================================
// CubeJS Schema: Concesionarias
// Modelo Dimensional para Concesionarias
// Generado: 2026-03-28T07:49:46.540Z
// ============================================================

// ------------------------------------------------------------
// DIMENSIONES
// ------------------------------------------------------------

cube(`Concesionarias`, {
    sql_table: `dim_concesionarias`,

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
        razonsocial: {
            sql: `${CUBE}.razonsocial`,
            type: `string`,
        },
    },
});

cube(`Tiendas`, {
    sql_table: `dim_tiendas`,

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
        distrito: {
            sql: `${CUBE}.distrito`,
            type: `string`,
        },
        provincia: {
            sql: `${CUBE}.provincia`,
            type: `string`,
        },
        departamento: {
            sql: `${CUBE}.departamento`,
            type: `string`,
        },
        direccion: {
            sql: `${CUBE}.direccion`,
            type: `string`,
        },
    },
});

cube(`Vendedores`, {
    sql_table: `dim_vendedores`,

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
    },
});

// ------------------------------------------------------------
// HECHOS
// ------------------------------------------------------------

cube(`Ventas`, {
    sql_table: `fct_ventas`,

    joins: {
        Concesionarias: {
            sql: `${CUBE}.dim_concesionarias_id = ${Concesionarias}.id`,
            relationship: `many_to_one`,
        },
        Tiendas: {
            sql: `${CUBE}.dim_tiendas_id = ${Tiendas}.id`,
            relationship: `many_to_one`,
        },
        Vendedores: {
            sql: `${CUBE}.dim_vendedores_id = ${Vendedores}.id`,
            relationship: `many_to_one`,
        },
    },

    measures: {
        count: {
            type: `count`,
        },
        precioVenta: {
            sql: `${CUBE}.precio_venta`,
            type: `sum`,
        },
        comisionVendedor: {
            sql: `${CUBE}.comision_vendedor`,
            type: `sum`,
        },
        // Eliminé la medida 'id' porque ya tienes 'count' y evita confusión con la dimensión
    },

    dimensions: {
        id_venta: {
            sql: `${CUBE}.id`,
            type: `string`, // Cambiado a string porque en tu SQL es UUID
            primary_key: true,
        },
        // NO agregues aquí dimensiones que apunten a otros cubos
    },

    pre_aggregations: {
        main: {
            type: `rollup`,
            measures: [CUBE.count, CUBE.precioVenta, CUBE.comisionVendedor],
            dimensions: [
                Concesionarias.nombre,
                Tiendas.nombre,
                Vendedores.nombre
            ],
            refresh_key: {
                every: `1 hour`,
            },
        },
    },
});
