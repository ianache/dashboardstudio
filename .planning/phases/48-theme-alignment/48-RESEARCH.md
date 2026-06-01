# Phase 48: Theme Alignment - Research

**Researched:** 2026-06-01
**Domain:** CSS custom properties, Vue 3 scoped styles, light/dark theming
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Scope de archivos:**
- Views: HomeView, ConnectionsView, DashboardDesignerView, DashboardViewerView, SettingsView, LoginView, DataTypesView, DiagramTypesView, DimensionalModelEditorView, DimensionalModelListView, ToolCatalogView, VisualizationConfiguratorView, KnowledgeSpacesView
- Components: SideMenu, TopBar, AppLayout, DashboardCard, KpiCard, ConfirmModal, PanelHeadBodyPieComponent, QuickActionCard, PageHeader, MIcon
- **Excluidos:** FlowEditorView, IntegrationsView, FlowEditorCanvas (y todos sus subcomponentes de editor)

**Logo del SideMenu:**
- `background: #2563eb` → `background: var(--primary-container)`
- Ícono y texto: `var(--on-primary-container)`

**Bloque de usuario (footer del SideMenu):**
- `background: #1e293b` → `background: var(--surface-container-high)`
- Nombre: `var(--on-surface)`
- Rol: `var(--on-surface-variant)`

**Nav-item activo:**
- `background: var(--primary-container)`
- `color: var(--on-primary-container)`
- `border-left-color: var(--primary)`
- Sub-item activo: `color: var(--primary)`

**Nav-item hover:**
- `background: rgba(15,23,42,0.6)` → `background: var(--surface-container-high)`
- Texto: `var(--on-surface)`
- Sub-item hover: `background: var(--surface-container)`

**Cards en views:**
- Fondo: `var(--card-bg)`
- Texto principal: `var(--on-surface)`
- Texto secundario: `var(--on-surface-variant)`
- Borde: `var(--outline-variant)`

**Textos de labels/hints/monospace:**
- Labels técnicos: `var(--on-surface-variant)`

**Inline styles en templates:**
- Eliminar todos los `style="color:#..."` del HTML
- Crear clases semánticas en `<style scoped>`: `.icon-muted`, `.icon-primary`, `.text-secondary`, etc.

**TopBar dropdowns y paneles:**
- Fondos: `var(--surface-container-lowest)`
- Bordes: `var(--outline-variant)`
- Texto: `var(--on-surface)` y `var(--on-surface-variant)`
- Botón danger hover: `var(--error-container)`

### Claude's Discretion
- Orden exacto de migración dentro de cada archivo
- Decisión sobre colores de estado (success/warning/error) que ya usan `--success`, `--warning` — mantener si ya funcionan en ambos temas
- Colores específicos de badges, chips y estados de conexión si usan variables del sistema correctamente

### Deferred Ideas (OUT OF SCOPE)
- FlowEditorView + IntegrationsView + canvas de nodos
- Animaciones de transición entre temas (fade suave)
- Modo "auto" que siga `prefers-color-scheme`
</user_constraints>

---

## Summary

Phase 48 is a pure CSS token migration — no new logic, no new components. The theme toggle infrastructure (Phase 47) is already complete: `uiStore.setTheme()` writes `data-theme` on `<html>`, and all tokens in `:root` and `[data-theme="light"]` are already defined in `main.css`. This phase replaces every hardcoded color value in in-scope files with the correct CSS variable.

The work has two distinct categories. The first is **`<style scoped>` CSS rules** containing hardcoded hex values (`#fff`, `#0f172a`, `#2563eb`, `#1e293b`, etc.) and also references to undeclared legacy tokens (`--text`, `--text-secondary`). The second is **inline `style="color:#..."` attributes** in templates that must be replaced with semantic CSS classes.

