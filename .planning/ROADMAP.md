# Project Roadmap: Markdown Notes in Editor

## Progress Table

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1-24. Core & UI Enhancements | 24/24 | Completed | 2026-05-16 |
| 25. Architecture & DB Extension | 0/2 | In Progress | - |
| 26. Note Layer & Drag Logic | 0/1 | Pending | - |
| 27. Markdown Engine & Styling | 0/1 | Pending | - |
| 28. Advanced Interaction & Persistence | 0/1 | Pending | - |

---

## Milestone: Markdown Notes in Editor

### Phase 25: Architecture & DB Extension
**Goal**: Extend the backend and frontend data structures to support a dedicated `notes` layer.
**Requirements**: FR-07, TR-04
**Status**: In Progress

Plans:
- [ ] 25-01-PLAN.md — Backend Schema Extension
- [ ] 25-02-PLAN.md — API & Integration

### Phase 26: Note Layer & Drag Logic
**Goal**: Implement the background layer in `FlowEditorCanvas.vue` and the logic to drop and move notes.
**Requirements**: FR-01, FR-02, FR-03, FR-08, TR-03
**Status**: Pending

### Phase 27: Markdown Engine & Styling
**Goal**: Implement inline editing with `marked.js` and the styling header (colors, font size).
**Requirements**: FR-04, FR-05, TR-01, TR-02, UI
**Status**: Pending

### Phase 28: Advanced Interaction & Persistence
**Goal**: Implement the NWSE resizing handle and ensure full persistence of the note state.
**Requirements**: FR-06, TR-05, FR-07
**Status**: Pending

---

## Phase Details

### Phase 25: Architecture & DB Extension
- [x] Add `flow_notes` column to `IntegrationFlow` model (SQLAlchemy).
- [x] Update Pydantic schemas to include `flow_notes` in responses/requests.
- [x] Create DB migration script.
- [x] Update `save_flow_diagram` endpoint to handle the separate `notes` key.
- [x] Update frontend store and API service.

### Phase 26: Note Layer & Drag Logic
- [ ] Add "Annotations" category to tool catalog.
- [ ] Modify `FlowEditorCanvas.vue` template to render `notes` array before connections.
- [ ] Implement `onNoteDrop` logic to add items to `notes` instead of `nodes`.
- [ ] Adapt drag logic to handle note movement on the canvas.

### Phase 27: Markdown Engine & Styling
- [ ] Implement `MarkdownNote` component (or inline logic).
- [ ] Add toggle state for edit/preview.
- [ ] Add the styling header with color palette and font size buttons.
- [ ] Apply "Sticky Note" CSS variants based on selected color.

### Phase 28: Advanced Interaction & Persistence
- [ ] Add NWSE resize handle to the note.
- [ ] Implement `onNoteResize` mouse tracking logic.
- [ ] Ensure `width`, `height`, `content`, `color`, and `fontSize` are all serialized and saved.
- [ ] Final polishing of Z-index and focus behavior.
