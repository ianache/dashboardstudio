# Feature List

## Visualizacion Design Improvements

> nota: considerar el boceto @images/diseño_visualizacion.jpeg

## 1. Objetivo del Módulo
Permitir a los usuarios finales configurar visualizaciones de datos personalizadas mediante una interfaz intuitiva de "arrastrar y soltar" (drag-and-drop), utilizando Cubos de Información como fuente de datos primaria.
## 2. Descripción de la Interfaz (UI/UX)
El módulo se divide en tres paneles principales dispuestos horizontalmente:
### A. Panel de Origen (Izquierda)
 * **Selector de Cubos:** Un menú desplegable para elegir la fuente de datos (Cubo).
 * **Listado de Métricas:** Lista de campos cuantitativos (ej. Ventas, Cantidad). Debe mostrar el conteo total de métricas disponibles.
 * **Listado de Dimensiones:** Lista de campos cualitativos (ej. Fecha, Región, Categoría). Debe mostrar el conteo total de dimensiones disponibles.
 * **Interacción:** Cada elemento debe tener un "handler" (icono de 6 puntos) que indique que es un objeto arrastrable.
### B. Panel de Configuración (Centro - Barra Plegable)
 * **Control de Plegado:** Un botón superior para expandir/retraer el panel y maximizar el área de vista previa.
 * **Sección de Series:** * Espacios numerados [1], [2], ... para soltar métricas.
   * **Botón Configurar:** Icono de engranaje por cada serie para definir agregaciones (Suma, Promedio, etc.) o estilos de color.
 * **Sección de Análisis:**
   * Espacios numerados para soltar las dimensiones que agruparán los datos.
### C. Panel de Preview (Derecha)
 * **Renderizado en Tiempo Real:** El gráfico debe actualizarse automáticamente al detectar un cambio en el panel de configuración.
 * **Selector de Tipo de Gráfico:** Botones superiores para cambiar entre Pie, Bar, Line, etc. (según la imagen refinada).
## 3. Requerimientos Funcionales (RF)
| ID | Requerimiento | Descripción |
|---|---|---|
| **RF-01** | **Carga de Cubos** | Al seleccionar un cubo, el sistema debe realizar una petición asíncrona para poblar las listas de métricas y dimensiones. |
| **RF-02** | **Drag-and-Drop** | Los elementos de métricas solo pueden soltarse en la sección "Series" y las dimensiones en "Análisis". |
| **RF-03** | **Validación de Datos** | Si una métrica se suelta en un campo de análisis, el sistema debe rechazar la acción y mostrar un feedback visual. |
| **RF-04** | **Configuración de Serie** | Al hacer clic en "Configurar", se abrirá un modal/popover para editar el alias de la métrica y su formato numérico. |
| **RF-05** | **Persistencia** | La configuración de la pestaña debe poder guardarse en el esquema del Dashboard (JSON). |
## 4. Requerimientos No Funcionales (RNF)
 * **Rendimiento:** La actualización del "Preview" no debe exceder los 2 segundos para datasets de hasta 10,000 registros.
 * **Usabilidad:** Debe cumplir con las pautas de accesibilidad para el estado de "arrastre" (cambio de cursor y resaltado de zona de soltado).
 * **Adaptabilidad:** El panel de preview debe ser responsive y reajustar el tamaño del gráfico al expandir/retraer la barra central.
## 5. Casos de Uso Principales
 1. **Usuario selecciona Cubo "Ventas":** Se listan métricas como "Ingresos" y dimensiones como "Mes".
 2. **Usuario arrastra "Ingresos" a Serie [1]:** El gráfico de preview muestra un valor total único (Gran Total).
 3. **Usuario arrastra "Mes" a Análisis [1]:** El gráfico se desglosa automáticamente mostrando los ingresos por mes.
 4. **Usuario cambia a Gráfico de Barras:** La visualización muta de circular a barras sin perder la configuración de datos.
5.  **"Filtros Rápidos"**: añadir una sección de "Filtros Rápidos" debajo de Dimensiones, lo que permitiría al usuario limpiar el ruido de los datos antes de ver la vista previa.