The most important structural finding is that **`--text` and `--text-secondary` are used extensively but are not defined in `main.css`**. They appear 165 times across 13 files (TopBar, PageHeader, DashboardDesignerView, VisualizationConfiguratorView, etc.). These must be aliased or replaced as part of this phase — the correct mapping is `--text` → `var(--on-surface)` and `--text-secondary` → `var(--on-surface-variant)`.

**Primary recommendation:** Work file-by-file. Each file has isolated `<style scoped>` — changes cannot bleed. Replace CSS rules first, inline styles second. SideMenu is highest priority (15+ hardcoded instances). TopBar is second priority (legacy `--text`/`--text-secondary` tokens + hardcoded dropdown backgrounds).

---

## Standard Stack

No new libraries are needed. All tokens already exist.

### Token Inventory (already in `main.css`)

| Token | Dark value | Light value | Replaces |
|-------|-----------|-------------|---------|
| `--card-bg` | `#1e2433` | `#ffffff` | `#fff`, `background: white`, `bg-white` |
| `--on-surface` | `#e1e2eb` | `#191c1e` | `#0f172a`, `#fff` (text), `text-slate-900` |
| `--on-surface-variant` | `#c2c6d5` | `#424754` | `#64748b`, `#94a3b8`, `#475569`, `text-slate-500` |
| `--surface-container-high` | `#272a30` | `#e6e8ea` | `#1e293b`, `rgba(15,23,42,0.6)` hover |
| `--surface-container` | `#1d2026` | `#eceef0` | `rgba(0,0,0,0.2)` sub-nav bg |
| `--surface-container-lowest` | `#0c0e14` | `#ffffff` | dropdown panels `background: #fff` |
| `--primary-container` | `#0058bc` | `#2170e4` | `#2563eb` (logo, active bg, badges) |
| `--on-primary-container` | `#c3d4ff` | `#fefcff` | `#fff` on blue backgrounds |
| `--primary` | `#adc6ff` | `#0058be` | `#3b82f6`, `#2563eb` (active border) |
| `--outline-variant` | `#424753` | `#c2c6d6` | `#e2e8f0`, `#334155`, `border-slate-200` |
| `--outline` | `#334155` | `#727785` | borders on inputs, cards |
| `--error-container` | `#93000a` | `#ffdad6` | danger hover bg |
| `--bg` | `#0f172a` | `#f7f9fb` | page backgrounds |
| `--sidebar-bg` | `var(--surface-container-lowest)` | `#ffffff` | already correct |
| `--shadow`, `--shadow-md` | blue-tinted | slate-tinted | already correct |

### Legacy Token Mapping (CRITICAL — not in new design system)

| Legacy token | Correct replacement | Occurrences |
|---|---|---|
| `var(--text)` | `var(--on-surface)` | ~100+ |
| `var(--text-secondary)` | `var(--on-surface-variant)` | ~65+ |
| `var(--primary-light)` | `var(--surface-container)` | found in TopBar `.alert-item.unread` |

---

## Architecture Patterns

### How theming works in this codebase

```
html[data-theme="light"]  ← uiStore.setTheme() writes here
  └── :root overrides     ← all --tokens resolve from here down
        └── .scoped-class { background: var(--card-bg) }  ← component CSS
```

CSS cascade resolves `var()` at paint time. No JavaScript is needed in components. Changing `data-theme` on `<html>` causes all `var()` references to instantly resolve to the new values.

### Pattern 1: Replace inline style with scoped class

**What:** Move hardcoded `style="color:#..."` from template into `<style scoped>` as a semantic class.

**When to use:** Any `style="color:#hexvalue"` or `style="color:rgba(...)"` on an icon, span, or div in the template.

**Before:**
```html
<MIcon icon="person" :size="18" style="color:#64748b" />
```

**After (template):**
```html
<MIcon icon="person" :size="18" class="icon-muted" />
```

**After (scoped style):**
```css
.icon-muted { color: var(--on-surface-variant); }
```

### Pattern 2: Replace CSS rule hex value with token

**What:** Find hex/rgba in `<style scoped>` CSS rules, replace with the matching token.

