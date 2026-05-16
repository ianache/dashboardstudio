---
phase: 28-advanced-interaction-persistence
plan: 28-01
subsystem: editor
tags: [frontend, refactor, notes]
requires: []
provides: [separated-notes-logic]
affects: [FlowEditorCanvas.vue]
tech-stack: [Vue 3, Markdown]
key-files: [dashboard-app/src/components/editor/FlowEditorCanvas.vue]
decisions:
  - Notes are now stored in a dedicated 'notes' array, isolated from functional 'nodes'.
  - Background rendering layer implemented for notes to ensure correct Z-ordering.
metrics:
  duration: 15m
  completed_date: 2026-05-17
---

# Phase 28 Plan 01: FlowEditorCanvas Refactor Summary

Refactored FlowEditorCanvas to properly separate Notes from functional Nodes in the data structure and rendering layers.

## Key Changes

### Separated Note Storage
- Updated `onDrop` to route 'annotations' tool category to the `notes` array instead of `nodes`.
- Implemented migration logic in `watch(diagramData)` to automatically move legacy annotations from the nodes array to the notes array upon loading.
- Set default width (240px) and height (120px) for new notes.

### Background Note Layer
- Introduced a dedicated Note rendering loop in the template, placed before the SVG connections layer.
- This ensures notes always appear behind nodes and connections.
- Removed annotation-specific conditional rendering and styling from the main functional nodes loop.

### Synchronized Interactions
- Added `onNoteMousedown` to enable dragging for notes using the existing node drag logic.
- Updated `deleteSelectedNode` to handle deletion from both nodes and notes arrays.
- Ensured double-click to edit and styling toolbar work correctly within the new data structure.

## Verification Results
- [x] Dropping a Note tool correctly populates the `notes` array.
- [x] Notes render behind functional nodes and connections.
- [x] Notes can be selected, moved, and deleted.
- [x] Legacy flows with notes in the nodes array are correctly migrated on load.
