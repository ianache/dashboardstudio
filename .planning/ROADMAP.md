# Project Roadmap: Markdown Notes in Editor

## Progress Table

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1-24. Core & UI Enhancements | 24/24 | Completed | 2026-05-16 |
| 25. Architecture & DB Extension | 2/2 | Completed | 2026-05-16 |
| 26. Note Layer & Drag Logic | 2/2 | Completed | 2026-05-16 |
| 27. Markdown Engine & Styling | 2/2 | Completed | 2026-05-16 |
| 28. Advanced Interaction & Persistence | 2/2 | Complete   | 2026-05-16 |

---

## Milestone: Markdown Notes in Editor

### Phase 25: Architecture & DB Extension
**Goal**: Extend the backend and frontend data structures to support a dedicated `notes` layer.
**Requirements**: FR-07, TR-04
**Status**: Completed (2026-05-16)

Plans:
- [x] 25-01-PLAN.md — Backend Schema Extension
- [x] 25-02-PLAN.md — API & Integration

### Phase 26: Note Layer & Drag Logic
**Goal**: Implement the background layer in `FlowEditorCanvas.vue` and the logic to drop and move notes.
**Requirements**: FR-01, FR-02, FR-03, FR-08, TR-03
**Status**: Completed (2026-05-16)

Plans:
- [x] 26-01-PLAN.md — Register Note tool and Annotations category
- [x] 26-02-PLAN.md — Implement canvas background layer and drag logic

### Phase 27: Markdown Engine & Styling
**Goal**: Implement inline editing with `marked.js` and the styling header (colors, font size).
**Requirements**: FR-04, FR-05, TR-01, TR-02, UI
**Status**: Completed (2026-05-16)

Plans:
- [x] 27-01-PLAN.md — Markdown Rendering & Inline Editing
- [x] 27-02-PLAN.md — On-Canvas Styling Toolbar

### Phase 28: Advanced Interaction & Persistence
**Goal**: Implement the NWSE resizing handle and ensure full persistence of the note state.
**Requirements**: FR-06, TR-05, FR-07
**Status**: Pending

Plans:
- [ ] 28-01-PLAN.md — Note Layer Isolation & Selection
- [ ] 28-02-PLAN.md — Dynamic NWSE Resizing Logic

---

## Phase Details

### Phase 25: Architecture & DB Extension
- [x] Add `flow_notes` column to `IntegrationFlow` model (SQLAlchemy).
- [x] Update Pydantic schemas to include `flow_notes` in responses/requests.
- [x] Create DB migration script.
- [x] Update `save_flow_diagram` endpoint to handle the separate `notes` key.
- [x] Update frontend store and API service.

### Phase 26: Note Layer & Drag Logic
- [x] Add "Annotations" category to tool catalog.
- [x] Modify `FlowEditorCanvas.vue` template to render `notes` array before connections.
- [x] Implement `onNoteDrop` logic to add items to `notes` instead of `nodes`.
- [x] Adapt drag logic to handle note movement on the canvas.

### Phase 27: Markdown Engine & Styling
- [x] Implement inline editing with `marked.js` and `dompurify`.
- [x] Add toggle state for edit/preview (double-click to edit).
- [x] Add the styling header with color palette and font size buttons.
- [x] Apply "Sticky Note" CSS variants based on selected color.

### Phase 28: Advanced Interaction & Persistence
- [ ] Refactor `onDrop` to separate notes into the dedicated `notes` array.
- [ ] Render notes in a dedicated layer before the SVG connection layer.
- [ ] Add NWSE resize handle to the note.
- [ ] Implement `onNoteResize` mouse tracking logic with 100x100 min-size.
- [ ] Ensure `width`, `height`, `content`, `color`, and `fontSize` are all serialized and saved.
- [ ] Final polishing of Z-index and focus behavior.
