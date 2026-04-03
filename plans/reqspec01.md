ReqSpec: Dynamic Drill-Down for DashboardStudio (Vue 3 + Cube.js)

1. Goal
Implementar un sistema de navegación descendente (Drill-Down) en los widgets de tipo gráfico. El sistema debe permitir definir una ruta de dimensiones en el diseñador y navegar por ellas en el tiempo de ejecución (Runtime) aplicando filtros acumulativos.
2. Modificaciones en el Store (Pinia)
Archivo objetivo: src/stores/widgetStore.ts (o similar)
 * Schema Update: Extender la interfaz WidgetConfig para soportar drillDownConfig.
   drillDownConfig: {
  active: boolean;
  hierarchy: string[]; // Array de dimensiones de Cube.js (ej: ['Tiendas.nombre', 'Categorias.nombre'])
  currentLevel: number; // Índice de la dimensión actual
  filters: Array<{ member: string, operator: 'equals', values: string[] }>; // Filtros acumulados durante el drill
}

 * Actions:
   * setDrillDown(widgetId, dimensionValue): Incrementa currentLevel, añade el valor clickeado a filters y dispara el refresh del widget.
   * resetDrillDown(widgetId): Limpia el nivel y los filtros.
   * goBackDrillDown(widgetId): Decrementa el nivel y elimina el último filtro de la pila.
3. UI: Modificación del Diseñador (El Modal de la imagen)
Archivo objetivo: src/components/designer/WidgetConfigModal.vue
 * Componente de Dimensiones: Reemplazar el input único de "Dimensiones" por un componente de lista dinámica (tipo Draggable o simplemente permitir añadir más de una).
 * Identificación visual: La primera dimensión de la lista es el "Nivel 0", la segunda el "Nivel 1", etc.
 * Sincronización con Cube Schema: Asegurarse de que cada dimensión agregada sea validada contra el CubeSchema (ya veo la pestaña "Esquema Cube" en tu captura).
4. Componente de Renderizado (ECharts)
Archivo objetivo: src/components/charts/ChartRenderer.vue
 * Event Listener: Configurar chartInstance.on('click', ...) solo si drillDownConfig.active es true.
 * Data Extraction: Extraer el valor del punto clickeado (params.name o params.data[dimIndex]).
 * Visual Feedback: Implementar un botón flotante de "Regresar" o un componente de Breadcrumbs simple que se muestre solo cuando currentLevel > 0.
5. Lógica del Adaptador Cube.js
Archivo objetivo: src/services/cubeAdapter.ts (o donde generes la query)
 * Query Mutation: La función que construye el objeto JSON para Cube.js debe:
   * Usar hierarchy[currentLevel] como la dimensión principal de la query.
   * Mergear los filters globales del dashboard con los filters locales del drillDownConfig.
   * Asegurar que el operador siempre sea equals para valores categóricos del drill.
Notas para el intercambio de "colegas" (Reflexiones Finales):
 * Manejo de Títulos: Sugiero que el título del gráfico sea dinámico. Si estoy en el nivel de "Tiendas" y hago drill en "Mitsui", el título debería cambiar a: Ventas por Categoría: Mitsui. Esto le da al usuario sentido de ubicación.
 * Breadcrumbs vs. Botón Volver: Para un diseñador BI, los breadcrumbs sobre el gráfico (ej: Todo > Mitsui > Aceites) son mucho más elegantes y permiten saltar dos niveles hacia arriba de un golpe.
 * Universal Transition: Como usas Apache ECharts, dile a ClaudeCode que use la propiedad universalTransition: true en la serie. Esto hará que cuando las barras cambien de "Tiendas" a "Categorías", se animen de forma fluida, lo que da una sensación de "profundizar" muy pro.