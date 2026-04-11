# Design System Documentation: Smart Retail Intelligence

## 1. Overview & Creative North Star

### Creative North Star: "The Intelligent Aperture"
In the high-stakes environment of retail intelligence, data shouldn't just be displayed; it should be revealed. This design system moves away from the "boxed-in" feel of traditional enterprise dashboards, adopting a philosophy we call **The Intelligent Aperture**. 

Instead of rigid grids and heavy borders, we use light, depth, and tonal shifts to guide the eye. The interface acts as a dark lens, where the most critical retail insights glow with clinical precision. We break the "template" look by using intentional asymmetry in layout, overlapping data visualizations, and high-contrast editorial typography that commands authority.

## 2. Colors & Surface Philosophy

The color palette is anchored in deep, obsidian tones, allowing our "AI-driven" accents to pulse with importance.

### The "No-Line" Rule
**Standard 1px solid borders are prohibited for sectioning.** To define boundaries, designers must use background color shifts. 
- A section sitting on `surface` (#0b1323) should be defined by a transition to `surface_container_low` (#141b2c). 
- This creates a sophisticated, "app-like" feel that mimics high-end hardware interfaces rather than a basic web page.

### Surface Hierarchy & Nesting
Treat the UI as a series of physical layers—like stacked sheets of tinted glass.
*   **Base Layer:** `surface` (#0b1323) — The infinite void.
*   **Level 1 (Sections):** `surface_container_low` (#141b2c) — Large layout blocks.
*   **Level 2 (Cards):** `surface_container` (#182030) — Primary data units.
*   **Level 3 (Prominence):** `surface_container_highest` (#2d3546) — Hover states or active selections.

### The "Glass & Gradient" Rule
To elevate the "Smart" aspect of the brand, use Glassmorphism for floating elements (like filter drawers or tooltips). 
- **Recipe:** Use `surface_container` at 70% opacity with a `backdrop-blur` of 20px. 
- **Signature Textures:** Apply subtle linear gradients to primary action buttons (from `primary_container` #4ecad2 to `primary` #6ee6ee) at a 135-degree angle to provide a sense of energy and "glow."

## 3. Typography: Editorial Precision

We utilize **Inter** not just for legibility, but as a structural element.

*   **Display & Headlines:** Use `display-md` or `headline-lg` for high-level KPIs. These should feel like news headlines—authoritative and impossible to miss. Use `on_surface` for maximum contrast.
*   **Data Density:** For tables and shelf-maps, use `body-sm` and `label-md`. The tight tracking and slightly smaller scale allow for high information density without feeling cluttered.
*   **The Narrative Hierarchy:** 
    *   **Titles:** `title-lg` (#dbe2f9) for card headers.
    *   **Captions:** `label-sm` (#bcc9ca) for metadata and timestamps, utilizing the `on_surface_variant` to recede into the background.

## 4. Elevation & Depth

Hierarchy is achieved through **Tonal Layering** rather than shadows.

*   **The Layering Principle:** Depth is created by stacking. Place a `surface_container_lowest` card on a `surface_container_low` section. This creates a "recessed" or "inset" look, perfect for data input fields or secondary logs.
*   **Ambient Shadows:** If a component must "float" (e.g., a critical stockout alert), use an extra-diffused shadow:
    *   *Blur:* 32px | *Spread:* -4px | *Opacity:* 12% | *Color:* `surface_container_lowest` (#060e1e).
*   **The "Ghost Border" Fallback:** If accessibility requires a stroke, use a **Ghost Border**. Apply `outline_variant` (#3d494a) at 20% opacity. It should be felt, not seen.

## 5. Components

### Buttons
- **Primary:** Gradient fill (`primary_container` to `primary`). No border. `on_primary` text.
- **Secondary:** Ghost style. `outline` (#869394) at 30% opacity with `primary` text.
- **Tertiary:** Pure text with `primary` color, used for low-priority actions in dense tables.

### Chips & Status Indicators
- **In-Stock (Success):** `primary` (#6ee6ee) text on a 10% opacity `primary` background.
- **Stockout (Alert):** `error` (#ffb4ab) text on a 10% opacity `error_container` background.
- **Trend (Neutral):** `secondary` (#cecb5b) for "Shelf Movement" metrics.

### Input Fields
- **Styling:** Use `surface_container_highest` for the field background. 
- **Interaction:** On focus, the field should not have a thick border; instead, the background should shift to `surface_bright` (#31394b) with a subtle `primary` glow on the bottom edge (2px).

### Cards & Lists (The "No Divider" Rule)
Forbid the use of horizontal lines. 
- To separate list items, use 8px of vertical whitespace (`spacing-md`) or alternating tonal shifts between `surface_container_low` and `surface_container`. 

### Specialized: The "Shelf Intelligence" Heatmap
- Use a custom gradient scale from `surface_container` (0% stock) to `primary` (100% stock). Avoid muddy mid-tones; keep the colors vibrant and "lit from within."

## 6. Do's and Don'ts

### Do
- **Do** use `primary_fixed` (#7df4fc) for interactive icons to give them a "lit" appearance against the dark background.
- **Do** allow for generous "negative space" around headline KPIs to create an editorial, premium feel.
- **Do** use `md` (0.375rem) or `lg` (0.5rem) rounding for cards to soften the technical nature of the data.

### Don't
- **Don't** use pure black (#000000). Always use the `surface` tokens to maintain depth and prevent "black-hole" visual fatigue.
- **Don't** use high-contrast white borders. They break the immersion of the "Intelligent Aperture."
- **Don't** stack more than three levels of surface containers. It leads to visual "muddiness."
- **Don't** use standard "drop-shadow" presets. Only use the Ambient Shadow specification provided in Section 4.