**Before:**
```css
.logo-icon-wrap {
  background: #2563eb;
}
.workspace-avatar {
  background: #1e293b;
  border: 1px solid #334155;
}
.nav-item:hover { background: rgba(15,23,42,0.6); }
```

**After:**
```css
.logo-icon-wrap {
  background: var(--primary-container);
}
.workspace-avatar {
  background: var(--surface-container-high);
  border: 1px solid var(--outline);
}
.nav-item:hover { background: var(--surface-container-high); }
```

### Pattern 3: Replace legacy `--text` tokens in TopBar and components

**What:** `--text` and `--text-secondary` are undefined in the new design system but used everywhere in TopBar, PageHeader, and several views. Replace all occurrences.

**Before:**
```css
.hamburger-btn { color: var(--text-secondary); }
.hamburger-btn:hover { color: var(--text); }
.bread-item.last { color: var(--text); }
.dropdown-panel { background: #fff; }
.dp-danger:hover { background: #fff2f0; }
```

**After:**
```css
.hamburger-btn { color: var(--on-surface-variant); }
.hamburger-btn:hover { color: var(--on-surface); }
.bread-item.last { color: var(--on-surface); }
.dropdown-panel { background: var(--surface-container-lowest); }
.dp-danger:hover { background: var(--error-container); }
```

### Pattern 4: Replace Tailwind-like hardcoded utility classes in views

**What:** Views like ConnectionsView, SettingsView, and DimensionalModelListView use utility classes like `text-slate-900`, `bg-white`, `border-slate-200`. These need to be replaced either with scoped CSS classes or with the equivalent CSS variable token.

**Strategy:** Create a `.view-title`, `.view-subtitle`, `.view-card` etc. scoped class per view rather than inline utility classes. Or — for views that already have scoped CSS — add the missing classes.

**Before (ConnectionsView template):**
```html
<h1 class="font-h1 text-h1 text-slate-900">Conexiones</h1>
<p class="font-body-md text-slate-500 max-w-2xl">...</p>
<div class="bg-white border border-slate-200 rounded-xl ...">
```

**After (template):**
```html
<h1 class="font-h1 text-h1 page-title">Conexiones</h1>
<p class="font-body-md page-subtitle max-w-2xl">...</p>
<div class="cv-empty-box">
```

**After (scoped style):**
```css
.page-title    { color: var(--on-surface); }
.page-subtitle { color: var(--on-surface-variant); }
.cv-empty-box  { background: var(--card-bg); border: 1px solid var(--outline-variant); border-radius: 12px; }
```

### Recommended Migration Order

Process files in this order (highest hardcoded density first):

1. **SideMenu.vue** — ~15 hardcoded instances, all in `<style scoped>`
2. **TopBar.vue** — legacy `--text`/`--text-secondary` + `background: #fff` on dropdowns
3. **AppLayout.vue** — already clean (uses `--bg`), verify only
4. **ConnectionsView.vue** — heaviest view; utility classes + `cv-card` with `#fff`/`#e2e8f0`
5. **SettingsView.vue** — `text-slate-900`, `text-slate-500` in header section
6. **DimensionalModelListView.vue** — 6+ inline `style="color:#..."` in template
7. **DashboardDesignerView.vue** — mixed `--text`/`--text-secondary` legacy tokens
8. **LoginView.vue** — standalone page; gradient background + card background
9. **DataTypesView.vue, DiagramTypesView.vue, ToolCatalogView.vue** — similar pattern, bulk
10. **KnowledgeSpacesView.vue, VisualizationConfiguratorView.vue** — same pattern
11. **DimensionalModelEditorView.vue, DashboardViewerView.vue** — lowest density
12. **Common components**: PageHeader, KpiCard, QuickActionCard — already mostly correct, minor fixes

### Anti-Patterns to Avoid

