---
name: Tarea pendiente - Monedas en Configurar Métrica
description: Implementar selector de moneda en ChartConfigModal cuando Formato = Moneda
type: project
---

## Tarea: Monedas en "Configurar Métrica" - COMPLETADO ✅

**Why:** El usuario quiere que al seleccionar Formato "Moneda" en una medida del widget, aparezca un selector de moneda definida en BD.

**Estado:** FINALIZADO.

### Resumen de la implementación

1. **Backend:** Implementado modelo `Currency`, esquema y endpoint `/api/v1/currencies/`. Seed automático con USD y PEN.
2. **Frontend Service & Store:** Implementado `currenciesApi` y `useCurrencyStore` para cargar monedas desde el backend.
3. **Unificación de Formatos:** Se unificaron las claves de formato en todo el proyecto a inglés para evitar inconsistencias entre componentes:
   - `number` (antes `numero`)
   - `currency` (antes `moneda`)
   - `percent` (antes `porcentaje`)
4. **ChartConfigModal.vue:** Actualizado para incluir selector de Formato y Moneda por cada medida.
5. **KpiWidget.vue:** Actualizado para soportar los nuevos formatos y mostrar el símbolo de moneda dinámicamente.
6. **EChartWrapper.vue:** Confirmado soporte para formatos `number`, `currency` y `percent`.
7. **VisualizationConfiguratorView.vue:** Confirmada consistencia con las claves en inglés.
8. **Documentación:** Actualizado `dashboard-app/docs/widget_doc.md` con los nuevos valores de formato.

### Notas técnicas
- Se realizó un backfill reactivo en `ChartConfigModal.vue` para asegurar que widgets antiguos obtengan los nuevos campos `format` y `currencyId`.
- El formateo de números en el frontend utiliza `Intl.NumberFormat` con el locale 'es' para asegurar separadores de miles y decimales correctos.

**Fecha de cierre:** 2026-05-14
