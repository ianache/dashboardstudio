ReqSpec: State Management for Dynamic Chart Drill-Down

1. Contexto y Objetivo

Implementar la lógica de gestión de estado para un sistema de Drill-Down dinámico en un Dashboard de BI. El objetivo es que cada widget pueda navegar de forma independiente a través de una jerarquía de dimensiones, acumulando filtros y permitiendo la reversibilidad (Back) del estado.
Stack: Vue 3 (Composition API), Pinia, Cube.js (Query Schema).
2. Definición de Modelos (Interfaces)
Se deben crear/extender las siguientes interfaces en el sistema de tipos:
export interface DrillStep {
  dimension: string;    // Miembro de Cube.js (ej: 'Orders.category')
  value: any;           // Valor seleccionado en el click
  label: string;        // Etiqueta visual para breadcrumbs
}

export interface WidgetDrillState {
  currentLevel: number; // Nivel actual en la jerarquía (0 = base)
  history: DrillStep[]; // Pila de pasos realizados (LIFO)
}

// Extensión de la configuración del Widget
export interface WidgetConfig {
  id: string;
  dimensions: string[]; // Jerarquía: ['Nivel0', 'Nivel1', 'NivelN']
  drillActive: boolean;
  // ... otras propiedades existentes
}

3. Lógica del Store (Pinia)
A. State
 * widgets: Un record de WidgetConfig indexado por ID.
 * drillStates: Un record de WidgetDrillState indexado por ID para mantener el estado de navegación volátil separado de la configuración persistente.
B. Getters
 * getWidgetQuery(widgetId):
   * Debe identificar la dimensión activa usando widgets[id].dimensions[drillState.currentLevel].
   * Debe transformar el history en un array de filtros de Cube.js: { member: step.dimension, operator: 'equals', values: [step.value] }.
   * Debe retornar un objeto de consulta válido para el cubeAdapter que combine la dimensión activa, las medidas originales y los filtros acumulados.
 * getBreadcrumbs(widgetId): Retorna el array history para su representación en UI.
C. Actions
 * executeDrillDown(widgetId, selectedValue, label):
   * Validar si existe un nivel superior en dimensions.
   * Pushear el estado actual (dimensión previa + valor) al history.
   * Incrementar currentLevel.
   * Llamar a refreshWidget(widgetId).
 * goBack(widgetId):
   * Hacer pop del history.
   * Decrementar currentLevel.
   * Llamar a refreshWidget(widgetId).
 * refreshWidget(widgetId):
   * Obtener la query generada por getWidgetQuery.
   * Llamar al servicio de datos (cubeAdapter) y actualizar el dataset del widget específico.
4. Requerimientos de Integración
 * Desacoplamiento: El cubeAdapter no debe saber que existe un drill-down; solo debe recibir el objeto de query procesado por el store.
 * Inmutabilidad: Las mutaciones al historial deben hacerse de forma que Vue detecte los cambios para actualizar los componentes de ECharts reactivamente.
 * Reseteo: Al cambiar la configuración base del widget en el diseñador (vía WidgetConfigModal), el drillState de ese widget debe resetearse a nivel 0.
5. Criterios de Aceptación
 * El getter getWidgetQuery debe ser capaz de fusionar filtros previos con el nuevo nivel de profundidad.
 * La acción goBack debe restaurar el estado previo de los datos exactamente como estaban antes del último clic.
 * Si un widget no tiene activado drillActive, la lógica de executeDrillDown debe abortar silenciosamente.
Reflexión final para el intercambio (Colega a Colega):
He dejado la acción refreshWidget como el punto de entrada para la llamada al backend. 