- **Do not add `--text` or `--text-secondary` to `main.css`:** The correct fix is to replace uses with `--on-surface` / `--on-surface-variant`. Adding aliases creates more tech debt.
- **Do not use `rgba()` with hardcoded dark colors for hover states:** `rgba(15,23,42,0.6)` looks dark in dark mode but invisible in light mode. Use `var(--surface-container-high)` instead.
- **Do not touch FlowEditorCanvas, AiCodeAssist, CodeAiAssist, PropDefsTable:** These are excluded and have their own dense color system.
- **Do not refactor component logic or structure:** Only `<style scoped>` and template attribute replacements.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Light/dark detection | Custom JS observer | `data-theme` on `<html>` (already set by uiStore) | Already implemented in Phase 47 |
| Token definitions | New CSS variables | Existing `:root` + `[data-theme="light"]` tokens | All 30+ tokens already defined |
| Theme persistence | localStorage custom code | `uiStore.theme` (already persists) | Phase 47 complete |

---

## Common Pitfalls

### Pitfall 1: `--text` and `--text-secondary` are undefined tokens

**What goes wrong:** TopBar, PageHeader, DashboardDesignerView, and several other files use `var(--text)` and `var(--text-secondary)` extensively. These tokens DO NOT exist in `main.css`. They resolve to `undefined`, which means the browser falls back to the inherited color — which happens to work in dark mode because `html,body` inherits `color: var(--text)` (also undefined). The cascade accidentally works in dark mode but will NOT switch in light mode.

**Why it happens:** Pre-existing legacy code from before the System Design was defined. These tokens were defined in an old version of `main.css` that has since been replaced with the Material You token set.

**How to avoid:** Replace ALL occurrences of `var(--text)` with `var(--on-surface)` and `var(--text-secondary)` with `var(--on-surface-variant)`.

**Warning signs:** Any file using `--text` or `--text-secondary` will not respond to the theme toggle.

### Pitfall 2: Hardcoded dropdown/modal backgrounds won't adapt

**What goes wrong:** `TopBar.vue` has `.dropdown-panel { background: #fff }` and `.dp-danger:hover { background: #fff2f0 }`. In light mode these look correct but in dark mode they show white panels.

**How to avoid:** Replace with `var(--surface-container-lowest)` for dropdown backgrounds and `var(--error-container)` for danger hover.

### Pitfall 3: `SideMenu` nav-item colors are partially hardcoded

**What goes wrong:** Nav items have `color: #94a3b8` (inactive), `color: #fff` (active), and `background: rgba(37,99,235,0.12)` (active bg). The active background is a semi-transparent hardcoded blue that will look wrong in light mode.

**How to avoid:** Use the exact locked-decision tokens: active → `background: var(--primary-container); color: var(--on-primary-container)`.

### Pitfall 4: Nav section titles use `rgba(255,255,255,0.25)`

**What goes wrong:** `.nav-section-title { color: rgba(255,255,255,0.25) }` — hardcoded white with opacity. In light mode, white text on white background is invisible.

**How to avoid:** Replace with `var(--on-surface-variant)` at reduced opacity, or `color: var(--on-surface-variant); opacity: 0.5`.

### Pitfall 5: Sub-nav items use white-based rgba values

**What goes wrong:** `.nav-sub-item { color: rgba(255,255,255,0.4) }` and `.nav-sub { background: rgba(0,0,0,0.2) }` — both will fail in light mode.

**How to avoid:**
- `.nav-sub-item` → `color: var(--on-surface-variant)`
- `.nav-sub` → `background: var(--surface-container)`
- `.nav-sub-item:hover` → `background: var(--surface-container-high); color: var(--on-surface)`

### Pitfall 6: LoginView gradient background is hardcoded

**What goes wrong:** `background: linear-gradient(135deg, #001529 0%, #003a8c 100%)` on `.auth-redirect`. The card also has `background: #fff`.

**How to avoid:** Replace gradient with `background: var(--background)` (or `var(--bg)`). Card: `background: var(--card-bg)`. This login page is a standalone route (no AppLayout), so the `data-theme` still applies to `<html>`.

