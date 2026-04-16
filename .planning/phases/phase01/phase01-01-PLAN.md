---
phase: phase01-setup-ui
plan: 01
type: execute
wave: 1
depends_on: []
files_modified: [dashboard-app/src/stores/visualizationConfigurator.js, dashboard-app/src/router/index.js]
autonomous: true
requirements: [FR-01, FR-02]

must_haves:
  truths:
    - "New route /designer/:id/configure is accessible."
    - "visualizationConfigurator store exists and can hold visualization state."
  artifacts:
    - path: "dashboard-app/src/stores/visualizationConfigurator.js"
      provides: "Visualization state management"
    - path: "dashboard-app/src/router/index.js"
      provides: "Route registration"
  key_links:
    - from: "dashboard-app/src/router/index.js"
      to: "dashboard-app/src/views/VisualizationConfiguratorView.vue"
      via: "Route lazy loading"
---

<objective>
Setup the foundation for the visualization designer by creating the Pinia store for temporary state and configuring the necessary routing.

Purpose: Decouple the visualization configuration state from the main dashboard store and enable navigation to the new designer view.
Output: visualizationConfigurator store and route registration.
</objective>

<execution_context>
@C:/Users/ianache/.gemini/get-shit-done/workflows/execute-plan.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/REQUIREMENTS.md
@dashboard-app/src/router/index.js
@dashboard-app/src/stores/dashboard.js
@dashboard-app/src/stores/cubejs.js
</context>

<tasks>

<task type="auto">
  <name>Task 1: Create visualizationConfigurator Pinia store</name>
  <files>dashboard-app/src/stores/visualizationConfigurator.js</files>
  <action>
    Create a new Pinia store named 'visualizationConfigurator'. 
    State should include:
    - dashboardId: null (string)
    - widgetId: null (string, for editing existing widgets)
    - title: 'Nuevo Gráfico' (string)
    - selectedCube: null (string)
    - measures: [] (array of measure objects)
    - dimensions: [] (array of dimension objects)
    - filters: [] (array of filter objects)
    - timeDimension: null (object {dimension, granularity})
    - chartType: 'bar' (string)
    - chartOptions: {} (object)

    Actions should include:
    - setDashboardId(id)
    - setWidget(widget) - to load existing widget config
    - setCube(cubeName)
    - addMeasure(measure)
    - removeMeasure(measureName)
    - addDimension(dimension)
    - removeDimension(dimensionName)
    - setChartType(type)
    - reset() - clears state to defaults
  </action>
  <verify>
    <automated>node -e "import('./dashboard-app/src/stores/visualizationConfigurator.js').then(m => console.log('Store loaded'))"</automated>
  </verify>
  <done>Store file created with all required state fields and actions.</done>
</task>

<task type="auto">
  <name>Task 2: Register Visualization Configurator route</name>
  <files>dashboard-app/src/router/index.js</files>
  <action>
    Add a new route within the children of the '/' route (protected by AppLayout).
    - Path: 'designer/:id/configure'
    - Name: 'VisualizationConfigurator'
    - Component: () => import('@/views/VisualizationConfiguratorView.vue')
    - Meta: { requiresDesigner: true, breadcrumbs: ['Diseño', 'Configurador'] }
    
    Ensure it is placed correctly among other 'designer' routes.
  </action>
  <verify>
    <automated>grep "VisualizationConfigurator" dashboard-app/src/router/index.js</automated>
  </verify>
  <done>Route registered in router/index.js pointing to the new view.</done>
</task>

</tasks>

<verification>
Check that the store is correctly imported and the route is present in the router file.
</verification>

<success_criteria>
- Pinia store initialized with the specified structure.
- Route /designer/:id/configure exists and points to the correct view (even if view doesn't exist yet).
</success_criteria>

<output>
After completion, create `.planning/phases/phase01/phase01-01-SUMMARY.md`
</output>
