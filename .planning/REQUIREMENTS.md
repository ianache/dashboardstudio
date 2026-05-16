# Requirements: Resizable Properties Sidebar

## Overview
Se requiere que la barra lateral derecha de propiedades en el editor de integraciones sea ajustable en ancho. Esto permitirá a los usuarios expandir el panel cuando trabajen con campos extensos (como el editor de código o payloads JSON) y contraerlo para maximizar el área de trabajo del canvas.

## Functional Requirements (FR)
- [x] **FR-01: Tirador de Ajuste (Resize Handle):** Debe aparecer un borde interactivo en el margen izquierdo del panel de propiedades.
- [x] **FR-02: Interacción de Arrastre (Drag-to-Resize):** El usuario debe poder hacer clic en el tirador, arrastrar horizontalmente y soltar para fijar el nuevo ancho.
- [x] **FR-03: Límites de Tamaño:** El ancho debe tener un mínimo (ej: 250px) y un máximo (ej: 800px o 50% de la pantalla) para evitar romper la UI.
- [x] **FR-04: Persistencia de Estado:** El ancho ajustado debe mantenerse mientras el usuario navega por diferentes nodos en la misma sesión del editor.
- [x] **FR-05: Compatibilidad con Colapso:** La funcionalidad de resizable debe integrarse con el botón de colapsar actual, manteniendo el ancho personalizado al re-expandir.

## Technical Requirements (TR)
- [x] **TR-01: Implementación en Vue 3:** Utilizar el `Composition API` y eventos globales de mouse en `FlowEditorCanvas.vue`.
- [x] **TR-02: Estilo CSS:** Definir el tirador con feedback visual (cambio de cursor a `col-resize` y resaltado al hacer hover).
- [x] **TR-03: Performance:** Asegurar que el redimensionado sea fluido (60fps) mediante el uso de `requestAnimationFrame` o optimización de reactividad.

## User Interface (UI)
- [x] **UI-01: Visual Handle:** Tirador: Línea sutil de 4px-6px en el borde izquierdo del panel derecho.
- [x] **UI-02: Cursor:** Cursor: `col-resize`.
- [x] **UI-03: Active State:** Color: Azul primario (`#2563eb`) o gris suave (`#e2e8f0`) al estar activo.
