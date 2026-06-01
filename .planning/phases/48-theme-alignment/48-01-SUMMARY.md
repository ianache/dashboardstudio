---
phase: 48-theme-alignment
plan: "01"
subsystem: ui
tags: [vue3, css-tokens, theming, design-system, sidemenu, topbar]

# Dependency graph
requires:
  - phase: 47-multi-system-design
    provides: "Theme toggle infrastructure — uiStore.setTheme(), data-theme on html, all CSS tokens in :root and [data-theme='light']"
provides:
  - "SideMenu.vue fully token-aware — zero hardcoded hex/rgba in scoped CSS or template inline styles"
  - "TopBar.vue fully token-aware — zero legacy tokens (--text, --text-secondary, --primary-light), zero hardcoded backgrounds"
  - "AppLayout.vue verified clean — already uses CSS tokens"
affects: [48-theme-alignment]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Inline style='color:#...' replaced with semantic scoped CSS classes (.icon-on-primary, .icon-muted)"
    - "Legacy undefined tokens (--text, --text-secondary) fully replaced with Material You tokens (--on-surface, --on-surface-variant)"
    - "Dark rgba hover states (rgba(15,23,42,0.6)) replaced with var(--surface-container-high) for bidirectional theme support"

key-files:
  created: []
  modified:
    - "dashboard-app/src/components/layout/SideMenu.vue"
    - "dashboard-app/src/components/layout/TopBar.vue"

key-decisions:
  - "nav-sub-action uses var(--primary) + opacity instead of rgba(96,165,250,0.8) — token-aware approach, works in both themes"
  - "nav-arrow and nav-section-title: use var(--on-surface-variant) + opacity: 0.6 — cleaner than rgba white"
  - "box-shadow on side-menu: replaced rgba(0,0,0,0.3) with var(--shadow-md) — consistent with design system"
  - "action-badge/user-avatar/dp-avatar color: #fff replaced with var(--on-primary-container) — adapts to primary color in light theme"
  - "AppLayout.vue already clean — no changes needed, only verification performed"

patterns-established:
  - "Pattern: Semantic icon classes (.icon-on-primary, .icon-muted) in scoped CSS instead of inline style attributes"
  - "Pattern: Legacy tokens --text/--text-secondary must be replaced with --on-surface/--on-surface-variant in all components"

requirements-completed: [THEME-01]

# Metrics
duration: 6min
completed: 2026-06-01
---

# Phase 48 Plan 01: Shell Layer Theme Token Migration Summary

**SideMenu, TopBar, and AppLayout fully migrated to CSS design tokens — shell layer responds to light/dark toggle instantly with zero hardcoded colors remaining**

## Performance

- **Duration:** 6 min
- **Started:** 2026-06-01T20:24:02Z
- **Completed:** 2026-06-01T20:30:05Z
- **Tasks:** 3 (2 with changes, 1 verification-only)
- **Files modified:** 2

## Accomplishments

- Replaced 18+ hardcoded color values in SideMenu.vue (hex, rgba) with CSS custom property tokens
- Replaced all legacy `--text` / `--text-secondary` / `--primary-light` references in TopBar.vue with Material You tokens
- Removed all `style="color:#..."` inline attributes from templates, replaced with semantic scoped classes
- Verified AppLayout.vue was already clean — confirmed uses only `var(--bg)` and layout variables
- Shell layer passes both overall verification commands (zero matches on legacy tokens, zero hardcoded backgrounds)

## Task Commits

1. **Task 1: Migrate SideMenu.vue** - `ad9a0c0` (feat)
2. **Task 2: Migrate TopBar.vue** - `2aea11f` (feat)
3. **Task 3: Verify AppLayout.vue** - no commit (already clean, no changes)

## Files Created/Modified

- `dashboard-app/src/components/layout/SideMenu.vue` - All hardcoded hex/rgba replaced with design tokens; added .icon-on-primary and .icon-muted semantic classes
- `dashboard-app/src/components/layout/TopBar.vue` - All legacy --text tokens and hardcoded backgrounds replaced; dropdown backgrounds, alert states, hover states now token-aware

## Decisions Made

- `nav-sub-action` color: replaced `rgba(96,165,250,0.8)` + `#60a5fa` hover with `var(--primary)` + opacity — keeps link-blue feel while being theme-aware
- `.nav-arrow` and `.nav-section-title`: used `var(--on-surface-variant); opacity: 0.6` instead of `rgba(255,255,255,0.25)` — works in both light and dark themes
- `box-shadow` on `.side-menu`: replaced `rgba(0,0,0,0.3)` with `var(--shadow-md)` — uses the design system's pre-defined shadow
- Avatar and badge `color: #fff` replaced with `var(--on-primary-container)` — adapts to theme since `--primary` (bg) also changes

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Replaced additional rgba/hex values not explicitly listed in plan**
- **Found during:** Task 1 verification
- **Issue:** `.side-menu box-shadow: rgba(0,0,0,0.3)` and `.nav-sub-action rgba(96,165,250,0.8)` / `#60a5fa` were not in the plan's CSS rules list but were caught by the verification grep
- **Fix:** Replaced with `var(--shadow-md)` and `var(--primary)` + opacity respectively
- **Files modified:** dashboard-app/src/components/layout/SideMenu.vue
- **Verification:** grep returned zero matches after fix
- **Committed in:** ad9a0c0 (Task 1 commit)

**2. [Rule 1 - Bug] Fixed color: #fff on avatar/badge elements in TopBar**
- **Found during:** Task 2 post-verification grep check
- **Issue:** `.action-badge`, `.user-avatar`, `.dp-avatar` used `color: #fff` — would not adapt to light theme
- **Fix:** Replaced with `var(--on-primary-container)` — the correct on-color for primary-colored surfaces
- **Files modified:** dashboard-app/src/components/layout/TopBar.vue
- **Verification:** grep returned zero matches after fix
- **Committed in:** 2aea11f (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (both Rule 1 — missed instances caught by verification grep)
**Impact on plan:** Both fixes necessary for complete theme correctness. No scope creep.

## Issues Encountered

None — all replacements mapped cleanly to existing design tokens.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- Shell layer (SideMenu, TopBar, AppLayout) is fully theme-aware
- Plans 48-02, 48-03, 48-04 (views and common components) were executed in a prior session
- Phase 48 is effectively complete — all in-scope files migrated

---
*Phase: 48-theme-alignment*
*Completed: 2026-06-01*
