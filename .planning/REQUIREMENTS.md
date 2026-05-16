# Requirements: Markdown Notes in Editor

## Overview
Se requiere extender las capacidades del editor de integraciones permitiendo a los usuarios añadir notas descriptivas en formato Markdown directamente sobre el lienzo de diseño. Estas notas servirán como documentación visual, permitiendo explicar la lógica del flujo, marcar secciones o dejar recordatorios.

## Functional Requirements (FR)
- **FR-01: Herramienta "Note":** Añadir una nueva herramienta llamada "Note" en el catálogo de herramientas del editor.
- **FR-02: Categoría "Annotations":** Crear una nueva categoría visual en el panel izquierdo llamada "Annotations" (Anotaciones) para agrupar herramientas de documentación.
- **FR-03: Colocación por Drag & Drop:** El usuario debe poder arrastrar la herramienta "Note" desde el catálogo y soltarla en cualquier posición libre del canvas.
- **FR-04: Edición en Línea (Inline Editing):**
    - Al hacer clic sobre una nota, esta debe entrar en "Modo Edición", mostrando un `textarea` con el contenido Markdown crudo.
    - Al hacer clic fuera de la nota (blur), se debe renderizar el contenido visualmente usando sintaxis Markdown.
- **FR-05: Personalización de Estilo:**
    - **Paleta de Colores:** En modo edición, la cabecera de la nota debe mostrar 5 círculos de color (Amarillo, Azul, Verde, Rosa, Gris) para cambiar el color de fondo de la nota.
    - **Tamaño de Fuente:** En modo edición, la cabecera debe incluir botones (+ / -) para ajustar el tamaño de fuente base del contenido Markdown.
- **FR-06: Redimensionado Dinámico:** La nota debe permitir ajustar su ancho y alto mediante un tirador (handle) ubicado en la esquina inferior derecha.
- [x] **FR-07: Persistencia Dedicada:** Las notas deben guardarse en un array independiente (`flow_notes`) separado de los nodos funcionales del flujo.
- [x] **FR-08: Capa de Fondo (Z-Order):** Las notas deben dibujarse siempre en el fondo, por detrás de todos los nodos funcionales y de todas las conexiones (flechas).

## Technical Requirements (TR)
- **TR-01: Integración de Marked.js:** Utilizar la librería `marked` para la conversión de MD a HTML.
- **TR-02: Sanitización de HTML:** Utilizar `dompurify` para asegurar que el HTML generado por Markdown sea seguro.
- [x] **TR-03: Renderizado de Capas:** Modificar `FlowEditorCanvas.vue` para renderizar el array de notas antes que los SVGs de las conexiones y el array de nodos funcionales.
- **TR-04: Extensión del Esquema DB:** Añadir la columna `flow_notes` (JSON) al modelo `IntegrationFlow` en el backend.
- **TR-05: Lógica de Resize NWSE:** Implementar manejadores de eventos de ratón específicos para el tirador de redimensionado de las notas.

## User Interface (UI)
- **Icono:** `sticky_note_2` o `description` (Material Symbols).
- **Colores (Sticky Notes):** 
    - Amarillo: `#fef9c3` (Borde: `#fde047`)
    - Azul: `#dbeafe` (Borde: `#93c5fd`)
    - Verde: `#dcfce7` (Borde: `#86efac`)
    - Rosa: `#fce7f3` (Borde: `#f9a8d4`)
    - Gris: `#f1f5f9` (Borde: `#cbd5e1`)
- **Tirador de Resize:** Icono discreto en la esquina inferior derecha.
- **Cursor:** `nwse-resize` sobre el tirador.
