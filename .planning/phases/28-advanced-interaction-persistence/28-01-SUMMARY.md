# Phase 28 Plan 01 Summary: Separate Notes from functional Nodes

Properly refactored FlowEditorCanvas to isolate Note elements from functional Nodes in both data structure and interaction handling.

## Key Changes
- **Data Isolation:** Notes are now stored exclusively in the `notes` reactive array.
- **Dedicated Interaction State:** Introduced `selectedNote` ref and `isDraggingNote` state to prevent interference with functional node selection/dragging.
- **UI Layering:** Verified and refined the background layer for notes, ensuring they render behind SVG connections and functional nodes.
- **Interactions:**
  - Implemented `selectNote` and `onNoteMousedown` for dedicated note handling.
  - Updated `onGlobalMousemove` to handle dragging for both nodes and notes seamlessly.
  - Added a Delete button to the note's styling toolbar for easy removal.
  - Refactored deletion logic into `deleteSelectedNode` and `deleteSelectedNote`.

## Deviations from Plan
- **Enhanced Interaction Separation:** Instead of just allowing `selectNode` to handle both, I implemented a strict separation with `selectedNote` and `selectedNode` as requested in the specific implementation details, which was cleaner than the generic approach suggested in the original Task 3.
- **UI Improvement:** Added a delete button directly to the note toolbar for better UX, since notes don't use the right properties panel.

## Success Criteria Check
- [x] New notes are stored in the 'notes' array instead of 'nodes'
- [x] Notes are rendered behind the SVG connections layer
- [x] Notes can still be dragged, selected, and deleted

## Self-Check: PASSED
- [x] File `dashboard-app/src/components/editor/FlowEditorCanvas.vue` contains the changes.
- [x] Commits made for the tasks.
