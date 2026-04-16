---
phase: phase04
plan: 02
type: execute
wave: 1
depends_on: [phase04-01]
files_modified: [dashboard-app/src/views/VisualizationConfiguratorView.vue, dashboard-app/src/stores/visualizationConfigurator.js]
autonomous: true
requirements: [FR-01]
---

<objective>
Implement Advanced Metric Configuration to allow users to customize field aliases and formatting.

Purpose: Provide granular control over how data is displayed in the visualization.
Output: Clickable settings icon on dropped fields that opens a small configuration overlay or modal.
</objective>

<execution_context>
@C:/Users/ianache/.gemini/get-shit-done/workflows/execute-plan.md
</execution_context>

<tasks>

<task type="auto">
  <name>Task 1: Update Store for Field Metadata</name>
  <files>dashboard-app/src/stores/visualizationConfigurator.js</files>
  <action>
    - Add `updateMeasure` and `updateDimension` actions to modify properties like `alias` or `format`.
    - Ensure these properties are persisted when saving the widget.
  </action>
  <verify>
    <automated>Verify that calling update actions modifies the store state correctly.</automated>
  </verify>
  <done>Store updated to support per-field configuration.</done>
</task>

<task type="auto">
  <name>Task 2: Add Settings Trigger to Drop Zones</name>
  <files>dashboard-app/src/views/VisualizationConfiguratorView.vue</files>
  <action>
    - Add a "Settings" (cog) icon to each `active-field` item in the drop zones.
    - Implement a local state to track which field is being configured.
  </action>
  <verify>
    <automated>Check if the cog icon appears and triggers a configuration state.</automated>
  </verify>
  <done>UI trigger for field settings implemented.</done>
</task>

<task type="auto">
  <name>Task 3: Implement Field Settings Overlay</name>
  <files>dashboard-app/src/views/VisualizationConfiguratorView.vue</files>
  <action>
    - Create a small overlay or modal that appears when the settings icon is clicked.
    - Add an input for "Nombre Visible" (Alias).
    - Add a dropdown for "Formato" (e.g., Number, Currency, Percent).
    - Bind these inputs to the store via the new update actions.
  </action>
  <verify>
    <automated>Verify that changing settings in the overlay updates the chart preview and is saved to the store.</automated>
  </verify>
  <done>Field settings overlay is functional and reactive.</done>
</task>

</tasks>

<success_criteria>
- Users can click a settings icon on any dropped field.
- Users can change the display name (alias) of a field.
- Users can choose basic formatting for metrics.
- Changes are reflected in the real-time preview.
</success_criteria>
