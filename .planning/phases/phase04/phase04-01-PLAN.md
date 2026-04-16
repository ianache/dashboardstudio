---
phase: phase04
plan: 01
type: execute
wave: 1
depends_on: [phase03]
files_modified: [dashboard-app/src/views/VisualizationConfiguratorView.vue, dashboard-app/src/stores/visualizationConfigurator.js]
autonomous: true
requirements: [FR-01]
---

<objective>
Implement the "Save to Dashboard" logic and basic UI refinements for the visualization configurator.

Purpose: Allow users to persist their configurations and provide a more polished experience.
Output: Working Save button that redirects back to the dashboard designer.
</objective>

<execution_context>
@C:/Users/ianache/.gemini/get-shit-done/workflows/execute-plan.md
@C:/Users/ianache/.gemini/get-shit-done/templates/summary.md
</execution_context>

<tasks>

<task type="auto">
  <name>Task 1: Implement Persistence Logic</name>
  <files>dashboard-app/src/views/VisualizationConfiguratorView.vue</files>
  <action>
    - Update `handleSave` to call `dashboardStore.addWidget` or `dashboardStore.updateWidget` based on `store.widgetId`.
    - Map `currentWidget.value` to the format expected by the store actions.
    - Add a loading state to the Save button to prevent multiple clicks.
    - Redirect back to `/designer/${store.dashboardId}` upon success.
  </action>
  <verify>
    <automated>Verify that clicking Save redirects and that the new/updated widget appears in the dashboard store.</automated>
  </verify>
  <done>Persistence logic implemented and functional.</done>
</task>

<task type="auto">
  <name>Task 2: Refine Configuration Store</name>
  <files>dashboard-app/src/stores/visualizationConfigurator.js</files>
  <action>
    - Ensure `setWidget` correctly populates the store from an existing widget object, including `chartType` and `cubeQuery`.
    - Add any missing fields like `title` editing capability to the UI (if not already present).
  </action>
  <verify>
    <automated>Check if editing an existing widget loads its current state correctly.</automated>
  </verify>
  <done>Store refined to handle full widget lifecycle.</done>
</task>

<task type="auto">
  <name>Task 3: UI Polish - Transitions and Layout</name>
  <files>dashboard-app/src/views/VisualizationConfiguratorView.vue</files>
  <action>
    - Add a transition-group to the draggable lists for smoother movements.
    - Implement a "Loading Overlay" on the entire view when metadata or save is in progress.
    - Refine the panel headers and spacing to match the 8px grid alignment.
  </action>
  <verify>
    <automated>Check for smooth transitions and correct alignment.</automated>
  </verify>
  <done>UI is polished and follows design guidelines.</done>
</task>

</tasks>

<success_criteria>
- Users can save new widgets to a dashboard.
- Users can update existing widgets.
- The UI feels smooth and responsive with proper feedback.
</success_criteria>
