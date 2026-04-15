---
phase: phase02
plan: 02
type: execute
wave: 2
depends_on: [phase02-01]
files_modified: [dashboard-app/src/views/VisualizationConfiguratorView.vue, dashboard-app/src/assets/main.css]
autonomous: false
requirements: [FR-01, NFR-Modern Refinement]
---

<objective>
Create the configuration drop zones for "Series" and "Análisis" with validation and UI states in the center panel.

Purpose: Allow users to specify metrics and dimensions for their chart using an intuitive drag-and-drop workflow.
Output: Functional drop zones with validation and removal capabilities.
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
@dashboard-app/src/stores/visualizationConfigurator.js
@dashboard-app/src/views/VisualizationConfiguratorView.vue
</context>

<tasks>

<task type="auto">
  <name>Task 1: Config Panel Drop Zones & Draggable Targets</name>
  <files>dashboard-app/src/views/VisualizationConfiguratorView.vue</files>
  <action>
    - Replace the "Configuración" panel body placeholder with two drop zones: "Series" (metrics) and "Análisis" (dimensions).
    - Setup `vuedraggable` components for each zone.
    - Bind `v-model` to `store.measures` and `store.dimensions`.
    - Use `item-key="fullName"`.
    - Implement an "empty state" slot within `vuedraggable` (header/footer) to display "Arrastre métrica aquí" when the list is empty.
  </action>
  <verify>
    <automated>Verify that items can be dragged from Source to Config panel and stay there.</automated>
  </verify>
  <done>Drop zones created and receiving draggable elements from the Source Panel.</done>
</task>

<task type="auto">
  <name>Task 2: Drop Validation & Duplicates Prevention</name>
  <files>dashboard-app/src/views/VisualizationConfiguratorView.vue</files>
  <action>
    - Configure the `group` property for the target `vuedraggable` components.
    - Set the `put` property to a function that prevents adding a field if it's already present in the target list (use `some(item => item.fullName === element.fullName)`).
    - Ensure only `measures` can be dropped in "Series" and only `dimensions` in "Análisis" (using the group name).
  </action>
  <verify>
    <automated>Verify that duplicate drops fail and cross-type drops are blocked.</automated>
  </verify>
  <done>Drop validation implemented correctly.</done>
</task>

<task type="auto">
  <name>Task 3: Visual Polish, States & Removal</name>
  <files>dashboard-app/src/views/VisualizationConfiguratorView.vue, dashboard-app/src/assets/main.css</files>
  <action>
    - Add CSS classes to highlight active/hovered drop zones during drag.
    - Implement a remove button (X icon) for each active field in the configuration panel.
    - Implement styles for the "Active Field" (Modern Refinement): shadow, 8px rounded corners, 8px grid alignment.
    - Ensure field removal from Config Panel doesn't affect the Source Panel list.
  </action>
  <verify>
    <automated>Verify hover states during drag and removal functionality.</automated>
  </verify>
  <done>Drop zones are visually polished and items can be removed.</done>
</task>

<task type="checkpoint:human-verify" gate="blocking">
  <what-built>A functional drag-and-drop configuration interface.</what-built>
  <how-to-verify>
    - Drag a Metric to Series.
    - Drag a Dimension to Análisis.
    - Try dragging a Metric to Análisis (should fail).
    - Try dragging the same Metric twice (should fail).
    - Reorder items within a zone.
    - Remove an item from a zone.
    - Verify that the Source Panel remains unchanged.
  </how-to-verify>
  <resume-signal>Approved</resume-signal>
</task>

</tasks>

<must_haves>
  truths:
    - "User can drag a measure from Source to Series zone."
    - "User can drag a dimension from Source to Análisis zone."
    - "User cannot drag a measure to Análisis zone."
    - "User cannot add the same field twice to the same zone."
    - "Fields in zones can be reordered."
    - "Fields in zones can be removed."
  artifacts:
    - path: "dashboard-app/src/views/VisualizationConfiguratorView.vue"
      provides: "DND interface"
  key_links:
    - from: "Source Panel"
      to: "Config Panel"
      via: "vuedraggable groups"
    - from: "Config Panel"
      to: "visualizationConfiguratorStore"
      via: "v-model binding"
</must_haves>

<success_criteria>
- Validation prevents duplicates and cross-zone drops.
- Drop zones provide visual feedback when an item is hovered over them.
- Final UI follows the Modern Refinement guidelines (8px grid, clean typography).
</success_criteria>

<output>
After completion, create `.planning/phases/phase02/phase02-02-SUMMARY.md`
</output>