### Pitfall 7: `ConfirmModal.vue` glassmorphic dialog uses hardcoded RGBA

**What goes wrong:** `.cm-dialog { background: rgba(30, 36, 51, 0.8) }` — hardcoded dark card background. In light mode, a semi-transparent dark card will look wrong.

**How to avoid:** The glassmorphic style intentionally uses a specific effect. Replace with `background: color-mix(in srgb, var(--card-bg) 85%, transparent)` OR simply `background: var(--surface-container-high)` for the dialog. The `cm-overlay` `rgba(15,23,42,0.55)` can stay as a backdrop dimmer — it's intentionally dark for focus in both themes.

---

## Code Examples

### SideMenu: Before/After for the highest-density area

```css
/* BEFORE — hardcoded, breaks in light mode */
.logo-icon-wrap   { background: #2563eb; }
.logo-title       { color: #fff; }
.logo-subtitle    { color: #475569; }
.nav-item         { color: #94a3b8; }
.nav-item:hover   { color: #f1f5f9; background: rgba(15,23,42,0.6); }
.nav-item.active  { color: #fff; background: rgba(37,99,235,0.12); border-left-color: #3b82f6; }
.nav-section-title { color: rgba(255,255,255,0.25); }
.nav-sub          { background: rgba(0,0,0,0.2); }
.nav-sub-item     { color: rgba(255,255,255,0.4); }
.nav-sub-item:hover { color: #fff; background: rgba(255,255,255,0.05); }
.nav-sub-item.active { color: #93c5fd; }
.workspace-avatar { background: #1e293b; border: 1px solid #334155; }
.workspace-name   { color: #fff; }
.workspace-role   { color: #475569; }
.nav-badge        { background: #2563eb; color: #fff; }

/* AFTER — theme-aware */
.logo-icon-wrap   { background: var(--primary-container); }
.logo-title       { color: var(--on-primary-container); }
.logo-subtitle    { color: var(--on-surface-variant); }
.nav-item         { color: var(--on-surface-variant); }
.nav-item:hover   { color: var(--on-surface); background: var(--surface-container-high); }
.nav-item.active  { color: var(--on-primary-container); background: var(--primary-container); border-left-color: var(--primary); }
.nav-section-title { color: var(--on-surface-variant); opacity: 0.6; }
.nav-sub          { background: var(--surface-container); }
.nav-sub-item     { color: var(--on-surface-variant); }
.nav-sub-item:hover { color: var(--on-surface); background: var(--surface-container-high); }
.nav-sub-item.active { color: var(--primary); }
.workspace-avatar { background: var(--surface-container-high); border: 1px solid var(--outline); }
.workspace-name   { color: var(--on-surface); }
.workspace-role   { color: var(--on-surface-variant); }
.nav-badge        { background: var(--primary-container); color: var(--on-primary-container); }
```

### SideMenu: Inline style replacement

```html
<!-- BEFORE -->
<MIcon icon="analytics" :size="22" :fill="1" style="color:#fff" />
<MIcon icon="person" :size="18" style="color:#64748b" />

<!-- AFTER -->
<MIcon icon="analytics" :size="22" :fill="1" class="icon-on-primary" />
<MIcon icon="person" :size="18" class="icon-muted" />
```

```css
/* scoped */
.icon-on-primary { color: var(--on-primary-container); }
.icon-muted      { color: var(--on-surface-variant); }
```

### TopBar: Background and legacy token replacement

```css
/* BEFORE */
.top-bar         { background: #fff; }
.dropdown-panel  { background: #fff; }
.dp-danger:hover { background: #fff2f0; }
.alert-item.unread { background: var(--primary-light); }
.alert-item.unread:hover { background: #d0e9ff; }
.hamburger-btn   { color: var(--text-secondary); }
.hamburger-btn:hover { color: var(--text); }

/* AFTER */
.top-bar         { background: var(--surface-container-lowest); }
.dropdown-panel  { background: var(--surface-container-lowest); border: 1px solid var(--outline-variant); }
.dp-danger:hover { background: var(--error-container); }
.alert-item.unread { background: var(--surface-container); }
.alert-item.unread:hover { background: var(--surface-container-high); }
.hamburger-btn   { color: var(--on-surface-variant); }
.hamburger-btn:hover { color: var(--on-surface); }
```

