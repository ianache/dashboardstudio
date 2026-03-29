cube(`Orders`, {
    sql: `SELECT * FROM orders`,

    // Pre-agregaciones cacheadas en Redis
    preAggregations: {
        ordersByDay: {
            measures: [Orders.count, Orders.totalAmount],
            dimensions: [Orders.status],
            timeDimension: Orders.createdAt,
            granularity: `day`,
            refreshKey: {
                every: `1 hour`,
            },
        },
    },

    measures: {
        count: {
            type: `count`,
        },
        totalAmount: {
            sql: `amount`,
            type: `sum`,
        },
    },

    dimensions: {
        id: {
            sql: `id`,
            type: `number`,
            primaryKey: true,
        },
        status: {
            sql: `status`,
            type: `string`,
        },
        createdAt: {
            s
      sql: `created_at`,
            type: `time`,
        },
    },
});
