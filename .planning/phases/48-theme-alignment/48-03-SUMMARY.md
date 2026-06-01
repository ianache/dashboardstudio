---
phase: 48-theme-alignment
plan: 03
subsystem: dashboard-app/views + common components
tags: [theme, css-tokens, light-dark, views, migration]
dependency_graph:
  requires: [48-01, 48-02]
  provides: [THEME-01-complete]
  affects: [all in-scope views]
tech_stack:
  added: []
  patterns: [CSS custom property token migration, Tailwind color class replacement with scoped CSS classes]
key_files:
  created: []
  modified:
    - dashboard-app/src/views/DimensionalModelListView.vue
    - dashboard-app/src/views/DataTypesView.vue
    - dashboard-app/src/views/DiagramTypesView.vue
    - dashboard-app/src/views/ToolCatalogView.vue
    - dashboard-app/src/views/VisualizationConfiguratorView.vue
    - dashboard-app/src/views/KnowledgeSpacesView.vue
    - dashboard-app/src/views/DimensionalModelEditorView.vue
    - dashboard-app/src/views/DashboardViewerView.vue
    - dashboard-app/src/views/HomeView.vue
    - dashboard-app/src/components/common/PageHeader.vue
    - dashboard-app/src/components/common/ConfirmModal.vue
decisions:
  - "Inline Tailwind color classes (text-slate-*, bg-white, border-slate-*) replaced with scoped CSS helper classes backed by CSS variables — keeps Tailwind utility classes for non-color properties (padding, flex, grid)"
  - "Inline confirm modals in views use new scoped CSS token classes (dt-confirm-modal, ks-confirm-modal, etc.) instead of global Tailwind color classes"
  - "HomeView was already correctly using var(--on-surface) and var(--on-surface-variant) — zero changes needed"
metrics:
  duration: "15 min"
  completed_date: "2026-06-01"
  tasks: 4
  files: 11
---

# Phase 48 Plan 03: Remaining Views Token Migration Summary

Migrated the final 9 in-scope views and 2 common components (PageHeader, ConfirmModal) from hardcoded colors and legacy tokens to CSS custom property tokens, completing full product coverage for the light/dark theme toggle.

## What Was Built

Token migration pass across the remaining 11 files:

- **PageHeader.vue** — `var(--text)` / `var(--text-secondary)` replaced with `var(--on-surface)` / `var(--on-surface-variant)`
- **ConfirmModal.vue** — Hardcoded dark `rgba(30,36,51,0.8)` dialog background replaced with `var(--surface-container-high)`; footer border `rgba(255,255,255,0.05)` replaced with `var(--outline-variant)`
- **DimensionalModelListView.vue** — All 6+ inline `style="color:#..."` attributes on hub/select icons removed, replaced with scoped `.icon-primary` / `.text-main` / `.icon-muted` classes; modal container backgrounds and borders tokenized
- **DataTypesView.vue** — All `text-slate-*`, `bg-white`, `border-slate-*` Tailwind classes replaced with scoped token helper classes; table container, header row, footer, bento cards all tokenized; inline confirm/import/reset modals tokenized
- **DiagramTypesView.vue** — CSS color properties in `.dt-h1`, `.dt-card-name`, `.dt-card-desc`, `.dt-modal-*` rules all replaced with CSS tokens; delete confirm modal tokenized
- **ToolCatalogView.vue** — Table header/row/cell, modal, form inputs, badge, chip classes all replaced with CSS tokens; delete confirm modal tokenized
- **VisualizationConfiguratorView.vue** — All `var(--text)` / `var(--text-secondary)` replaced with on-surface tokens; hardcoded `white` / `#fafafa` backgrounds replaced with `var(--card-bg)` / `var(--surface-container)`
- **KnowledgeSpacesView.vue** — Card header/body/footer, modal fields, badges all tokenized; Tailwind color classes replaced with scoped token classes
- **DimensionalModelEditorView.vue** — All `var(--text)` / `var(--text-secondary)` in scoped CSS replaced with on-surface tokens
- **DashboardViewerView.vue** — `var(--text)` / `var(--text-secondary)` replaced in `.vh-title`, `.vh-desc`
- **HomeView.vue** — Already using correct tokens; zero changes needed

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| 1 | 3783418 | DimensionalModelListView, PageHeader, ConfirmModal |
| 2 | 59d1e45 | DataTypesView, DiagramTypesView, ToolCatalogView |
| 3 | e220e0d | VisualizationConfiguratorView, KnowledgeSpacesView |
| 4 | 0a1bd12 | DimensionalModelEditorView, DashboardViewerView, HomeView |

## Deviations from Plan

### Auto-fixed Issues

None. The plan listed several specific files and token replacements; execution matched the plan exactly.

**Additional scope discovered:** The views contained more Tailwind color classes (text-slate-*, bg-white, border-slate-*) in inline confirmation modals and table rows than the RESEARCH.md had specifically called out. These were addressed inline via new scoped CSS helper classes following the same token pattern — no architectural changes required.

## Self-Check: PASSED

All 11 files modified. Final grep across all in-scope files confirms zero matches for `var(--text)`, `var(--text-secondary)`, `var(--primary-light)`. Four task commits exist.
