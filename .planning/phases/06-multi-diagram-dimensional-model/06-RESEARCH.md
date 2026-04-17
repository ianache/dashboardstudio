# Phase 6: Multi-diagram Dimensional Model - Research

**Researched:** 2026-04-17
**Domain:** Vue 3 canvas editor — multi-diagram / sub-diagram UX on top of existing DimensionalModelEditorView
**Confidence:** HIGH (codebase is fully readable; requirements are explicit in plans/FEAT03.md)

---

## Summary

Phase 6 extends the existing Dimensional Model editor with a **multi-diagram** concept: every model keeps one canonical "main diagram" that always contains all nodes and relationships, plus N optional "sub-diagrams" that show a user-chosen subset of those same nodes. All diagrams inside one model share the **same node/relationship objects** — editing a node's name or fields in any diagram updates it everywhere. Only the visual placement (x, y positions) and the membership in a given diagram are diagram-local.

The current editor (`DimensionalModelEditorView.vue`) already manages nodes and relationships through `useDimensionalModelStore`, which persists data to the FastAPI/PostgreSQL backend at `/api/v1/dimensional-models/{id}`. The entire model is stored as two JSON columns (`nodes`, `relationships`). Phase 6 adds a third concept — **diagrams** — as a new JSON structure inside the model. No new backend endpoints are required; the existing PUT endpoint accepts arbitrary JSON for `nodes` and `relationships`, and the `diagrams` array will be added to the same payload.

The most important architectural decision is the **node-reference model**: each diagram holds `diagramNodes[]` that are `{ nodeId, x, y }` records pointing to canonical nodes by ID. The canonical node data (name, fields, type) lives in `model.nodes[]` and is looked up at render time. This avoids duplicating field definitions across diagrams.

**Primary recommendation:** Add a `diagrams` array to the model data structure, implement a diagram tab bar in the editor toolbar, and refactor the canvas rendering to use the active diagram's `diagramNodes[]` for positions while resolving canonical node data from `model.nodes[]`. The right-side properties panel and all existing field-editing logic remain unchanged.

---

<phase_requirements>
## Phase Requirements

Inferred from `plans/FEAT03.md` (no formal IDs assigned yet):

| ID (inferred) | Description | Research Support |
|---------------|-------------|-----------------|
| MD-01 | Every model has one permanent "main diagram" containing all nodes; cannot be deleted | Node-reference architecture; main diagram auto-syncs from model.nodes |
| MD-02 | Users can create, rename, and delete sub-diagrams | DiagramTabBar component + store actions |
| MD-03 | Sub-diagrams display a subset of nodes; user adds/removes nodes per diagram | diagramNodes[] membership pattern |
| MD-04 | Sub-diagrams are visually distinct (different background, border, or header color) | CSS `--diagram-bg` variable on canvas wrapper |
| MD-05 | Drag-and-drop of nodes between diagrams | Existing mousedown/drag pattern; cross-diagram move means removing from one diagramNodes[] and adding to another |
| MD-06 | Editing a node (name, fields) in any diagram propagates to all other diagrams | Shared canonical model.nodes[] — no change to field edit logic |
| MD-07 | Canvas click on empty area opens a side panel to rename the diagram and edit its description (Markdown-renderable) | Sidebar panel "Diagram Properties"; marked-js or similar for MD preview |

</phase_requirements>

---

## Standard Stack

### Core (already in project — no new installs needed)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Vue 3 | ^3.4 | Component framework | Project standard |
| Pinia | ^2.1 | State management | Project standard; `useDimensionalModelStore` already handles model mutations |
| vue-router | ^4.3 | Routing | Already in use |
| FastAPI + SQLAlchemy | existing backend | Persisting model JSON | PUT endpoint already accepts `nodes`/`relationships` JSON |

