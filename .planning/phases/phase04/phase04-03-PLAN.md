---
phase: phase04
plan: 03
type: execute
wave: 1
depends_on: [phase04-02]
files_modified: [dashboard-app/src/views/VisualizationConfiguratorView.vue]
autonomous: true
requirements: [FR-01]
---

<objective>
Finalize the Visualization Configurator with Quick Filters and a collapsible Config Panel.

Purpose: Optimize the workspace and provide basic filtering capabilities within the configurator.
Output: Working collapsible sidebar for the config panel and a basic UI for adding quick filters.
</objective>

<execution_context>
@C:/Users/ianache/.gemini/get-shit-done/workflows/execute-plan.md
</execution_context>

<tasks>

<task type="auto">
  <name>Task 1: Implement Collapsible Config Panel</name>
  <files>dashboard-app/src/views/VisualizationConfiguratorView.vue</files>
  <action>
    - Add a toggle button to collapse/expand the center "Configuration" panel.
    - Update the grid layout to adjust when the panel is collapsed.
  </action>
  <verify>
    <automated>Verify that clicking the toggle collapses the panel and expands the preview area.</automated>
  </verify>
  <done>Collapsible configuration panel implemented.</done>
</task>

<task type="auto">
  <name>Task 2: Implement Quick Filters UI</name>
  <files>dashboard-app/src/views/VisualizationConfiguratorView.vue</files>
  <action>
    - Add a "Filtros Rápidos" section to the configuration panel.
    - Implement a drop zone for dimensions to act as filters.
    - Add a basic input/dropdown for filter values within each dropped filter item.
  </action>
  <verify>
    <automated>Check if dimensions can be dropped into the filters zone and if they update the chart preview.</automated>
  </verify>
  <done>Quick filters UI and logic implemented.</done>
</task>

<task type="auto">
  <name>Task 3: Final Aesthetic Polish</name>
  <files>dashboard-app/src/views/VisualizationConfiguratorView.vue</files>
  <action>
    - Refine all shadows and border colors to match the "Modern Refinement" style.
    - Ensure consistent 8px grid spacing across all panels.
    - Final check of the "Save" workflow to ensure everything (including new filters) is persisted.
  </action>
  <verify>
    <automated>Final visual inspection and E2E save test.</automated>
  </verify>
  <done>Visualizer configurator is fully polished and functional.</done>
</task>

</tasks>

<success_criteria>
- The configuration panel can be collapsed to maximize chart preview space.
- Users can add and configure filters.
- The UI follows high-quality aesthetic standards.
</success_criteria>
