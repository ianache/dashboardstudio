---
name: Dashboard Studio
colors:
  surface: '#111319'
  surface-dim: '#111319'
  surface-bright: '#373940'
  surface-container-lowest: '#0c0e14'
  surface-container-low: '#191b22'
  surface-container: '#1d2026'
  surface-container-high: '#272a30'
  surface-container-highest: '#32353b'
  on-surface: '#e1e2eb'
  on-surface-variant: '#c2c6d5'
  inverse-surface: '#e1e2eb'
  inverse-on-surface: '#2e3037'
  outline: '#8c909e'
  outline-variant: '#424753'
  surface-tint: '#adc6ff'
  primary: '#adc6ff'
  on-primary: '#002e69'
  primary-container: '#0058bc'
  on-primary-container: '#c3d4ff'
  inverse-primary: '#095bbf'
  secondary: '#b7c8e1'
  on-secondary: '#213145'
  secondary-container: '#3a4a5f'
  on-secondary-container: '#a9bad3'
  tertiary: '#ffb595'
  on-tertiary: '#571e00'
  tertiary-container: '#9e3d00'
  on-tertiary-container: '#ffc9b2'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#d8e2ff'
  primary-fixed-dim: '#adc6ff'
  on-primary-fixed: '#001a41'
  on-primary-fixed-variant: '#004494'
  secondary-fixed: '#d3e4fe'
  secondary-fixed-dim: '#b7c8e1'
  on-secondary-fixed: '#0b1c30'
  on-secondary-fixed-variant: '#38485d'
  tertiary-fixed: '#ffdbcd'
  tertiary-fixed-dim: '#ffb595'
  on-tertiary-fixed: '#351000'
  on-tertiary-fixed-variant: '#7c2e00'
  background: '#111319'
  on-background: '#e1e2eb'
  surface-variant: '#32353b'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  title-lg:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '500'
    lineHeight: 28px
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-md:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.05em
  mono-md:
    fontFamily: jetbrainsMono
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 20px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 4px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  gutter: 16px
  margin-mobile: 16px
  margin-desktop: 32px
---

## Brand & Style
The design system is engineered for a high-performance BI/ETL environment where data density and clarity are paramount. The brand personality is **technical, precise, and authoritative**, designed to instill confidence in data engineers and analysts.

The aesthetic follows a **Modern Corporate** approach with **Glassmorphic** accents. It prioritizes a "lights-out" operations center feel, utilizing deep navy surfaces to reduce eye strain during long sessions of pipeline building. Key interactions are highlighted with a vibrant electric blue, while depth is communicated through subtle transparency and layered luminosity rather than traditional heavy shadows.

## Colors
The palette is optimized for a dark-mode-first experience. 
- **Background & Surface:** We use a deep slate hierarchy. The background (`#0f172a`) acts as the canvas, while the primary surface (`#1e2433`) defines workspace areas like sidebars and card containers.
- **Accents:** Electric Blue is used exclusively for primary actions, active states, and progress indicators. 
- **Semantic Colors:** Success, Error, and Warning colors are high-chroma to ensure they stand out against the dark backgrounds for instant status recognition.
- **Borders:** All UI boundaries use a low-contrast slate (`#334155`) to define structure without creating visual noise in data-heavy tables.

## Typography
The system relies on **Inter** for its exceptional readability in digital interfaces. 
- **Hierarchy:** We use a strict typographic scale to manage information density. Headlines use slight negative letter-spacing for a more "locked-in" professional look.
- **Data Display:** For SQL editors and JSON payloads, we introduce **JetBrains Mono** to ensure character distinction (e.g., distinguishing `0` from `O`).
- **Readability:** Text contrast is kept high, with primary body text using 90% opacity white and secondary labels using 60% opacity to maintain a clear visual path.

## Layout & Spacing
The design system utilizes a **12-column fluid grid** for dashboards, allowing widgets to reflow based on screen real estate.
- **Rhythm:** A 4px base unit governs all dimensions.
- **Density:** In "Data View" modes (tables/grids), spacing is compressed to `sm` (8px) for rows. In "Management" modes (settings/forms), spacing expands to `md` (16px) to improve focus.
- **Sidebars:** Fixed-width navigation (240px) or collapsed icons (64px) provide a consistent anchor for the fluid content area.

## Elevation & Depth
Depth is created through **Tonal Layering** and **Glassmorphism**:
- **Level 0 (Background):** `#0f172a` - The lowest layer.
- **Level 1 (Card/Surface):** `#1e2433` - Used for primary UI containers.
- **Level 2 (Modals/Overlays):** These use a semi-transparent version of the surface color (80% opacity) with a `blur(12px)` backdrop filter and a 1px inner border of `#ffffff10`.
- **Shadows:** Avoid heavy black shadows. Use subtle, 20% opacity blue-tinted shadows for floating elements to maintain the "luminous" dark aesthetic.

## Shapes
The shape language balances approachability with professional structure.
- **Components:** Standard buttons, inputs, and cards use an **8px (0.5rem)** corner radius.
- **Large Containers:** Dashboard widgets and modals use a **16px (1rem)** radius to soften the high-density data layouts.
- **Badges/Chips:** Use a fully rounded "pill" shape (999px) to distinguish them from interactive buttons.

## Components
- **Buttons:** Primary buttons are solid Electric Blue. Secondary buttons are ghost-style with a 1px border. All hover states should include a subtle "inner glow" or brightness increase.
- **Pill Badges:** Used for status (e.g., "Active", "Failed"). These must be semi-transparent with a 10% background opacity of their semantic color and a 100% opacity text label for high legibility.
- **Input Fields:** Dark background (`#0f172a`), 1px border (`#334155`). On focus, the border transitions to Electric Blue with a subtle outer glow.
- **Data Nodes:** In the ETL workflow builder, nodes should be cards with 8px rounding, featuring a 2px colored left-border indicating the node type (Source, Transform, Sink).
- **Tables:** No vertical borders. Use 1px horizontal dividers. Header rows should have a slightly darker background than body rows to anchor the data.
- **Modals:** Must use the glassmorphic style—frosted background blur and a subtle white top-stroke to simulate light hitting the edge.