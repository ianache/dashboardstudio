# Phase 2: Drag-and-Drop Core - Research

**Researched:** 2026-04-15
**Domain:** Vue 3, Vuedraggable v4, Cube.js Metadata Integration
**Confidence:** HIGH

## Summary

This research explores the implementation of a drag-and-drop interface for the Visualization Configurator using `vuedraggable` v4 (Vue 3 compatible). The core focus is on populating a "Source Panel" with Cube.js metadata (measures and dimensions) and configuring specific "Drop Zones" ("Series" and "Análisis") with validation rules that restrict item types.

**Primary recommendation:** Use separate `vuedraggable` groups (`measures` and `dimensions`) to enforce validation natively, and store full metadata objects in the `visualizationConfiguratorStore` to avoid constant lookups during preview generation.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| FR-01 | Drag-and-Drop Interface (Source Panel, Drop Zones) | Detailed `vuedraggable` v4 configuration for Source Panel and Config Panel zones. |
| FR-01 | Searchable metrics and dimensions | Logic for filtering `allMeasures` and `allDimensions` from `useCubeStore`. |
| NFR-Modern Refinement | 6-dot handle, hover states, 8px grid | UI patterns for draggable items using existing CSS variables. |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `vuedraggable` | 4.1.0 | Drag-and-drop functionality | Standard Vue wrapper for Sortable.js; v4 is the official Vue 3 version. |
| `@cubejs-client/core` | 0.35.23 | Cube.js API client | Official client for metadata and data fetching. |
| `pinia` | 2.1.7 | State management | Official Vue 3 store; handles persistence of the configuration. |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|--------------|
| `@vueuse/core` | 10.9.0 | Composition utilities | Useful for `useVModel` or specialized reactive helpers if needed. |

**Installation:**
Already installed in `package.json`. No additional packages required.

## Architecture Patterns

### Recommended Project Structure
```
src/
├── components/
│   ├── dashboard/
│   │   ├── SourcePanel.vue          # Left column: Cube selector + Measures/Dimensions
│   │   ├── ConfigPanel.vue          # Center column: Series/Analysis zones
│   │   └── DraggableItem.vue        # Common UI for draggable elements
├── stores/
│   ├── cubejs.js                    # Source of truth for Cube metadata
│   └── visualizationConfigurator.js # State for the current configuration
```

### Pattern 1: Source to Target (Clone)
**What:** Items are dragged from the Source Panel to the Config Panel. The source list remains unchanged (`pull: 'clone'`), and the target list receives a copy of the metadata object.
**When to use:** Standard for "Field Lists" in BI tools.
**Example:**
```vue
<!-- Source List -->
<draggable 
  v-model="sourceMeasures" 
  :group="{ name: 'measures', pull: 'clone', put: false }" 
  :clone="cloneItem"
  item-key="fullName"
>
  <template #item="{ element }">
    <div class="draggable-field measure">{{ element.title }}</div>
  </template>
</draggable>

<!-- Target List (Series) -->
<draggable 
  v-model="store.measures" 
  group="measures" 
  item-key="fullName"
  class="drop-zone"
>
  <template #item="{ element }">
    <div class="active-field">{{ element.title }}</div>
  </template>
</draggable>
```

### Anti-Patterns to Avoid
- **Hand-rolling DND:** Avoid using native HTML5 Drag and Drop directly; it's error-prone and lacks the sorting/grouping capabilities of `vuedraggable`.
- **String-only storage:** Don't store only the names of measures/dimensions in the target list; store the whole metadata object to avoid re-fetching titles/types for the UI.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Sorting/Reordering | Manual array splicing | `vuedraggable` | Handles edge cases, animations, and touch support. |
| Type Validation | Custom `@drop` listeners | `group` property | Built-in logic for restricting items between lists. |
| Metadata Cache | Global variables | `useCubeStore` | Already implements caching and backend synchronization. |

## Common Pitfalls

### Pitfall 1: Missing `item-key`
**What goes wrong:** Random UI glitches, items disappearing, or console errors during drag.
**Why it happens:** Vue 3 version of `vuedraggable` requires a unique key to track elements in the virtual DOM.
**How to avoid:** Always provide `:item-key="fullName"` (or any unique property).

### Pitfall 2: Collapsed Drop Zones
**What goes wrong:** Impossible to drop items into an empty list.
**Why it happens:** An empty `<div>` or `<ul>` has 0px height.
**How to avoid:** Set a `min-height` (e.g., 40px) on the `draggable` component and use the `#header` slot to show a placeholder ("Arrastre aquí").

### Pitfall 3: Duplicate Clones
**What goes wrong:** Same measure can be dragged multiple times into the same zone.
**Why it happens:** `pull: 'clone'` doesn't check for existence in the target list.
**How to avoid:** Use a `put` function in the target's `group` configuration to check if the item already exists.

## Code Examples

### Draggable Item Structure
Based on `cubejs.js` getters:
```javascript
{
  fullName: "Orders.count",   // Unique identifier
  title: "Ventas (Contador)", // Display label
  type: "number",             // Data type (from Cube)
  memberType: "measure"       // Metadata type (manually added for internal logic)
}
```

### Validation Logic (Put function)
```javascript
// Inside target draggable :group prop
:group="{
  name: 'measures',
  put: (to, from, element) => {
    // Only allow if not already in the list
    return !store.measures.some(m => m.fullName === element.fullName);
  }
}"
```

### Source Panel Population
```javascript
const cubeStore = useCubeStore()
const configuratorStore = useVisualizationConfiguratorStore()

// Computed properties for filtered metadata
const availableMeasures = computed(() => {
  if (!configuratorStore.selectedCube) return []
  return cubeStore.getMeasuresForCube(configuratorStore.selectedCube).map(m => ({
    ...m,
    fullName: m.name, // CubeJS meta uses name for fullName
    memberType: 'measure'
  }))
})
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `vuedraggable` v2 | `vuedraggable` v4 | Vue 3 release | Migration to `#item` slot and mandatory `item-key`. |
| Local component state | Pinia Store | Project wide | Better persistence and cross-component reactivity. |

## Open Questions

1. **Multi-Cube support:** Should we allow dragging fields from different cubes?
   - What we know: Current `visualizationConfiguratorStore` resets when `selectedCube` changes.
   - Recommendation: Stick to single-cube per visualization for now as it simplifies Cube.js query generation.

## Sources

### Primary (HIGH confidence)
- `dashboard-app/package.json` - Confirmed `vuedraggable` 4.1.0 version.
- `dashboard-app/src/stores/cubejs.js` - Analyzed metadata structure and getters.
- `dashboard-app/src/stores/visualizationConfigurator.js` - Analyzed target state.
- [Vuedraggable Next Documentation](https://github.com/SortableJS/vue.draggable.next) - Verified Vue 3 slot usage and `group` behavior.

### Secondary (MEDIUM confidence)
- [Sortable.js Options](https://github.com/SortableJS/Sortable) - Verified `pull: 'clone'` and `put` function behavior.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Libraries already in project and versions verified.
- Architecture: HIGH - Standard BI tool patterns for DND.
- Pitfalls: HIGH - Common issues with Vue 3 DND well-documented.

**Research date:** 2026-04-15
**Valid until:** 2026-05-15 (Standard stable ecosystem)