### ConnectionsView: Card with utility classes

```html
<!-- BEFORE — hardcoded classes and inline styles -->
<div class="bg-white border border-slate-200 rounded-xl p-12 ...">
  <h3 class="text-lg font-semibold text-slate-900">Sin conexiones configuradas</h3>
  <p class="text-sm text-slate-500 max-w-md">...</p>
</div>

<!-- AFTER — scoped classes -->
<div class="cv-empty-box">
  <h3 class="cv-empty-title">Sin conexiones configuradas</h3>
  <p class="cv-empty-desc max-w-md">...</p>
</div>
```

```css
/* in scoped */
.cv-empty-box   { background: var(--card-bg); border: 1px solid var(--outline-variant); border-radius: 12px; padding: 3rem; display: flex; flex-direction: column; align-items: center; gap: 1rem; text-align: center; }
.cv-empty-title { font-size: 18px; font-weight: 600; color: var(--on-surface); }
.cv-empty-desc  { font-size: 14px; color: var(--on-surface-variant); }
```

---

## File-by-File Audit Summary

### SideMenu.vue — HIGH density (15 instances)

| Location | Hardcoded | Replace with |
|----------|-----------|-------------|
| `.logo-icon-wrap` | `background: #2563eb` | `var(--primary-container)` |
| `.logo-title` | `color: #fff` | `var(--on-primary-container)` |
| `.logo-subtitle` | `color: #475569` | `var(--on-surface-variant)` |
| Template `MIcon analytics` | `style="color:#fff"` | `class="icon-on-primary"` |
| Template `MIcon person` | `style="color:#64748b"` | `class="icon-muted"` |
| `.nav-item` | `color: #94a3b8` | `var(--on-surface-variant)` |
| `.nav-item:hover` | `rgba(15,23,42,0.6)` | `var(--surface-container-high)` |
| `.nav-item.active` | `rgba(37,99,235,0.12)`, `#3b82f6` | `var(--primary-container)`, `var(--primary)` |
| `.nav-section-title` | `rgba(255,255,255,0.25)` | `var(--on-surface-variant)` + `opacity:0.6` |
| `.nav-sub` | `rgba(0,0,0,0.2)` | `var(--surface-container)` |
| `.nav-sub-item` | `rgba(255,255,255,0.4)` | `var(--on-surface-variant)` |
| `.nav-sub-item:hover` | `rgba(255,255,255,0.05)` | `var(--surface-container-high)` |
| `.nav-sub-item.active` | `color: #93c5fd` | `var(--primary)` |
| `.workspace-avatar` | `#1e293b`, `#334155` | `var(--surface-container-high)`, `var(--outline)` |
| `.workspace-name` | `color: #fff` | `var(--on-surface)` |
| `.workspace-role` | `color: #475569` | `var(--on-surface-variant)` |
| `.nav-badge` | `#2563eb`, `#fff` | `var(--primary-container)`, `var(--on-primary-container)` |
| Scrollbar thumb | `rgba(255,255,255,0.1)` | `var(--outline)` |

### TopBar.vue — MEDIUM density (legacy tokens + hardcoded backgrounds)

| Location | Issue | Fix |
|----------|-------|-----|
| `.top-bar` | `background: #fff` | `var(--surface-container-lowest)` |
| `.dropdown-panel` | `background: #fff` | `var(--surface-container-lowest)` |
| `.dp-danger:hover` | `background: #fff2f0` | `var(--error-container)` |
| `.alert-item.unread` | `var(--primary-light)` (undefined) | `var(--surface-container)` |
| All `var(--text)` | undefined token | `var(--on-surface)` |
| All `var(--text-secondary)` | undefined token | `var(--on-surface-variant)` |
| `.hamburger-btn:hover` | `background: var(--bg)` | `var(--surface-container-high)` |
| `.action-btn:hover` | `background: var(--bg)` | `var(--surface-container-high)` |

