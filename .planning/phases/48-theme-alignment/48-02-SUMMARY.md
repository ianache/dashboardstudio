---
phase: 48-theme-alignment
plan: 02
subsystem: ui
tags: [vue3, css-tokens, theme, light-dark, tailwind-migration]

# Dependency graph
requires:
  - phase: 47-multi-system-design
    provides: CSS custom property token system (--on-surface, --card-bg, --outline-variant, etc.) via data-theme on html element
  - phase: 48-01-PLAN.md
    provides: Shell layer token migration (AppLayout, SideMenu, TopBar)
provides:
  - ConnectionsView.vue fully token-aware — cv-card, skeleton, empty state, confirm dialog
  - LoginView.vue fully token-aware — adaptive page background and card background
  - SettingsView.vue fully token-aware — no legacy --text tokens
  - DashboardDesignerView.vue fully token-aware — no legacy --text tokens, modals use dv-* classes
affects: [48-03-PLAN.md, 48-04-PLAN.md]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Tailwind utility class replacement via scoped CSS helper classes (page-title, cv-*, dv-*)"
    - "color-mix(in srgb, ...) for transparent tints of semantic tokens"
    - "Intentional brand colors (fill='#1890ff' SVG) explicitly left unchanged"

key-files:
  created: []
  modified:
    - dashboard-app/src/views/ConnectionsView.vue
    - dashboard-app/src/views/SettingsView.vue
    - dashboard-app/src/views/DashboardDesignerView.vue
    - dashboard-app/src/views/LoginView.vue

key-decisions:
  - "color-mix(in srgb, var(--success) 15%, transparent) used for badge tints instead of hardcoded light colors"
  - "SVG fill='#1890ff' in LoginView left intentionally as brand color per RESEARCH.md"
  - "#fff on primary/error backgrounds (contrast text) left unchanged — these are correct for all themes"
  - "Modal dialogs in DashboardDesignerView refactored with dv-* scoped classes rather than inline Tailwind utilities"

patterns-established:
  - "dv-* prefix for DashboardDesignerView component-level token helpers"
  - "cv-* prefix for ConnectionsView component-level token helpers"
  - "All surface containers use var(--surface-container) / var(--surface-container-high) tokens"
  - "Error states use var(--error-container) background with var(--error) text/border"

requirements-completed: [THEME-01]

# Metrics
duration: 35min
completed: 2026-06-01
---

# Phase 48 Plan 02: Theme Alignment — Views Summary

**Four heavy views (ConnectionsView, SettingsView, DashboardDesignerView, LoginView) migrated from hardcoded Tailwind utilities and legacy --text tokens to CSS custom property design tokens — zero hardcoded color values in template or scoped CSS.**

## Performance

- **Duration:** 35 min
- **Started:** 2026-06-01T19:24:17Z
- **Completed:** 2026-06-01T19:59:00Z
- **Tasks:** 3
- **Files modified:** 4

## Accomplishments
- ConnectionsView: ~30 hardcoded instances replaced — cv-card, skeleton loaders, empty state, confirm dialog, action buttons all use token variables
- SettingsView and DashboardDesignerView: all `var(--text)` / `var(--text-secondary)` legacy tokens replaced + remaining hex surface colors updated
- LoginView: standalone page fully adaptive — gradient background, card background, and spinner all use theme tokens
- DashboardDesignerView modals (New, Import, Delete, AI Assist) refactored from inline Tailwind utility classes to scoped `dv-*` CSS helper classes

## Task Commits

1. **Task 1: Migrate ConnectionsView.vue** - `b081581` (feat)
2. **Task 2: Migrate SettingsView.vue and DashboardDesignerView.vue** - `898c044` (feat)
3. **Task 3: Migrate LoginView.vue** - `48c0291` (feat)

## Files Created/Modified
- `dashboard-app/src/views/ConnectionsView.vue` — cv-* token-aware scoped classes; no hardcoded hex in CSS or template
- `dashboard-app/src/views/SettingsView.vue` — all --text legacy tokens replaced; surface/card/error containers tokenized
- `dashboard-app/src/views/DashboardDesignerView.vue` — --text tokens replaced; modals refactored with dv-* helpers; Assign Users modal fully tokenized
- `dashboard-app/src/views/LoginView.vue` — gradient background replaced with var(--bg); card and spinner use theme tokens

## Decisions Made
- `color-mix(in srgb, var(--token) 15%, transparent)` used to produce transparent tints from semantic tokens (success badge bg, primary ring) without hardcoding new hex values
- SVG logo `fill="#1890ff"` in LoginView left as-is — explicitly listed as intentional brand color in RESEARCH.md
- `#fff` on colored avatar/badge backgrounds (`.profile-avatar color:#fff`) left unchanged — these are correct contrast colors on primary/error backgrounds for both light and dark themes
- DashboardDesignerView modals had extensive inline Tailwind classes; used scoped CSS helper classes (dv-*) rather than applying utilities directly, aligning with the project "no external CSS framework" convention

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Extended scope to modal dialogs in DashboardDesignerView**
- **Found during:** Task 2 (DashboardDesignerView.vue)
- **Issue:** Plan specified replacing "text-slate-* on page header" but the file had extensive Tailwind color classes inside 4 modal dialogs (New, Import, Delete, AI Assist) that also failed the success criterion
- **Fix:** Applied same utility-class-to-scoped-CSS pattern to all modal dialogs; created dv-modal, dv-modal-header-row, dv-modal-footer, dv-modal-title, dv-form-input, etc.
- **Files modified:** dashboard-app/src/views/DashboardDesignerView.vue
- **Verification:** grep for text-slate-|bg-white|bg-slate-|border-slate- returns zero matches
- **Committed in:** 898c044 (Task 2 commit)

**2. [Rule 1 - Bug] Extended scope to Assign Users Modal in DashboardDesignerView**
- **Found during:** Task 2
- **Issue:** Same as above — the Assign Users modal had ~20 hardcoded hex values (#0f172a, #64748b, #3b82f6, etc.)
- **Fix:** Replaced all hex values with equivalent semantic tokens (--primary, --on-surface, --on-surface-variant, --error-container, etc.)
- **Files modified:** dashboard-app/src/views/DashboardDesignerView.vue
- **Verification:** No remaining hex values in the assign modal styles
- **Committed in:** 898c044 (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (both Rule 1 - scope needed to meet the plan's own success criterion)
**Impact on plan:** All auto-fixes required to satisfy the zero-hardcoded-color success criterion stated in the plan.

## Issues Encountered
- None — straightforward migration with clear token mappings from RESEARCH.md

## User Setup Required
None — no external service configuration required.

## Next Phase Readiness
- All four views are fully token-aware and will adapt correctly to light/dark theme toggle
- Ready for 48-03 (remaining views) and 48-04 (components) phases
- Pattern established: cv-*/dv-* scoped helper class approach for view-level token bridges

---
*Phase: 48-theme-alignment*
*Completed: 2026-06-01*
