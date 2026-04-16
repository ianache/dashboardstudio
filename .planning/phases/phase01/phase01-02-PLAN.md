---
phase: phase01-setup-ui
plan: 02
type: execute
wave: 2
depends_on: [phase01-01]
files_modified: [dashboard-app/src/views/VisualizationConfiguratorView.vue]
autonomous: true
requirements: [FR-01, NFR-Modern Refinement]

must_haves:
  truths:
    - "VisualizationConfiguratorView.vue exists and renders a 3-column layout."
    - "The UI uses existing CSS variables for consistent look (Modern Refinement)."
  artifacts:
    - path: "dashboard-app/src/views/VisualizationConfiguratorView.vue"
      provides: "Base layout for visualization configuration"
  key_links:
    - from: "VisualizationConfiguratorView.vue"
      to: "dashboard-app/src/stores/visualizationConfigurator.js"
      via: "Pinia useVisualizationConfiguratorStore"
---

<objective>
Implement the base UI scaffolding for the Visualization Configurator with a three-column layout following the "Modern Refinement" style.

Purpose: Provide the visual structure where subsequent features (drag and drop, preview) will be integrated.
Output: Base VisualizationConfiguratorView.vue component.
</objective>

<execution_context>
@C:/Users/ianache/.gemini/get-shit-done/workflows/execute-plan.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/REQUIREMENTS.md
@dashboard-app/src/assets/main.css
@dashboard-app/src/views/DashboardDesignerView.vue
@dashboard-app/src/stores/visualizationConfigurator.js
</context>

<tasks>

<task type="auto">
  <name>Task 1: Create VisualizationConfiguratorView component</name>
  <files>dashboard-app/src/views/VisualizationConfiguratorView.vue</files>
  <action>
    Create the shell of the VisualizationConfiguratorView.vue.
    - Set up the script section using Composition API and Pinia store integration.
    - Implement a 3-column grid layout in the template:
        - .panel-source (Left panel for data sources)
        - .panel-config (Center panel for configuration drop zones)
        - .panel-preview (Right panel for chart preview)
    - Add a header section with:
        - Breadcrumbs (using uiStore.setBreadcrumbs in onMounted)
        - Action buttons: "Guardar" (primary) and "Cancelar" (secondary)
    - Set up basic lifecycle hooks to initialize/reset the store.
  </action>
  <verify>
    <automated>grep -E "panel-source|panel-config|panel-preview" dashboard-app/src/views/VisualizationConfiguratorView.vue</automated>
  </verify>
  <done>View component created with the required 3-column layout structure.</done>
</task>

<task type="auto">
  <name>Task 2: Apply "Modern Refinement" styles</name>
  <files>dashboard-app/src/views/VisualizationConfiguratorView.vue</files>
  <action>
    Apply scoped CSS to VisualizationConfiguratorView.vue.
    - Use `display: grid` with `grid-template-columns: 280px 320px 1fr` for the main layout.
    - Use variables from main.css (--border, --bg, --card-bg, --shadow, --border-radius).
    - Ensure 8px grid alignment (padding/margin: 8px, 16px, 24px).
    - Give panels a clean look: white background, rounded corners (8px), subtle border (1px solid var(--border)).
    - Add descriptive headings to each panel (e.g., "Origen de Datos", "Configuración", "Vista Previa").
  </action>
  <verify>
    <automated>grep "grid-template-columns" dashboard-app/src/views/VisualizationConfiguratorView.vue</automated>
  </verify>
  <done>Styles applied that meet the "Modern Refinement" non-functional requirements.</done>
</task>

</tasks>

<verification>
Check that the component is registered in the router and that the 3-column layout is visible.
</verification>

<success_criteria>
- VisualizationConfiguratorView.vue exists and displays three distinct columns.
- The layout is responsive and fills the available screen height.
- Design matches the "Modern Refinement" aesthetics (clean, professional).
</success_criteria>

<output>
After completion, create `.planning/phases/phase01/phase01-02-SUMMARY.md`
</output>
