# Phase 49: Diseño Minimalista Profesional - Context

**Gathered:** 2026-06-01
**Status:** Ready for planning

<domain>
## Phase Boundary

Rediseñar el Dashboard Studio para lograr un aspecto minimalista, profesional y moderno, empleando colores neutros e iconos de alta calidad, mientras se preserva la funcionalidad existente.

</domain>

<decisions>
## Implementation Decisions

### Typography & Spacing
- Primary font: Clean Sans-Serif (standard, modern)
- Weights: Light & Airy (regular body, medium/semibold headers)
- Density: Airy / Relaxed (generous whitespace/padding)
- Headings: Subtle Hierarchy (relies on color/weight more than drastic size changes)

### Color Palette Strategy
- Background: Follow the active System Design theme (light/dark) for the primary background
- Surfaces: White on Off-White (or the dark-mode equivalent, contrasting subtle surfaces against the background)
- Accent: Soft / Muted Accent (e.g. slate blue, sage green)
- Text: Soft Dark Gray (e.g. var(--on-surface-variant)) to avoid harsh pure black

### Iconography
- Style: Light Line-Art Icons (e.g., Lucide, Phosphor) instead of current Material icons
- Stroke: Standard Stroke (1.5px/2px) for crisp readability
- Color: Match Text Color by default (var(--on-surface-variant))
- Sizing: Standard & Aligned (20px/24px) consistent with text

### Component Shapes & Elevation
- Corners: Subtle Rounding (6px - 8px) for a friendly, modern look
- Elevation: Soft / Diffused Shadows for floating elements
- Separation: Borders over Shadows for standard cards/panels (subtle 1px border)
- Inputs/Buttons: Outlined style with transparent/white backgrounds and subtle borders

### Claude's Discretion
- Exact mapping of these decisions to existing CSS tokens or Tailwind configuration
- Handling of interactive states (hover/focus)

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- The application currently uses a robust CSS Custom Property system established in Phase 47/48 (`var(--primary)`, `var(--on-surface)`, etc.).

### Established Patterns
- Colors are handled via scoped CSS tokens and the `data-theme` attribute on the HTML element.
- Tailwind CSS is used alongside scoped tokens.

### Integration Points
- Shell layer components (SideMenu, TopBar, AppLayout) and existing common components (like `Card` and `MIcon.vue`) will be the primary targets for visual updates.

</code_context>

<specifics>
## Specific Ideas

- The UI should closely match the spirit of the provided Stitch/Google design reference (clean, airy, professional).

</specifics>

<deferred>
## Deferred Ideas

- None — discussion stayed within phase scope.

</deferred>

---

*Phase: 49-dashboard-designer-styling*
*Context gathered: 2026-06-01*