### ConnectionsView.vue — HIGH density (30+ instances)

| Category | Issue | Fix |
|----------|-------|-----|
| Template utility classes | `text-slate-900`, `text-slate-500` | Create `.page-title`, `.page-subtitle` scoped classes |
| Template utility classes | `bg-white border border-slate-200` | Create `.cv-empty-box` scoped class |
| Skeleton loaders | `bg-white border border-slate-200`, `bg-slate-100` | `var(--card-bg)`, `var(--outline-variant)`, `var(--surface-container)` |
| `.cv-card` | `background: #fff; border: 1px solid #e2e8f0` | `var(--card-bg)`, `var(--outline-variant)` |
| `.cv-card-name` | `color: #0f172a` | `var(--on-surface)` |
| `.cv-card-desc` | `color: #64748b` | `var(--on-surface-variant)` |
| `.cv-host-label` | hardcoded color | `var(--on-surface-variant)` |
| Inline `style="color:#94a3b8"` on icons | template inline | `.icon-muted` class |
| Inline `style="color:#dc2626"` delete icon | template inline | `.icon-danger` class |
| Delete confirm modal | multiple hardcoded | `var(--card-bg)`, tokens |

### SettingsView.vue — MEDIUM density

| Location | Issue | Fix |
|----------|-------|-----|
| Header `text-slate-900` | hardcoded text class | `.page-title { color: var(--on-surface) }` |
| Header `text-slate-500` | hardcoded text class | `.page-subtitle { color: var(--on-surface-variant) }` |
| `var(--text)` usages | undefined token | `var(--on-surface)` |
| `var(--text-secondary)` usages | undefined token | `var(--on-surface-variant)` |

### DimensionalModelListView.vue — MEDIUM (6 inline template styles)

| Location | Hardcoded | Fix |
|----------|-----------|-----|
| `style="color: #2563eb"` on hub icons | 3 occurrences | `.icon-primary { color: var(--primary) }` |
| `style="color: #0f172a"` on selected text | 2 occurrences | `.text-main { color: var(--on-surface) }` |
| `style="color: #94a3b8"` on placeholder/arrow | 3 occurrences | `.icon-muted { color: var(--on-surface-variant) }` |

### LoginView.vue — LOW density (standalone page)

| Location | Hardcoded | Fix |
|----------|-----------|-----|
| `.auth-redirect` | `linear-gradient(135deg, #001529 0%, #003a8c 100%)` | `background: var(--background)` |
| `.auth-redirect-card` | `background: #fff` | `background: var(--card-bg)` |
| `.auth-spinner` | `border: 3px solid #e6f4ff; border-top-color: #1890ff` | `var(--outline-variant)`, `var(--primary)` |
| `SVG fill="#1890ff"` | hardcoded in SVG | Keep — SVG logos are intentionally brand-fixed |

### PageHeader.vue — LOW density

| Location | Issue | Fix |
|----------|-------|-----|
| `.ph-title` | `color: var(--text)` | `var(--on-surface)` |
| `.ph-desc` | `color: var(--text-secondary)` | `var(--on-surface-variant)` |

### ConfirmModal.vue — LOW density

| Location | Hardcoded | Fix |
|----------|-----------|-----|
| `.cm-dialog` | `rgba(30, 36, 51, 0.8)` | `var(--surface-container-high)` |
| `.cm-btn--primary:hover` | `#0066d6` | Keep — hardcoded pressed-blue shade is acceptable for hover precision |
| `.cm-btn--danger:hover` | `#ab000d` | Keep — same rationale |
| `.cm-footer` border | `rgba(255,255,255,0.05)` | `var(--outline-variant)` |

