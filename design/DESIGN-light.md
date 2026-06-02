---
name: Ligth Mode
colors:
  surface: '#f7f9fb'
  surface-dim: '#d8dadc'
  surface-bright: '#f7f9fb'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f2f4f6'
  surface-container: '#eceef0'
  surface-container-high: '#e6e8ea'
  surface-container-highest: '#e0e3e5'
  on-surface: '#191c1e'
  on-surface-variant: '#424754'
  inverse-surface: '#2d3133'
  inverse-on-surface: '#eff1f3'
  outline: '#727785'
  outline-variant: '#c2c6d6'
  surface-tint: '#005ac2'
  primary: '#0058be'
  on-primary: '#ffffff'
  primary-container: '#2170e4'
  on-primary-container: '#fefcff'
  inverse-primary: '#adc6ff'
  secondary: '#565e74'
  on-secondary: '#ffffff'
  secondary-container: '#dae2fd'
  on-secondary-container: '#5c647a'
  tertiary: '#4648d4'
  on-tertiary: '#ffffff'
  tertiary-container: '#6063ee'
  on-tertiary-container: '#fffbff'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#d8e2ff'
  primary-fixed-dim: '#adc6ff'
  on-primary-fixed: '#001a42'
  on-primary-fixed-variant: '#004395'
  secondary-fixed: '#dae2fd'
  secondary-fixed-dim: '#bec6e0'
  on-secondary-fixed: '#131b2e'
  on-secondary-fixed-variant: '#3f465c'
  tertiary-fixed: '#e1e0ff'
  tertiary-fixed-dim: '#c0c1ff'
  on-tertiary-fixed: '#07006c'
  on-tertiary-fixed-variant: '#2f2ebe'
  background: '#f7f9fb'
  on-background: '#191c1e'
  surface-variant: '#e0e3e5'
typography:
  h1:
    fontFamily: Plus Jakarta Sans
    fontSize: 36px
    fontWeight: '700'
    lineHeight: '1.2'
    letterSpacing: -0.02em
  h2:
    fontFamily: Plus Jakarta Sans
    fontSize: 24px
    fontWeight: '600'
    lineHeight: '1.3'
    letterSpacing: -0.01em
  h3:
    fontFamily: Plus Jakarta Sans
    fontSize: 20px
    fontWeight: '600'
    lineHeight: '1.4'
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: '1.6'
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: '1.5'
  body-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: '1.5'
  label-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '600'
    lineHeight: '1'
    letterSpacing: 0.01em
  label-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '500'
    lineHeight: '1'
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  unit: 4px
  container-padding: 24px
  gutter: 16px
  stack-sm: 8px
  stack-md: 16px
  stack-lg: 32px
  section-gap: 48px
---

## Brand & Style
The design system is rooted in a **Modern Corporate** aesthetic, prioritizing clarity, precision, and a sense of "intelligent calm." It targets high-level decision-makers and data analysts who require a high information density without cognitive overload. The interface should evoke a feeling of "command and control"—sophisticated, stable, and highly responsive. 

By leveraging deep slate tones against crisp, soft backgrounds, the system creates a focused work environment. Visual flourishes are reserved for data insights and primary interactions, ensuring the AI-driven metrics remain the focal point.

## Colors
The palette is engineered for professional data environments.
- **Primary (Electric Blue):** Used exclusively for high-priority actions, active states, and critical data trends.
- **Secondary (Slate/Navy):** The foundation for structural elements like sidebars and navigation headers, providing a "grounded" frame for the content.
- **Backgrounds:** A tiered system of soft whites and grays (#F8FAFC to #F1F5F9) to separate different functional areas without harsh borders.
- **Status Colors:** High-saturation tones for immediate semantic recognition within data tables and charts.

## Typography
This design system utilizes a dual-font strategy. **Plus Jakarta Sans** is used for headings and dashboard titles to add a modern, slightly geometric personality. **Inter** is utilized for all body text, data points, and UI labels due to its exceptional legibility at small sizes and high-density environments. Font weights are used purposefully to create hierarchy: Semi-bold for labels and Bold for primary metrics.

## Layout & Spacing
The layout follows a **Fluid Grid** model with a standard 12-column system. 
- **The Sidebar** is fixed at 280px to provide a consistent navigation anchor.
- **The Dashboard Area** uses fluid widths with a maximum inner container of 1600px to prevent excessive line lengths on ultra-wide monitors.
- **Spacing Rhythm:** An 8px base grid ensures consistency. Airy margins (24px to 32px) are used around cards to prevent the data-heavy interface from feeling cramped.

## Elevation & Depth
This design system employs **Tonal Layers** and **Ambient Shadows** to define hierarchy. 
- **Surface Level 0:** The main application background (#F8FAFC).
- **Surface Level 1:** Navigation sidebars and secondary panels.
- **Surface Level 2 (Cards):** Pure white (#FFFFFF) containers with a very soft, diffused shadow (0px 4px 20px rgba(15, 23, 42, 0.05)).
- **Interactive Depth:** On hover, buttons and cards should slightly "lift" using a more pronounced shadow to indicate interactivity.

## Shapes
The shape language is consistently **Rounded**. A 0.5rem (8px) base radius is applied to standard components like buttons and input fields. Large dashboard cards use a 1rem (16px) radius to create a softer, more modern container feel. This balance of rounded corners maintains a professional software look while feeling approachable and contemporary.

## Components
- **Buttons:** Primary buttons use a solid Electric Blue fill with white text. Secondary buttons use a subtle slate outline or ghost style. Interaction states should include a slight darkening of the blue on hover.
- **Cards:** The core container for all analytics. Cards must feature a subtle 1px border (#E2E8F0) in addition to the ambient shadow for crispness on all screen types.
- **Inputs:** Clean, outlined fields with a 1px border. On focus, the border transitions to Electric Blue with a soft outer glow.
- **Data Visualizations:** Use a refined color palette for charts. Avoid standard "rainbow" palettes; instead, use monochromatic shades of blue and indigo, utilizing status colors (green/red) only for highlighting performance metrics.
- **Navigation:** The sidebar uses a dark theme (#0F172A) with high-contrast white text for active states and muted slate-gray for inactive icons, ensuring the primary navigation remains distinct from the content area.