### Supporting (new additions)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| marked | ^12.x | Markdown rendering for diagram description | MD-07 requires Markdown preview in properties panel |
| DOMPurify | ^3.x | Sanitize marked HTML output | Always pair with marked to prevent XSS |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| marked + DOMPurify | vue-markdown-it | vue-markdown-it is heavier; marked is already a transitive dep of many tools and is lighter |
| Custom node-reference architecture | Duplicating full node data per diagram | Duplication causes sync bugs when a field is renamed; reference pattern is the correct choice |
| New backend endpoints for diagrams | Extending existing model JSON payload | New endpoints add migration + schema work; JSON extension is zero-migration and backend already supports it |

**Installation (only new deps):**
```bash
cd dashboard-app
npm install marked dompurify
```

---

## Architecture Patterns

### Updated Data Model

The canonical model structure gains a `diagrams` array:

```javascript
// Model stored in backend (nodes/relationships/diagrams are all JSON columns)
{
  id: string,
  name: string,
  description: string,
  is_global: boolean,
  nodes: [
    // CANONICAL nodes — shared across all diagrams
    { id, type, name, fields[], x, y, globalRef }
  ],
  relationships: [
    // Unchanged — always scoped to model, shown in diagrams where both endpoints are present
    { id, fromNodeId, toNodeId, cardinality }
  ],
  diagrams: [
    {
      id: string,
      name: string,
      description: string,           // Markdown text
      isMain: boolean,               // true for the one permanent main diagram
      diagramNodes: [
        { nodeId: string, x: number, y: number }  // diagram-local position overrides
      ]
    }
  ]
}
```

**Key rule:** The "main" diagram (`isMain: true`) always contains ALL nodes from `model.nodes[]`. When a new node is added globally, the main diagram gets a new `diagramNodes` entry automatically. Sub-diagrams only get nodes when the user explicitly adds them.

### Recommended Component Structure

```
src/views/DimensionalModelEditorView.vue  (refactored — active diagram context)
src/components/dimensional-model/
├── DiagramTabBar.vue      # Tab strip at top of editor; + button to create sub-diagram
├── DiagramCanvas.vue      # Extracted canvas (currently inline in EditorView); receives activeDiagram
└── DiagramPropsPanel.vue  # Side panel shown when canvas background is clicked (name + MD description)
src/stores/dimensionalModel.js            (extended with diagram actions)
```

### Pattern 1: Active Diagram Context

The editor view tracks `activeDiagramId` as a ref. All canvas rendering uses a computed `activeDiagram` that resolves from `model.diagrams[]`. Node positions are read from `activeDiagram.diagramNodes[]`, not from the canonical `node.x/node.y`. This means `node.x/node.y` on canonical nodes can be repurposed as "main diagram position" or removed in favor of a mandatory main-diagram entry in `diagramNodes[]`.

**Simplest approach (recommended):** Keep `node.x/node.y` as the main-diagram position (backward compatible with existing saved models). When a sub-diagram entry exists for a node, use its x/y override. This avoids a migration.

```javascript
// In EditorView computed
const activeDiagramNodes = computed(() => {
  if (!activeDiagram.value || activeDiagram.value.isMain) {
    // Main diagram: all canonical nodes, use node.x/node.y
    return model.value.nodes
  }
  // Sub-diagram: only nodes listed in diagramNodes[], with local positions
  return activeDiagram.value.diagramNodes
    .map(dn => {
      const canonical = model.value.nodes.find(n => n.id === dn.nodeId)
      if (!canonical) return null
      return { ...canonical, x: dn.x, y: dn.y }
    })
    .filter(Boolean)
})
```

### Pattern 2: Relationship Visibility Per Diagram

Relationships are only drawn when BOTH `fromNode` and `toNode` are present in the active diagram's `activeDiagramNodes`. Filter in a computed:

```javascript
const visibleRelationships = computed(() =>
  model.value.relationships.filter(r =>
    activeDiagramNodes.value.some(n => n.id === r.fromNodeId) &&
    activeDiagramNodes.value.some(n => n.id === r.toNodeId)
  )
)
```

### Pattern 3: DiagramTabBar