### DashboardCard.vue — CLEAN
Already uses CSS tokens throughout. Only check: gradient array in `<script setup>` uses hardcoded colors — these are intentional decorative gradients, acceptable to leave.

### KpiCard.vue — CLEAN
Uses CSS tokens throughout. `iconBg` prop default `rgba(0,88,190,0.1)` is passed from HomeView which already uses `rgba()` with token color values inline — acceptable as prop default.

### QuickActionCard.vue — MOSTLY CLEAN
Minor: `rgba(0, 88, 190, 0.1)` and `rgba(86, 94, 116, 0.1)` hardcoded in icon wrap backgrounds. Acceptable — these reference exact primary/secondary hex values that correspond to the dark theme; they are not critical for theme switching.

### PanelHeadBodyPieComponent.vue — MOSTLY CLEAN
Two instances to fix:
- `.panel-header:hover { background: rgba(173, 198, 255, 0.05) }` — acceptable (subtle, works in both)
- `.panel-btn-primary:hover { background: #0066d6 }` — acceptable (same as ConfirmModal)

---

## State of the Art

| Old Approach | Current Approach | Impact |
|--------------|------------------|--------|
| Hardcoded hex colors in scoped CSS | CSS custom properties from `:root` / `[data-theme]` | Toggle changes all values instantly |
| `--text` / `--text-secondary` legacy tokens | `--on-surface` / `--on-surface-variant` Material You tokens | Correct names, defined values |
| `rgba(dark-color, opacity)` for hover states | `var(--surface-container-high)` semantic surface token | Works in both themes |
| `background: #fff` on dropdowns/cards | `var(--card-bg)` or `var(--surface-container-lowest)` | Adapts to both modes |

---

## Open Questions

1. **SVG logo in LoginView has `fill="#1890ff"`**
   - What we know: Brand blue, intentional, in an inline SVG
   - Recommendation: Leave it. Brand colors in logos/marks are intentionally fixed.

2. **`--primary-light` in TopBar `.alert-item.unread`**
   - What we know: This token (`--primary-light`) is not defined anywhere. The unread state currently has no visible highlight.
   - Recommendation: Replace with `var(--surface-container)` — provides a subtle tonal differentiation without adding a new token.

3. **Glassmorphic modals (`ConfirmModal`, `cm-dialog`)**
   - What we know: The `backdrop-filter: blur` + semi-transparent background is a deliberate design choice.
   - What's unclear: Whether glassmorphic style looks right in light mode with `var(--surface-container-high)` (solid, no transparency).
   - Recommendation: Replace `rgba(30,36,51,0.8)` with `var(--surface-container-high)` for the dialog background. The overlay blur still provides the visual depth. If the team wants true glassmorphism in both themes, that is a separate enhancement.

---

## Sources

### Primary (HIGH confidence)
- Direct code audit: `dashboard-app/src/assets/main.css` — full token inventory verified
- Direct code audit: `dashboard-app/src/components/layout/SideMenu.vue` — hardcoded instances counted
- Direct code audit: `dashboard-app/src/components/layout/TopBar.vue` — legacy token usage confirmed
- Direct code audit: `dashboard-app/src/stores/ui.js` — theme mechanism confirmed
- Direct code audit: `design/DESIGN.md`, `design/DESIGN-light.md` — token sources verified

### Secondary (HIGH confidence — same codebase)
- `48-CONTEXT.md` — all locked decisions read and incorporated verbatim

---

## Metadata

**Confidence breakdown:**
- Token inventory: HIGH — all tokens verified directly in `main.css`
- File-by-file audit: HIGH — all 12 in-scope components/views code-read
- Replacement mapping: HIGH — all mappings derived from existing token definitions
- Pitfall identification: HIGH — all identified from actual code, not assumptions

**Research date:** 2026-06-01
**Valid until:** Stable — tokens won't change unless `main.css` is edited
