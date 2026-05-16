---
gsd_state_version: 1.0
id: note-dragging-fix
title: Corregir comportamiento de arrastre de notas
area: frontend
status: todo
created_at: "2026-05-17T02:00:00.000Z"
priority: medium
---

# Todo: Corregir comportamiento de arrastre de notas

## Context
Al implementar las notas en el canvas, se separó la lógica de nodos y notas. Sin embargo, el manejador global de movimiento de ratón (`onGlobalMousemove`) no está verificando el estado `isDraggingNote`, lo que impide que las notas se muevan correctamente al ser arrastradas, a diferencia de los nodos funcionales.

## Description
Las notas deben poder moverse por el canvas con la misma fluidez y comportamiento (snapping, coordenadas) que los nodos normales. 

## Proposed Fix
Actualizar `onGlobalMousemove` en `FlowEditorCanvas.vue` para incluir la lógica de arrastre cuando `isDraggingNote` es verdadero, utilizando la referencia `draggedNode` (que actualmente se asigna tanto para nodos como para notas en sus respectivos eventos `mousedown`).

## Acceptance Criteria
- [ ] Las notas se desplazan al ser arrastradas con el ratón.
- [ ] El movimiento respeta el "snap to grid" si está activo.
- [ ] El comportamiento es idéntico al de los nodos funcionales.
