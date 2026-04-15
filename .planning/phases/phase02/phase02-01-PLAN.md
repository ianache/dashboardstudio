---
phase: phase02
plan: 01
type: execute
wave: 1
depends_on: []
files_modified: [dashboard-app/src/stores/visualizationConfigurator.js, dashboard-app/src/views/VisualizationConfiguratorView.vue]
autonomous: true
requirements: [FR-01]
must_haves:
  truths:
    - "Source Panel lists cubes from Cube.js meta."
    - "Measures and Dimensions are correctly identified and listed."
    - "Field list is searchable."
    - "Fields are draggable with cloning enabled."
  artifacts:
    - path: "dashboard-app/src/stores/visualizationConfigurator.js"
      provides: "Updated store for DND objects"
    - path: "dashboard-app/src/views/VisualizationConfiguratorView.vue"
      provides: "Source panel implementation"
  key_links:
    - from: "useCubeStore"
      to: "VisualizationConfiguratorView.vue"
      via: "computed filtered lists"
---

<objective>
Implement the Source Panel in `VisualizationConfiguratorView.vue` with Cube.js metadata integration and draggable fields.

Purpose: Allow users to browse and drag Cube.js fields (measures and dimensions) for visualization configuration.
Output: Searchable source lists with draggable items (clone mode).
</objective>

<execution_context>
@C:/Users/ianache/.gemini/get-shit-done/workflows/execute-plan.md
@C:/Users/ianache/.gemini/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/STATE.md
@.planning/phases/phase02/02-RESEARCH.md
@.planning/phases/phase02/phase02-CONTEXT.md
@dashboard-app/src/stores/cubejs.js
@dashboard-app/src/stores/visualizationConfigurator.js
@dashboard-app/src/views/VisualizationConfiguratorView.vue
</context>

<tasks>

<task type="auto">
  <name>Task 1: Enhance Store for Metadata Objects</name>
  <files>dashboard-app/src/stores/visualizationConfigurator.js</files>
  <action>
    - Update the `visualizationConfiguratorStore` to store full metadata objects in `measures` and `dimensions` arrays instead of just names.
    - Each object should have: `fullName`, `title`, `type`, `memberType`.
    - Update `setWidget` to map the `cubeQuery` (which uses key/label) back to these metadata objects using `useCubeStore` if available.
    - Modify `addMeasure`/`addDimension` or replace them with logic that handles objects.
    - Ensure `selectedCube` defaults to the first available cube from `useCubeStore` if not set.
  </action>
  <verify>
    <automated>Check if measures/dimensions arrays hold objects with fullName and title.</automated>
  </verify>
  <done>Store supports object-based field selections.</done>
</task>

<task type="auto">
  <name>Task 2: Build Source Panel UI & Field Search</name>
  <files>dashboard-app/src/views/VisualizationConfiguratorView.vue</files>
  <action>
    - Replace the placeholder in the "Origen de Datos" panel with a Cube selector (`<select>`).
    - Connect the selector to `store.selectedCube` and load cubes from `useCubeStore`.
    - Implement two searchable lists: "Métricas" (measures) and "Análisis" (dimensions) for the selected cube.
    - Use `computed` properties to filter these lists based on search inputs (reactive state).
    - Map Cube.js metadata to the objects expected by the store.
  </action>
  <verify>
    <automated>Verify Cube selector and search inputs are rendered and functional.</automated>
  </verify>
  <done>Source Panel displays searchable lists of fields from the selected Cube.</done>
</task>

<task type="auto">
  <name>Task 3: Draggable Fields & Handle</name>
  <files>dashboard-app/src/views/VisualizationConfiguratorView.vue</files>
  <action>
    - Wrap the source list items with `vuedraggable` (v4).
    - Configure the `measures` list: `group="{ name: 'measures', pull: 'clone', put: false }"`.
    - Configure the `dimensions` list: `group="{ name: 'dimensions', pull: 'clone', put: false }"`.
    - Use `:item-key="'fullName'"` for both.
    - Implement the field UI with a 6-dot drag handle icon and hover states (Modern Refinement).
    - Ensure `clone` prop is used to provide the metadata object.
  </action>
  <verify>
    <automated>Check that vuedraggable is correctly initialized and items are draggable.</automated>
  </verify>
  <done>Fields in Source Panel are draggable with clone behavior and proper handles.</done>
</task>

</tasks>

<verification>
Check that fields from different cubes can be loaded, filtered, and dragged (ghost element appears).
</verification>

<success_criteria>
- Cube selector lists all available cubes from metadata.
- Metrics and dimensions are listed and searchable.
- Fields are draggable with a visible handle and cloning behavior.
</success_criteria>

<output>
After completion, create `.planning/phases/phase02/phase02-01-SUMMARY.md`
</output>
