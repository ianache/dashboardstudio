Roadmap de ejecución para tu sesión de VibeCoding:

​Fase 1: El Cimiento (Tipado y Estructura)
​Antes de que Claude escriba lógica, debe conocer el "contrato".

​Definición de Interfaces: Crear o actualizar los archivos .ts de tipos. Sin esto, el autocompletado y la validación de tipos en el Store fallarán.
​Ampliación del Estado (State): Inicializar los objetos widgets y drillStates en el Store de Pinia.

​Fase 2: El Cerebro (Getters de Transformación)

​Esta es la parte más crítica porque es donde se "traduce" la navegación a lenguaje de Cube.js.

​Implementar getWidgetQuery: Claude debe asegurar que este getter sea puro y que pueda combinar correctamente los filtros existentes con los nuevos del historial.
​Implementar getBreadcrumbs: Una lógica simple para que la UI sepa qué mostrar.

​Fase 3: La Maquinaria (Acciones de Transición)

​Aquí definimos cómo se "mueve" el sistema.
​Implementar executeDrillDown: La lógica de validación (¿hay más niveles?) y el "push" al historial.
​Implementar goBack: La lógica de "pop" y retroceso de nivel.
​Implementar refreshWidget: El puente que llama al adaptador. Nota: Aquí es donde probarás si la query generada en la Fase 2 realmente trae datos de Cube.js.
​Fase 4: La Conexión Visual (ECharts & UI)
​Una vez que el Store funciona en la consola/DevTools, vamos a la pantalla.
​Binding en ChartRenderer: Conectar el evento click de ECharts a la acción executeDrillDown del Store.
​Componente Breadcrumbs: Crear el pequeño componente visual sobre el gráfico para mostrar la ruta y permitir el goBack.
​Fase 5: El Diseñador (Configuración)
​Finalmente, cerramos el círculo permitiendo que el usuario configure esto.
​Actualizar WidgetConfigModal: Modificar el input de dimensiones para que acepte un array (jerarquía) en lugar de un valor único.
​Mi consejo de "colega" para el prompt inicial a ClaudeCode:
​Si vas a usar ClaudeCode, yo le lanzaría el primer prompt así:
​"Claude, vamos a implementar el Drill-Down dinámico. Empecemos por la Fase 1 y 2: define las interfaces DrillStep y WidgetDrillState, y luego implementa el getter getWidgetQuery en el Store. No pases a la UI hasta que la lógica de transformación de la query de Cube.js sea perfecta."
​¿Por qué este orden?
Porque si la lógica del getWidgetQuery (Fase 2) está mal, el gráfico te va a mostrar basura o dar error de API, y te volverás loco buscando el bug en la UI cuando el problema es la mutación del objeto JSON de Cube.

Tomar detalles desde las siguientes ReqSpecs:
1. reqspec01.md
2. reqspec02.md