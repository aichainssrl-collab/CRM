---
name: Professional Enterprise CRM
colors:
  surface: '#fcf8fa'
  surface-dim: '#ddd9db'
  surface-bright: '#fcf8fa'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f6f2f4'
  surface-container: '#f1edef'
  surface-container-high: '#ebe7e9'
  surface-container-highest: '#e5e1e3'
  on-surface: '#1c1b1d'
  on-surface-variant: '#47464c'
  inverse-surface: '#313032'
  inverse-on-surface: '#f4f0f2'
  outline: '#78767d'
  outline-variant: '#c8c5cd'
  surface-tint: '#5d5c74'
  primary: '#00000b'
  on-primary: '#ffffff'
  primary-container: '#1a1a2e'
  on-primary-container: '#83829b'
  inverse-primary: '#c6c4df'
  secondary: '#5e5d68'
  on-secondary: '#ffffff'
  secondary-container: '#e1deea'
  on-secondary-container: '#63616c'
  tertiary: '#695d3c'
  on-tertiary: '#ffffff'
  tertiary-container: '#b9aa83'
  on-tertiary-container: '#493f20'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#e2e0fc'
  primary-fixed-dim: '#c6c4df'
  on-primary-fixed: '#1a1a2e'
  on-primary-fixed-variant: '#45455b'
  secondary-fixed: '#e4e1ed'
  secondary-fixed-dim: '#c8c5d1'
  on-secondary-fixed: '#1b1b23'
  on-secondary-fixed-variant: '#47464f'
  tertiary-fixed: '#f2e1b7'
  tertiary-fixed-dim: '#d5c59d'
  on-tertiary-fixed: '#231b02'
  on-tertiary-fixed-variant: '#514627'
  background: '#fcf8fa'
  on-background: '#1c1b1d'
  surface-variant: '#e5e1e3'
typography:
  display:
    fontFamily: Inter
    fontSize: 28px
    fontWeight: '700'
    lineHeight: 36px
    letterSpacing: -0.02em
  h1:
    fontFamily: Inter
    fontSize: 22px
    fontWeight: '600'
    lineHeight: 28px
    letterSpacing: -0.01em
  h2:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 24px
  h3:
    fontFamily: Inter
    fontSize: 15px
    fontWeight: '600'
    lineHeight: 20px
  body:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  body-medium:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
  small:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
  small-medium:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
  mono:
    fontFamily: JetBrains Mono
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 4px
  sidebar_width: 240px
  topbar_height: 56px
  container_padding: 32px
  stack_gap: 16px
  input_height: 36px
---

## Brand & Style

This design system is built for the high-stakes environment of B2B enterprise sales and relationship management. It prioritizes utility, speed, and clarity above all else. The brand personality is **sober, reliable, and precise**, evoking a sense of institutional trust while maintaining the agile feel of modern developer-centric tools.

The design style is **Minimalist-Corporate**. It draws heavily from the density and typographic precision of Linear and the clean, functional aesthetics of the Vercel Dashboard. The interface uses generous white space and a restricted color palette to reduce cognitive load, allowing users to focus on complex data sets and mission-critical workflows.

## Colors

The color strategy uses deep Navy (#1A1A2E) for structural elements to ground the interface in professionalism. The primary accent is a vibrant Indigo (#3B5BDB) used sparingly to signal interactivity and focus. 

The palette is divided into functional layers:
- **Structural:** The Sidebar uses the Primary color to distinguish navigation from content.
- **Surface:** A high-contrast combination of White surfaces on a Light Gray background provides clear visual separation of modules.
- **Feedback:** Semantic colors (Success, Warning, Destructive) are paired with low-saturation "Light" variants for background fills in badges and alerts, ensuring high legibility without overwhelming the user.
- **Borders:** Two levels of border strength are used to define hierarchy without relying on heavy shadows.

## Typography

The typography in this design system utilizes **Inter** for all UI elements to ensure maximum legibility and a neutral, systematic tone. A secondary Monospace font (JetBrains Mono) is reserved for IDs, API keys, and data tables where character alignment is critical.

- **Headings:** Use tight letter-spacing on larger sizes to maintain a modern, "tucked" appearance.
- **Body Text:** Optimized at 14px for high information density, typical of B2B dashboards.
- **Hierarchy:** Weight is used more frequently than size to distinguish information levels, keeping the interface compact.

## Layout & Spacing

The layout follows a **Fixed-Fluid** hybrid model. The 240px sidebar is permanently docked to the left to provide constant access to high-level navigation, while the content area expands to fill the viewport.

- **Grid:** A 12-column fluid system is used for dashboard layouts, with 24px gutters.
- **Rhythm:** All spacing is based on a 4px increment. Margin and padding values should prioritize 8px, 16px, and 24px units.
- **Density:** Components use a "compact" density model, with 36px standard heights for inputs and buttons to facilitate data-heavy entry screens.
- **Responsiveness:** Below 1024px, the sidebar collapses into a hamburger menu; padding reduces from 32px to 16px.

## Elevation & Depth

This design system avoids heavy shadows in favor of **Tonal Layers and Low-Contrast Outlines**. Depth is communicated through the stacking of surfaces and the strategic use of borders.

- **Level 0 (Background):** #F8F9FA. The foundation layer.
- **Level 1 (Surface):** #FFFFFF. Used for main content cards and the topbar. Defined by a 1px border (#E9ECEF).
- **Level 2 (Popovers/Modals):** White with a very subtle, diffused shadow (0px 4px 12px rgba(0,0,0,0.05)) and a stronger border (#CED4DA).
- **Interaction:** Hover states on rows or interactive cards use #EEF2FF rather than a shadow change, maintaining the flat, minimal aesthetic.

## Shapes

The shape language is structured to balance approachability with a professional edge. 

- **Default Radius (8px):** Applied to buttons, input fields, cards, and dropdown menus. This creates a soft but organized appearance.
- **Pill Radius (100px):** Exclusively reserved for status badges, tags, and avatars to differentiate them from interactive structural components.
- **Icons:** Use Lucide Icons with a 1.5px stroke. Icons should always be centered within their bounding box and paired with labels in most navigational contexts.

## Components

Components follow the **shadcn/ui** philosophy: unstyled functional primitives styled with the specific tokens of this design system.

- **Buttons:** 
  - Primary: Indigo background, white text. 
  - Secondary: White background, 1px border (#CED4DA), navy text.
  - Ghost: No background/border, navy text, appears on hover.
- **Inputs:** 36px height, 1px border (#E9ECEF), transitions to 1px #3B5BDB on focus with a 2px indigo-light ring.
- **Badges:** 100px radius, 12px Medium font. Use the "Light" semantic background colors (e.g., Success Light) with the dark semantic text color.
- **Data Tables:** Clean rows with 1px bottom borders. Row hover state uses #EEF2FF. Headers use Small-Medium (12px/500) typography in Neutral (#868E96).
- **Sidebar Items:** 14px Medium font, 1.5px stroke icons. Active state uses a vertical 2px Indigo bar on the far left or a subtle background tint.