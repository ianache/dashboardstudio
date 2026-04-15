# Phase 2: Drag-and-Drop Core - Context

**Status:** Plan Phase
**Description:** Implement the drag-and-drop interface for configuring visualizations using `vuedraggable` v4.

## Decisions
- [x] Use `vuedraggable` for drag-and-drop.
- [x] Store full metadata objects in `visualizationConfiguratorStore`.
- [x] Enforce type validation (measures to Series, dimensions to Análisis).
- [x] Use a searchable field list in the Source Panel.

## Phase Goals
1. Implement the Source Panel in `VisualizationConfiguratorView.vue` with Cube.js metadata.
2. Configure `vuedraggable` in Source and Config panels.
3. Create Drop Zones for "Series" and "Análisis".
4. Implement validation (correct zones, no duplicates).

## User Feedback
- Use a 6-dot handle for draggable items.
- Modern Refinement: spacing (8px grid), hover states, clean typography.
- Cloning logic for Source Panel.
