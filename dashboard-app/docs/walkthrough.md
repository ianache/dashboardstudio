# Walkthrough: JSON Viewer y Download (AI Assist)

El requerimiento era permitir al usuario exportar e inspeccionar el `Artifact` (el código JSON puro generado por la IA) antes de aplicar las tablas creadas al canvas del Modelo Dimensional.

## 📌 Cambios Implementados

### Lógica Refactorizada
- Agregadas las variables reactivas `aiViewMode` (por defecto en `'visual'`) y `aiRawJson` (para almacenar el texto JSON con indentación estándar de 2 espacios) en [DimensionalModelEditorView.vue](file:///c:/Users/ianache/Desktop/DATA/01-DOCUMENTOS/02-PROYECTOS/102-concesionarias/dashboardstudio/dashboard-app/src/views/DimensionalModelEditorView.vue).
- Se implementó la nueva función [downloadAIAssistJSON()](file:///c:/Users/ianache/Desktop/DATA/01-DOCUMENTOS/02-PROYECTOS/102-concesionarias/dashboardstudio/dashboard-app/src/views/DimensionalModelEditorView.vue#1593-1603). Esta función crea dinámicamente un `Blob` del tipo `application/json` usando el contenido en crudo de la respuesta, para disparar una descarga automática llamada `ai_generated_tables_{timestamp}.json`.
- Reinicio del visor a su estado visual predeterminado cada vez que se inyectan las tablas en el canvas.

### Interfaz del Modal de Asistente IA
- Construcción de un menú de controles al lado del texto *"N tabla(s) generadas"* que permite al usuario alternar entre **Visor Visual** (la vista clásica de tarjetas descriptivas) y **JSON**.
- Renderizado condicional de un bloque de código `.json-editor` cuando se selecciona la vista técnica:
  - Formato monoespaciado y con colores de contraste oscuro.
  - El usuario puede previsualizar allí mismo la estructura raw generada por el LLM.
- Adición funcional del botón **⬇ Descargar Artifact (.json)** posicionado arriba a la derecha del editor de texto.

### Resiliencia del Analizador JSON (Parser)
- Se reescribió la lógica interna para soportar de manera robusta casos donde la IA envuelve múltiples tablas dentro de un objeto en lugar de un array (ej. `{ "tables": [ ... ] }`).
- El analizador ahora evalúa en tres capas: 1) JSON directo, 2) Bloque Markdown, 3) Extracción de array como "fallback" estricto.
- Se implementó transparencia ante errores de sintaxis del LLM: si el JSON falla, la aplicación ahora revela el texto crudo en la propia alerta de error mediante un menú desplegable *"Ver respuesta original"*, facilitando el diagnóstico.

El resultado es un inspector de "Artifacts" moderno, robusto e integrado de manera nativa en el modal, con una tolerancia a errores del LLM líder en su clase.

# Walkthrough: Exportación desde el Listado (Cards)

