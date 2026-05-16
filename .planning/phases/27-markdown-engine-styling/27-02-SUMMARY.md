---
phase: 27-markdown-engine-styling
plan: 27-02
subsystem: frontend
tags: [notes, styling, toolbar, ui]
requires: [27-01]
provides: [on-canvas-styling]
affects: [FlowEditorCanvas.vue]
tech-stack: [vue]
key-files: [dashboard-app/src/components/editor/FlowEditorCanvas.vue]
decisions:
  - "Positioned the styling toolbar at the top of the note (using bottom: calc(100% + 8px)) for better visibility."
  - "Implemented a darkenColor helper to calculate border colors dynamically based on the note background."
metrics:
  duration: 15m
  completed_date: 2026-05-16
---

# Phase 27 Plan 02: On-Canvas Styling Toolbar Summary

Implemented a floating on-canvas styling toolbar for notes, allowing immediate customization of appearance.

## Key Changes

### Frontend (dashboard-app)

#### Styling Toolbar UI
- Added `fec-note-toolbar` component to the note body.
- Visible only when a note is selected or being edited.
- Includes:
  - **Color Palette**: 5 color options (Yellow, Blue, Green, Pink, Grey).
  - **Font Size Controls**: Plus/Minus buttons with a live size indicator.
- Styled to look like a clean, floating action bar above the note.

#### Styling Logic
- Implemented `changeNoteColor(node, color)` to update the `color` property.
- Implemented `changeNoteFontSize(node, delta)` with range protection (8px - 48px).
- Added `darkenColor(hex)` utility to generate consistent border colors for notes.
- Updated node template to bind `background`, `borderColor`, and `fontSize` to the note's properties.

## Verification Results
- Selecting a note reveals the toolbar.
- Clicking a color button (e.g., Pink #fce7f3) instantly changes the note's background and border.
- Clicking font size buttons scales the text (both in preview and edit mode).
- Proporties persist during the session (and are saved with the diagram).

## Self-Check: PASSED
- [x] Files modified: dashboard-app/src/components/editor/FlowEditorCanvas.vue
- [x] All styling controls are functional.
- [x] Limits for font size are enforced.
