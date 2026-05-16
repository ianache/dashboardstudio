---
gsd_state_version: 1.0
id: note-properties-edit-fix
title: Corregir selección y edición de propiedades de notas
area: frontend
status: todo
created_at: "2026-05-17T02:10:00.000Z"
priority: high
---

# Todo: Corregir selección y edición de propiedades de notas

## Context
Tras separar las notas en una capa de fondo independiente, el evento de clic no está activando correctamente el panel de propiedades para las notas, o bien el panel no está preparado para mostrar los campos específicos de las anotaciones (Contenido Markdown, Color, etc.).

## Description
Al hacer clic sobre una nota en el canvas, esta debe quedar seleccionada (visualizado con un borde resaltado) y el panel lateral derecho debe mostrar sus propiedades editables. Actualmente, la selección parece estar limitada a nodos funcionales.

## Proposed Fix
1.  Actualizar el manejador `selectNote(note)` en `FlowEditorCanvas.vue` para asegurar que limpia la selección de nodos/conexiones anteriores.
2.  Verificar que el panel de propiedades en el template de `FlowEditorCanvas.vue` tiene un bloque `v-else-if="selectedNote"` que muestre los controles de edición (textarea para el contenido, selectores de estilo).
3.  Asegurar que los cambios realizados en el panel se reflejan reactivamente en el objeto de la nota.

## Acceptance Criteria
- [ ] Al hacer clic en una nota, se resalta visualmente.
- [ ] El panel lateral derecho muestra las propiedades de la nota seleccionada.
- [ ] Los cambios en las propiedades (ej: texto MD) se guardan y previsualizan correctamente.