A horizontal tab strip above the canvas. Each tab = one diagram. The "+" button creates a new sub-diagram. Tabs can be double-clicked to rename inline. The main diagram tab has no delete button.

```vue
<!-- DiagramTabBar.vue -->
<div class="diagram-tab-bar">
  <div
    v-for="diag in model.diagrams"
    :key="diag.id"
    class="diagram-tab"
    :class="{ active: diag.id === activeDiagramId, 'is-main': diag.isMain }"
    @click="activeDiagramId = diag.id"
  >
    <span class="tab-label">{{ diag.name }}</span>
    <button v-if="!diag.isMain" class="tab-close" @click.stop="deleteDiagram(diag.id)">×</button>
  </div>
  <button class="tab-add" @click="createDiagram">+</button>
</div>
```

### Pattern 4: Adding Nodes to Sub-diagrams

When in a sub-diagram view, the toolbar's "+ Hecho" / "+ Dimensión" buttons add to the **canonical model** AND add a `diagramNode` entry to the active sub-diagram. The "Add Global Dim" button also adds the globalRef node to the active diagram.

For adding an **existing** canonical node to a sub-diagram (that doesn't yet include it), a secondary mechanism is needed — either a "Add existing node" button/modal, or drag from a node list panel. The simplest approach: add an "+ Add node" button in sub-diagram view that opens a checklist of canonical nodes not yet in this diagram.

### Pattern 5: Diagram Properties Panel

When the user clicks on the empty canvas background (not on a node), show a "Diagram" section in the right properties panel instead of node/relationship properties. Fields:
- Name (text input, inline edit)
- Description (textarea with a Markdown preview toggle)

```vue
<!-- In props panel -->
<div v-if="selectedDiagram && !selectedNode && !selectedRel" class="props-body">
  <div class="form-group">
    <label class="form-label">Nombre del diagrama</label>
    <input :value="activeDiagram.name" @change="renameDiagram($event.target.value)" class="form-input" />
  </div>
  <div class="form-group">
    <label class="form-label">Descripción</label>
    <textarea v-if="!mdPreview" v-model="diagDescDraft" class="form-input" rows="6" />
    <div v-else class="md-preview" v-html="sanitizedMd" />
    <button @click="mdPreview = !mdPreview">{{ mdPreview ? 'Editar' : 'Vista previa' }}</button>
  </div>
</div>
```

### Anti-Patterns to Avoid

- **Duplicating node data per diagram:** Storing fields/name/type inside each diagram's `diagramNodes` entry leads to sync bugs when a field is renamed. Always resolve from canonical `model.nodes[]`.
- **Storing activeDiagramId in Pinia:** This is UI-local state; store it as a `ref` inside the editor component, not in the global store. The store only holds persisted data.
- **Auto-saving on every node drag:** The current editor already uses an "unsaved changes" badge + manual save. Keep this pattern — don't introduce auto-save on every position change.
- **Deleting canonical nodes from a sub-diagram:** "Remove from diagram" should only remove the `diagramNode` entry, never the canonical node. Deleting the canonical node is a separate action that removes it from all diagrams.
- **Showing sub-diagram background in PNG export:** When exporting to PNG, the export should capture the currently visible diagram, including its distinct background.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Markdown rendering | Custom parser | `marked` + `DOMPurify` | Marked handles all CommonMark edge cases; DOMPurify prevents XSS from user input |
| Tab persistence across route changes | Custom localStorage | Vue Router param / Pinia ephemeral state | activeDiagramId doesn't need persistence; default to main diagram on mount |
| Node position conflict resolution | Manual merge logic | Always treat diagramNodes[] as source of truth, canonical x/y as main-diagram fallback | Simple and avoids conflicts |

**Key insight:** The entire multi-diagram feature is a frontend-only concern. The backend already stores arbitrary JSON. No new API endpoints or database migrations are needed.

---

## Common Pitfalls

### Pitfall 1: Main Diagram Out of Sync
**What goes wrong:** A new canonical node is added but the main diagram's `diagramNodes[]` is not updated, so the node is invisible on the main diagram canvas.
**Why it happens:** Node creation writes to `model.nodes[]` but forgets to add a `diagramNode` entry for the main diagram.
**How to avoid:** In `addNode()` store action, always append a corresponding entry to the main diagram's `diagramNodes[]`.
**Warning signs:** Node shows in sub-diagram list but is missing from the main diagram tab.

### Pitfall 2: Relationship Arrows Drawn to Missing Nodes
**What goes wrong:** A relationship connects nodeA → nodeB, but only nodeA is in the current sub-diagram. The arrow tries to render to coordinates `{0,0}`.
**Why it happens:** `nodeCenter(nodeId)` returns undefined/null for nodes not in the active diagram.
**How to avoid:** Use the `visibleRelationships` computed filter (see Pattern 2). Add a defensive fallback in `nodeCenter()`.

### Pitfall 3: Existing Models Have No `diagrams` Array
**What goes wrong:** When Phase 6 code loads an old model from the backend, `model.diagrams` is `undefined`, causing crashes.
**Why it happens:** Old models were saved before `diagrams` was part of the schema.
**How to avoid:** In `_transformBackendToFrontend()` in the store, add migration logic:
```javascript
diagrams: Array.isArray(m.diagrams) && m.diagrams.length
  ? m.diagrams
  : [{ id: 'main', name: 'Principal', description: '', isMain: true,
       diagramNodes: (m.nodes || []).map(n => ({ nodeId: n.id, x: n.x || 100, y: n.y || 100 })) }]
```

### Pitfall 4: Stale Node Positions After Canonical Node is Deleted
**What goes wrong:** A node is deleted from the model but its `nodeId` still exists in sub-diagram `diagramNodes[]`, causing dangling references.
**Why it happens:** `deleteNode()` removes from `model.nodes[]` but doesn't clean up sub-diagrams.
**How to avoid:** In `deleteNode()` store action, also sweep all `model.diagrams[].diagramNodes` to remove entries with that `nodeId`.

### Pitfall 5: Markdown XSS
**What goes wrong:** User enters `<script>` or `<img onerror="...">` in the diagram description field and it executes.
**Why it happens:** `marked` converts Markdown to raw HTML that gets injected via `v-html`.
**How to avoid:** Always pipe through `DOMPurify.sanitize()` before `v-html` binding.

---

## Code Examples

### Initializing diagrams on model load
```javascript
// In stores/dimensionalModel.js — _transformBackendToFrontend()
_transformBackendToFrontend(m) {
  const nodes = (m.nodes || []).map(n => this._transformNodeBackendToFrontend(n))
  const diagrams = Array.isArray(m.diagrams) && m.diagrams.length
    ? m.diagrams
    : [{
        id: 'main',
        name: 'Principal',
        description: '',
        isMain: true,
        diagramNodes: nodes.map(n => ({ nodeId: n.id, x: n.x || 100, y: n.y || 100 }))
      }]
  return {
    id: m.id,
    name: m.name,
    description: m.description,
    isGlobal: m.is_global,
    createdBy: m.created_by,
    createdAt: m.created_at,
    updatedAt: m.updated_at,
    nodes,
    relationships: (m.relationships || []).map(r => this._transformRelationshipBackendToFrontend(r)),
    diagrams
  }
},
```

### Adding a node with diagram sync
```javascript
// In stores/dimensionalModel.js — addNode()
addNode(modelId, { type, name, x = 100, y = 100 }) {
  const m = this.models.find(m => m.id === modelId)
  if (!m) return
  const node = { id: generateId(), type, name, x, y, globalRef: null, fields: [] }
  m.nodes.push(node)
  // Keep main diagram in sync
  const mainDiagram = m.diagrams?.find(d => d.isMain)
  if (mainDiagram) {
    mainDiagram.diagramNodes.push({ nodeId: node.id, x, y })
  }
  return node
},
```

### Node drag position update in sub-diagram
```javascript
// In EditorView — when a node drag ends
function onNodeDragEnd(nodeId, newX, newY) {
  if (activeDiagram.value?.isMain) {
    // Main diagram: update canonical position
    modelStore.updateNode(modelId, nodeId, { x: newX, y: newY })
  } else {
    // Sub-diagram: update only the diagramNode entry
    modelStore.updateDiagramNodePosition(modelId, activeDiagramId.value, nodeId, newX, newY)
  }
}
```

### Markdown rendering with sanitization
```javascript
// In component <script setup>
import { marked } from 'marked'
import DOMPurify from 'dompurify'

const sanitizedMd = computed(() =>
  DOMPurify.sanitize(marked.parse(activeDiagram.value?.description || ''))
)
```

---

## State of the Art

| Old Approach | Current Approach | Notes |
|--------------|------------------|-------|
| Single canvas, all nodes always visible | Multi-diagram: main + sub-diagrams showing subsets | This is standard in tools like dbt, Lucidchart, and ERD editors |
| node.x/node.y as the only position | diagramNodes[].{x,y} as diagram-local position override | Enables same node at different positions in different views |
| Plain textarea for description | Markdown textarea + preview toggle | Standard pattern in ERD/wiki tools |

---

## Open Questions

1. **Where does "drag node between diagrams" appear in the UX?**
   - What we know: FEAT03.md mentions "drag nodes between sub-diagrams"
   - What's unclear: Does this mean drag a node from one diagram tab to another (complex, requires cross-tab drop target), or does it mean "add this node to another diagram" via a context menu?
   - Recommendation: Implement as a context-menu action ("Add to diagram…" / "Remove from this diagram") in Phase 6. True cross-tab drag-and-drop is a future enhancement.

2. **Should the backend schema be extended with a `diagrams` column?**
   - What we know: The current DB model has `nodes` (JSON) and `relationships` (JSON) columns. The Python schemas do not list `diagrams`.
   - What's unclear: Whether to add a proper `diagrams` JSON column to the DB model and schema, or embed diagrams inside the `nodes` JSON blob.
   - Recommendation: Add an explicit `diagrams` column to `DimensionalModel` SQLAlchemy model and the Pydantic schemas. This is cleaner and avoids nesting diagrams inside `nodes`. No migration script is needed since the existing Alembic setup or direct `CREATE TABLE` can add the column with a default of `[]`.

3. **Diagram description length and storage**
   - What we know: Requirements say "texto/textarea extenso" with Markdown support.
   - What's unclear: Whether to cap length. PostgreSQL JSON handles large text without issue.
   - Recommendation: No server-side length limit. Frontend textarea can have reasonable UX maxlength for usability.

---

## Sources

### Primary (HIGH confidence)
- Direct source-code inspection of `DimensionalModelEditorView.vue`, `stores/dimensionalModel.js`, `services/api.js`, `backend/app/models/models.py`, `backend/app/schemas/schemas.py` — all read directly from the repository.
- `plans/FEAT03.md` — explicit requirements document for this phase (in-repo, read directly).
- `dashboard-app/CLAUDE.md` — project conventions and stack (read directly).

### Secondary (MEDIUM confidence)
- [marked documentation](https://marked.js.org/) — API verified; v12 is stable and widely used.
- [DOMPurify GitHub](https://github.com/cure53/DOMPurify) — standard XSS sanitizer for browser environments, v3 stable.

### Tertiary (LOW confidence)
- None. All findings are based on direct code inspection or well-established library documentation.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all existing dependencies verified by reading package.json; only marked + DOMPurify are new, both are well-established.
- Architecture: HIGH — based on direct inspection of current store, editor component, and data model; patterns are straightforward extensions of existing code.
- Pitfalls: HIGH — pitfalls derived from reading existing code and identifying exact failure points (e.g., `_transformBackendToFrontend` is the correct place for migration logic).

**Research date:** 2026-04-17
**Valid until:** 2026-05-17 (stable Vue 3 + Pinia ecosystem; codebase not expected to change architecture before planning)
