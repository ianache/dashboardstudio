<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
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

### Deferred Ideas (OUT OF SCOPE)
- None — discussion stayed within phase scope.
</user_constraints>

# Phase 49: Diseño Minimalista Profesional - Research

**Researched:** 2026-06-01
**Domain:** Frontend UI/UX Design, CSS Custom Properties, Iconography
**Confidence:** HIGH

## Summary

The UI will transition from a Material-influenced dense look to a "Stitch/Google" airy, minimalist, and highly professional design. This involves shifting from Material font icons to `lucide-vue-next` (Light line-art icons), refining global CSS for soft shadows and consistent 8px rounding, replacing harsh black with `var(--on-surface-variant)`, and applying an "outlined" aesthetic to inputs and buttons. 

**Primary recommendation:** Centralize the icon migration by turning `MIcon.vue` into an adapter for `lucide-vue-next` components mapped via a dictionary, avoiding a 50+ file refactor. Refine `assets/main.css` to update shadow definitions, border radii, and button styles.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| lucide-vue-next | ^0.358.0 | Line-art icon library | Matches "Light Line-Art Icons" requirement, clean modern aesthetic, Vite-friendly tree shaking. |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Inter & Plus Jakarta Sans | Google Fonts | Primary Sans-Serif | Already imported in `index.html`. Perfect fit for the "Clean Sans-Serif" requirement. |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| lucide-vue-next | Phosphor Icons (vue) | Both are excellent, but Lucide has stronger default compatibility with minimalist enterprise designs and standard strokes. |

**Installation:**
```bash
npm install lucide-vue-next
```

## Architecture Patterns

### Recommended Project Structure
```
dashboard-app/src/
├── components/common/
│   ├── MIcon.vue        # Update as an adapter
│   └── IconMap.js       # New: Dictionary mapping Material strings to Lucide
├── assets/
│   └── main.css         # Target for global token/style refinements
```

### Pattern 1: Icon Adapter (`MIcon.vue` rewrite)
**What:** Instead of replacing `<MIcon icon="grid_view" />` across 54 files, rewrite `MIcon.vue` to map material string names to dynamically loaded Lucide components.
**When to use:** When replacing a legacy icon font in a codebase with deep usage without causing massive regressions.
**Example:**
```vue
<template>
  <component 
    :is="resolvedIcon" 
    :size="size" 
    :stroke-width="strokeWidth" 
    class="m-icon-adapter" 
    aria-hidden="true" 
  />
</template>

<script setup>
import { computed } from 'vue'
import { HelpCircle, LayoutGrid, Settings, MoreVertical } from 'lucide-vue-next'
import { iconMap } from './IconMap.js'

const props = defineProps({
  icon: { type: String, required: true },
  size: { type: Number, default: 20 },
  weight: { type: Number, default: 400 }
})

const strokeWidth = computed(() => props.weight > 400 ? 2 : 1.5)
const resolvedIcon = computed(() => iconMap[props.icon] || HelpCircle)
</script>
```

### Pattern 2: Subdued Global Shadows & Borders
**What:** Update root CSS properties in `assets/main.css` to enforce "Borders over Shadows" and "Subtle Rounding".
**Example:**
```css
/* Update in main.css :root and data-theme="light" */
--shadow: 0 2px 4px rgba(15, 23, 42, 0.04);
--shadow-md: 0 4px 6px rgba(15, 23, 42, 0.05);
--radius-md: 0.5rem; /* Ensure 8px */
```

### Pattern 3: Outlined Inputs & Buttons
**What:** Move away from heavily filled backgrounds to transparent/white backgrounds with subtle borders for primary interactivity.

### Anti-Patterns to Avoid
- **Massive Refactor:** Do not hunt and manually replace every `<MIcon>` tag in the project. Map them.
- **Hardcoding Colors:** Do not use Tailwind color classes (`text-gray-500`). Stick to `--on-surface-variant` and `--outline` classes as per Phase 48 context.
- **Removing Existing Themes:** Ensure changes apply gracefully to `[data-theme="light"]` and the default dark theme.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Icon Component | A custom SVG wrapper parsing paths | `lucide-vue-next` | Enterprise standard, ensures stroke-width scaling, accessibility handling out-of-the-box. |

**Key insight:** Migrating to line-art icons fundamentally changes the optic weight. Rely on `lucide-vue-next`'s `stroke-width` prop mapped from the legacy `weight` prop to maintain visual balance.

## Common Pitfalls

### Pitfall 1: Unmapped Icons Crash
**What goes wrong:** A dynamically injected icon name (e.g., from `toolCatalog.js` or `connectionTypes.js`) doesn't exist in the new Lucide map, rendering blank or crashing.
**Why it happens:** Material symbols use thousands of snake_case strings.
**How to avoid:** Always use a fallback icon (e.g., `HelpCircle` or `Image`) in the `MIcon.vue` adapter for unknown strings. 

### Pitfall 2: Overriding Phase 48 Theme Alignment
**What goes wrong:** Hardcoding hex codes while restyling buttons and cards.
**Why it happens:** Forgetting the platform relies on CSS custom variables (`var(--primary)`, `var(--surface)`) toggled via `data-theme`.
**How to avoid:** Always use the defined CSS variables in `assets/main.css` when building the new outlined input/button styles.

## Code Examples

### Outlined Button Pattern
```css
/* Source: Derived from Phase 49 Design Constraints & Phase 48 Themes */
.btn-primary { 
  background: transparent; 
  color: var(--primary); 
  border-color: var(--primary); 
}
.btn-primary:hover:not(:disabled) { 
  background: color-mix(in srgb, var(--primary) 10%, transparent);
}

.btn-secondary {
  background: transparent;
  color: var(--on-surface-variant);
  border-color: var(--outline);
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Material Symbols Font | Lucide Components | 2024-2025 | Eliminates heavy font load, much crisper and neutral "startup" aesthetic. |
| Deep Shadows for Elevation | Borders over Shadows | 2023-2025 | Creates an "airy" feel; shadows only used for transient overlays (modals/dropdowns). |

**Deprecated/outdated:**
- `Material Symbols Font`: Replaced by `lucide-vue-next` dynamic component injection to reduce bundle size and enforce minimal style.

## Open Questions

1. **Complete Icon Map Dictionary**
   - What we know: There are ~35 distinct string usages of icons (e.g., `grid_view`, `settings`, `account_tree`).
   - What's unclear: The exact 1:1 mapping equivalent in Lucide.
   - Recommendation: Create `IconMap.js` and manually map the ~35 used ones during the implementation phase. Unknown ones fallback to `HelpCircle`.

## Sources

### Primary (HIGH confidence)
- `assets/main.css` - Analyzed current variable definitions and component classes
- `MIcon.vue` - Analyzed legacy icon API
- `lucide-vue-next` official docs - API for dynamic icon loading and stroke manipulation

### Secondary (MEDIUM confidence)
- Project Git History (`STATE.md`) - Verified Phase 48 established token-first architecture.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Lucide is the exact line-art implementation of the visual requirement.
- Architecture: HIGH - Adapter pattern is standard for large-scale icon migration.
- Pitfalls: HIGH - Documented based on actual dynamic usages in `dashboard-app`.

**Research date:** 2026-06-01
**Valid until:** 2026-07-01