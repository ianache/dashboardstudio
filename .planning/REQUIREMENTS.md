# Scoped Requirements: Visualizacion Design Improvements

## 1. Functional Requirements (FR)

### FR-01: Drag-and-Drop Interface
- Implement a three-column layout:
  - **Left:** Source Panel with searchable metrics and dimensions from Cube.js.
  - **Center:** Configuration Panel with drop zones for "Series" and "Analysis".
  - **Right:** Preview Panel for real-time chart rendering.
- Use `vuedraggable` for high-performance drag-and-drop interactions.
- Provide visual feedback during drag (highlighting valid drop zones).

### FR-02: Real-time Chart Preview
- Automatically trigger Cube.js queries when configuration changes.
- Support multiple chart types (Bar, Line, Pie, etc.) using `vue-echarts`.
- Implement a "Loading" state during data fetching.

### FR-03: Advanced Configuration
- Modal/Popover to edit metric aliases and formatting (RF-04 from PRD).
- Support for "Quick Filters" (Filtros Rápidos) as per PRD update.
- Aggregate functions selection (Sum, Avg, Min, Max, Count).

### FR-04: Dashboard Integration
- Ability to save the configuration as a new widget in the active dashboard.
- Persist widget layout and query parameters in the dashboard JSON schema.

## 2. Non-Functional Requirements (NFR)
- **Performance:** Preview update < 2s for 10k records.
- **Usability:** 6-dot handle for draggable items, intuitive hover states.
- **Modern Refinement:** Clean typography, consistent spacing (8px grid), and refined color palette matching `diseño_visualizacion.jpeg`.
- **Responsiveness:** Central panel must be collapsible to maximize preview area.

## 3. Technical Specifications
- **Frontend Framework:** Vue 3 + Pinia + Vite.
- **Data Layer:** `@cubejs-client/core` for querying.
- **Visuals:** `echarts` + `vue-echarts`.
- **Drag-and-Drop:** `vuedraggable` (already in `package.json`).

## 4. UI/UX Guidelines
- **Modern Look:** Use subtle shadows, rounded corners (8px), and a neutral base color palette with vibrant accents for metrics/dimensions.
- **Interaction:** Smooth transitions when collapsing the center panel.
