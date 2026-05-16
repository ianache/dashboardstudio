---
gsd_state_version: 1.0
milestone: v1.4
milestone_name: Markdown Notes in Editor
current_phase: 25
status: In Progress 🛠️
last_updated: "2026-05-16T21:00:00.000Z"
progress:
  total_phases: 4
  completed_phases: 0
  total_plans: 4
  completed_plans: 0
---

# Project State: Markdown Notes in Editor

- **Status:** In Progress 🛠️
- **Current Phase:** Phase 25: Architecture & DB Extension
- **Last Action:** Updated architecture to use a dedicated background layer and separate storage for notes.

## Workflow Status
- [x] Config defined
- [x] Context created
- [ ] Research completed
- [x] Requirements finalized
- [x] Roadmap structured
- [ ] Execution complete

## Milestone: Markdown Notes in Editor
- [ ] Phase 25: Architecture & DB Extension
- [ ] Phase 26: Note Layer & Drag Logic
- [ ] Phase 27: Markdown Engine & Styling
- [ ] Phase 28: Advanced Interaction & Persistence

## Accumulated Context
### Milestone Goals
- Add a "Note" tool for canvas documentation.
- Support markdown rendering, inline editing, and custom styling.
- Enable dynamic resizing for notes.
- **New Architecture:** Notes are stored in a dedicated `flow_notes` array and rendered in the background (z-order behind everything).

### Decisions Made
- Category: "Annotations" (New).
- Palette: Classic Sticky Notes (Yellow, Blue, Green, Pink, Grey).
- Interaction: NWSE-resize via corner handle.
- Libraries: Using already installed `marked` and `dompurify`.
- **Storage:** Dedicated `flow_notes` column in the database to separate documentation from functional nodes.
- **Layering:** The `notes` array will be rendered first in the `FlowEditorCanvas.vue` DOM to ensure it sits behind SVG connections and nodes.
