# Project: Visualizacion Design Improvements

## Context
Este proyecto consiste en una mejora del módulo de visualización del Dashboard Studio. El objetivo es proporcionar una interfaz de arrastrar y soltar (drag-and-drop) moderna e intuitiva para configurar gráficos y paneles a partir de cubos de información.

## Objective
Implementar un configurador de visualizaciones dinámico con:
- Selección de cubos y campos (Métricas/Dimensiones).
- Interfaz de tres paneles (Origen, Configuración, Preview).
- Renderizado en tiempo real con soporte para múltiples tipos de gráficos.
- Persistencia en el esquema del dashboard.

## Technical Stack
- **Frontend:** Vue 3 (Composition API), Vite, Vanilla CSS.
- **Backend:** FastAPI (Python), PostgreSQL (con Cube.js como middleware de datos).
- **Libraries to Research:** Drag-and-drop (dnd-kit, vue-draggable), Charting (ECharts/Chart.js).

## Visual Direction
- **Modern Refinement:** Refinar los patrones existentes para una estética más limpia y profesional (según `@images/diseño_visualizacion.jpeg`).

## Reference
Basado en: `PRD.md`
