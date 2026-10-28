# Developer guide

ClimWeb has shared building blocks for accessibility. Use them instead of solving the same problem again in a page template, and run the checks before opening a pull request.

## Checks to run

```bash
climweb test climweb.base.tests.test_template_a11y climweb.base.tests.test_a11y_forms climweb.base.tests.test_contrast climweb.base.tests.test_image_block
```

```bash
.venv-a11y/bin/python tools/a11y/scan.py --base-url http://localhost:8000
```

The template tests fail on `<img>` without `alt`, icon-only links or buttons without a name, and positive `tabindex`. The scan runs axe-core on rendered pages; see `tools/a11y/README.md`. Add new page types to `tools/a11y/pages.txt`.

## Page structure (`config/templates/base.html`)

- **Skip link** to `#main-content`. Page templates provide their own `<main>`; keep exactly one per page.
- **Page title:** Wagtail pages get it from page metadata. Other views set `{% block title %}`.
- **Language:** `<html lang>` comes from the site's default language setting, not the browser. `google-translate.js` updates it when a visitor switches language.
- **Status messages:** call `announce(message, assertive)` (in `common_cms.js`) to have a screen reader read a message without moving focus. Every `bulmaToast.toast()` is announced automatically.

## Focus and keyboard

- A two-tone `:focus-visible` ring is set site-wide in `base.css`. **Don't remove outlines** with `outline: none`; style the focus state instead if needed.
- Use real `<button type="button">` elements for actions and `<a href>` for navigation. A `div` or an `<a>` without `href` can't be reached by keyboard.
- Never use a positive `tabindex`.

## Shared components (`config/static/js/common_cms.js`)

These enhance existing markup automatically, so page scripts can stay as they are:

| Component | What to use | What you get |
|---|---|---|
| Filter accordions | `new Accordion(id)` with `.js-accordion-header` / `.js-accordion-body` | Headers become keyboard-operable buttons with `aria-expanded` |
| Collapsible blocks | `.ac-header` as a `<button>` inside `.ac-item` | `aria-expanded` kept in sync with `.ac-item--open` |
| Modals | Bulma `.modal`, opened by toggling `.is-active` | Dialog role and label, focus moved in and trapped, Esc closes, focus returned |
| In-page tabs | Bulma `.tabs > ul > li > a` without `href`, with `data-target`/`data-content`/`data-id` naming the panel | Tab roles, keyboard selection, `aria-selected`; also for tabs inserted after page load |
| Toggle buttons | `#list-view-button`, `#grid-view-button`, `.stn-toggle-btn` with `.active` | `aria-pressed` |
| Maps | `data-map-label="…"` on the map container | Label on the MapLibre canvas or Leaflet container |

Hover-only dropdowns (`.dropdown.is-hoverable`) also open on keyboard focus.

## Forms (`config/templates/bulma/forms/`, `base/templatetags/a11y_forms.py`)

Render forms with `{{ form|bulma }}` to get labels, fieldsets for option groups, linked errors and help text, an error summary, and `autocomplete` from field names. In custom field markup, use `{{ field|a11y_widget:'input' }}` instead of `{{ field }}`.

## Images and icons

- **Content images:** `alt="{% image_alt value.image fallback %}"` uses the editor's alt text for this use, then the image description, then your fallback, and returns empty when marked decorative.
- **StreamField image fields:** use `OptionalAltImageBlock` (`base/blocks.py`) to give editors "Alt text" and "Image is decorative".
- **Decorative images** next to text that says the same thing: `alt=""`.
- **Duplicate links**, such as a thumbnail linking to the same page as the title next to it: add `tabindex="-1" aria-hidden="true"` to the duplicate.
- **Icons:** `aria-hidden="true"` when next to text. Icon-only links and buttons need `aria-label`.

## Colour

- Secondary text uses `var(--text-muted)` (`#6b6b6b`, 5.33:1 on white). Don't introduce lighter greys.
- Check new colour pairs with `climweb.base.contrast.contrast_ratio()`: 4.5:1 for text, 3:1 for large text, icons and borders that identify controls.
- CAP severity text: `{{ severity|severity_text_color }}`, not `border_color` or `color`.
- Never use colour alone to carry meaning; add text or a label.

## Charts and maps

- **Charts** (Highcharts): load `accessibility.js`, give each chart a title (use `title: { text, style: { display: "none" } }` when a visible heading already exists), and load `exporting` + `export-data` so screen reader users get "View as data table".
- **Maps:** label every map (`data-map-label`), and make sure its information is also available as text on the page (a list, table or search). Give MapLibre markers a role: `img` for a plain pin, `button` when it opens a popup.

## Motion

- Don't auto-advance sliders or carousels.
- Animations are stopped by the `prefers-reduced-motion` block in `base.css`, and jQuery animations are turned off. For JS animations, check `matchMedia("(prefers-reduced-motion: reduce)")`.
- MapLibre animations honour reduced motion unless you pass `essential: true`; don't.

## Translations

Wrap visible text and `aria-label` values in `{% translate %}`. Strings in static JS files can't be translated with Django; pass them from the template (as a `data-` attribute or a JS variable built with `escapejs`), as the map labels do.