Se solicitó habilitar el botón de exportación YAML directamente desde la vista en cuadrícula de modelos ([DimensionalModelListView.vue](file:///c:/Users/ianache/Desktop/DATA/01-DOCUMENTOS/02-PROYECTOS/102-concesionarias/dashboardstudio/dashboard-app/src/views/DimensionalModelListView.vue)) para optimizar el flujo de trabajo del usuario.

## 📌 Cambios Implementados
- Se inyectó el botón con el ícono de descarga (SVG estándar) a la **izquierda** del ícono de Edición dentro de la clase `.model-card-actions` de la tarjeta.
- Se agregó el manejador del evento `@click.stop="exportModel(model.id)"` para evitar conflictos de clicks con el contenedor interactivo.
- Se ha duplicado e integrado la lógica fundamental de compilación `js-yaml` a una nueva función que obtiene asíncronamente las colecciones de Nodos y Relaciones de `$store` y construye el Blob `.yaml` de manera idéntica al entorno de edición individual.

# Walkthrough: Exportación a Imagen PNG (Diseñador)

Se requería una manera fácil de tomar capturas estéticas y de alta definición del área de trabajo (canvas) para propósitos de documentación.

## 📌 Cambios Implementados
- Se instaló globalmente la biblioteca líder `html2canvas` para procesar el DOM y capturar visualizaciones íntegras de componentes Vue.
- En [DimensionalModelEditorView.vue](file:///c:/Users/ianache/Desktop/DATA/01-DOCUMENTOS/02-PROYECTOS/102-concesionarias/dashboardstudio/dashboard-app/src/views/DimensionalModelEditorView.vue), se integró un nuevo botón con forma de **imagen/captura** en la barra de herramientas, ubicado estrictamente a la **izquierda** del icono de script CubeJS.
- El manejador [handleExportPNG()](file:///c:/Users/ianache/Desktop/DATA/01-DOCUMENTOS/02-PROYECTOS/102-concesionarias/dashboardstudio/dashboard-app/src/components/dashboard/DashboardWidget.vue#162-193) invoca a `html2canvas`, escala el lienzo `x2` para garantizar nitidez, pinta un fondo blanco `#ffffff` (evitando transparencias indeseadas) y procesa el string de codificación base64 (`toDataURL`).
- El sistema de exportación formatea en tiempo real el nombre del archivo para cumplir la aserción: *minúsculas y espacios reemplazados por guiones* (ej. `recurso-humano.png`).

# Walkthrough: Asignación de Dashboards con Keycloak

Se reemplazó la lista ficticia/estática de usuarios ("mock") para la asignación de dashboards ([DashboardDesignerView.vue](file:///c:/Users/ianache/Desktop/DATA/01-DOCUMENTOS/02-PROYECTOS/102-concesionarias/dashboardstudio/dashboard-app/src/views/DashboardDesignerView.vue)) a favor del buscador orgánico directo hacia la API nativa de Administración de Keycloak (`Admin REST API`).

## 📌 Cambios Implementados
- **Barra de Búsqueda Integrada:** Se incluyó un input para buscar cuentas mediante texto. Éste dispara llamadas nativas al servidor OAuth2 de la variable de ambiente (`VITE_KEYCLOAK_URL`) autorizadas con el propio Access Token del empleado.
- **Resultados en Tiempo Real:** Los resultados exponen los perfiles oficiales extraídos del Directorio Activo/Keycloak (Nombre completo, Email, y Avatar auto-generado), previniendo asignaciones accidentales de usuarios que ya no existen.
- **Pre-carga de Permisos:** Al abrir el listado de asiganciones, en vez de ver solo IDs en blanco, el portal interrogará paralelamente a la misma API para reconstruir visualmente las "tarjetas" de los perfiles que ya estaban asignados y permitir eliminarlos ordenadamente.

> [!IMPORTANT]
> Esta operación consumirá eficientemente el endpoint `/admin/realms/{realm}/users`. Por arquitectura de seguridad de Keycloak, requerirá obligatoriamente que tu usuario tenga asignado el Rol Cliente de la herramienta `realm-management` -> **`view-users`** o en su defecto `query-users`. Si no cuenta con dicho permiso, reflejará en pantalla de forma amigable la falta de privilegios.

# Walkthrough: Captura PNG de Gráficos ECharts

El usuario requirió que ciertos gráficos alojados en los Dashboards (específicamente Barras, Línea y Pastel) pudieran ser extraídos como formato PNG en alta calidad de manera idéntica a su representación visual, sin recortes y usando nombres de archivo normalizados ("slugs").

## 📌 Modificaciones Ejecutadas
- **Icono Condicional:** En [DashboardWidget.vue](file:///c:/Users/ianache/Desktop/DATA/01-DOCUMENTOS/02-PROYECTOS/102-concesionarias/dashboardstudio/dashboard-app/src/components/dashboard/DashboardWidget.vue) se agregó un botón con el icono de "Exportar Imagen". Por solicitud técnica y visual, su aparición está limitada nativamente a `v-if="['bar', 'line', 'pie'].includes(widget.chartType)"`. 
- **Ocultamiento Limpio:** Dado que el requerimiento estipulaba que saliera "todo el contenido del chart" (incluyendo el título), optamos por generar el render sobre el recuadro general (`.dashboard-widget`). Para evitar que botones interactivos o de borrado contamine la presentación, la función oculta y restaura transparente en milisegundos todo el contenedor `.widget-actions`.
- **Normalización de Títulos:** Al procesar `html2canvas.toDataURL()`, la función sanitiza dinámicamente el nombre de la gráfica empleando `.normalize("NFD")` para desglosar y remover diacríticos (Acentos locales como `í`,`ó`,`ñ`), para finalmente aplicar la expresión regular `replace(/[^a-z0-9]+/g, '-')` y entregar nombres de descarga ultra limpios, e.g. `ganancia-historica-ano-2024.png`.

# Walkthrough: Maximizar Gráficos (Pop-Up)

Se añadió la funcionalidad en la barra superior de los componentes `DashboardGrid`/`DashboardWidget` para expandir un gráfico y analizarlo orgánicamente a resolución completa fuera de su celda temporal en pantalla.

## 📌 Modificaciones Ejecutadas
- **Botón Vectorial Adaptativo:** A la izquierda del botón tradicional "Actualizar", se integró un nuevo control interactivo. Este expone el icono expandir (`Maximizar`) si el estado subyacente del widget está en sus cuadrículas normales, y contraer (`Minimizar`) si el modo fullscreen está habilitado.
- **Jerarquía de Capas (Z-Index):** En vez de arriesgar una desalineación usando transformaciones directas en DOM (propensas a bugs con rejillas Draggables o Flex), la Grilla detecta cuál de sus tarjetas quiere "escapar" de su celda y la eleva al `zIndex 100`, empujando artificialmente la clase `.is-maximized` que clava al chart un `position: fixed` a 40px de los bordes del dispositivo del usuario con una sombra imponente.
- **Efecto Cortina de Modal Clásico:** Originalmente se usó una cortina superior con desenfoques. Para atender la solicitud visual ("no como una imagen difumidana sino el mismo card mostrado como un modal de tamaño que ocupe toda la pantalla"), se eliminó el filtro de difuminado y la capa (backdrop) pasó a vivir directamente detrás de la grilla de tu Dashboard, logrando una renderización puramente nativa con `rgba(0,0,0,0.5)`, destacando el componente orginal fielmente.
