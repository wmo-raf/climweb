# WCAG 2.1 AA conformance checklist

This checklist records how the ClimWeb **platform** meets each WCAG 2.1 level A and AA success criterion. It reflects the accessibility work released after ClimWeb 1.2.3. Use it to fill in your site's [accessibility statement](statement.md).

A site's actual conformance also depends on its content (images, videos, documents and link text that editors add) and on its brand colours. Criteria marked **Depends on content** are met by the platform when editors follow [Writing accessible content](editors.md).

## How this was evaluated

- **Automated:** axe-core 4.12 (WCAG 2.1 A/AA rules) on 14 key page types at desktop (1280px) and mobile (375px) widths, with no failures. Static template tests in the test suite check for missing image alt text, unnamed icon buttons and focus order. Both are described in `tools/a11y/README.md`.
- **Rendered checks:** colour contrast measured on rendered pages; reflow checked at 320px on 11 page types.
- **Keyboard:** menus, accordions, tabs, dialogs, autocompletes, sliders and forms operated with the keyboard during development.
- **Not yet done:** a full manual pass with screen readers (NVDA, JAWS, VoiceOver, TalkBack). Complete the [manual testing checklist](manual-testing.md) before claiming full conformance.

## Status key

| Status | Meaning |
|---|---|
| **Supports** | The platform meets the criterion |
| **Partially supports** | Most of the platform meets it; known exceptions are listed |
| **Depends on content** | The platform supports it; meeting it depends on what editors publish |
| **Not applicable** | ClimWeb has no content the criterion applies to |
| **Not yet verified** | Not yet tested; treat as unknown |

## Level A

| Criterion | Status | Notes |
|---|---|---|
| 1.1.1 Non-text Content | Supports / Depends on content | Platform images, icons, charts and maps have text alternatives: charts have a title and "View as data table"; climate stripes have a text summary; maps are labelled, with their information also given as text. Content images use the editor's alt text or image description. |
| 1.2.1 Audio-only and Video-only | Depends on content | Audio playlists and videos need a transcript or description from editors. |
| 1.2.2 Captions (Prerecorded) | Depends on content | YouTube embeds show YouTube's captions; editors must add them in YouTube. |
| 1.2.3 Audio Description or Media Alternative | Depends on content | |
| 1.3.1 Info and Relationships | Supports | Landmarks, headings, labelled form fields, fieldsets for option groups, tables with headers, ARIA for tabs, accordions and dialogs. |
| 1.3.2 Meaningful Sequence | Supports | |
| 1.3.3 Sensory Characteristics | Depends on content | Platform instructions don't rely on shape, colour or position alone. |
| 1.4.1 Use of Color | Supports | CAP warning severity is always written as text; map legends pair colours with labels. |
| 1.4.2 Audio Control | Supports | No audio plays automatically. |
| 2.1.1 Keyboard | Supports | Individual features drawn on maps can't be focused; the same information and actions are available through search, lists and tables on each map page. |
| 2.1.2 No Keyboard Trap | Supports | Dialogs keep focus inside them while open, and Esc closes them. |
| 2.1.4 Character Key Shortcuts | Supports | No single-key shortcuts. |
| 2.2.1 Timing Adjustable | Partially supports | Forms have no time limits. Confirmation messages close after 2.5 seconds; error messages stay 8 seconds and can be dismissed. All are announced to screen readers when they appear. |
| 2.2.2 Pause, Stop, Hide | Supports | Nothing moves or updates on its own except the satellite imagery auto-update, which has an on/off switch. |
| 2.3.1 Three Flashes or Below Threshold | Supports | |
| 2.4.1 Bypass Blocks | Supports | "Skip to main content" link. |
| 2.4.2 Page Titled | Supports | |
| 2.4.3 Focus Order | Supports | No positive `tabindex` (checked by the test suite). |
| 2.4.4 Link Purpose (In Context) | Depends on content | Platform links and icon buttons are named. Editors should avoid "click here". |
| 2.5.1 Pointer Gestures | Supports | Maps have zoom buttons and keyboard panning; sliders have Previous/Next buttons. |
| 2.5.2 Pointer Cancellation | Supports | |
| 2.5.3 Label in Name | Supports | Accessible names start with the visible text. |
| 2.5.4 Motion Actuation | Not applicable | |
| 3.1.1 Language of Page | Supports | Set from the site's default language; updated when a visitor switches language. |
| 3.2.1 On Focus | Supports | |
| 3.2.2 On Input | Partially supports | Listing filters (publications, products, projects, tenders, vacancies, glossary, daily reports) reload the page as soon as a checkbox changes, without advance notice. |
| 3.3.1 Error Identification | Supports | Form errors are shown next to each field, linked to it, and listed in a summary that receives focus. |
| 3.3.2 Labels or Instructions | Supports | Every field is labelled; required fields are marked and explained. |
| 4.1.1 Parsing | Supports | Removed in WCAG 2.2. |
| 4.1.2 Name, Role, Value | Supports | Third-party widgets (Google Translate, reCAPTCHA, YouTube) are the vendors' responsibility. |

## Level AA

| Criterion | Status | Notes |
|---|---|---|
| 1.2.4 Captions (Live) | Not applicable | Unless a site streams live video. |
| 1.2.5 Audio Description (Prerecorded) | Depends on content | |
| 1.3.4 Orientation | Supports | |
| 1.3.5 Identify Input Purpose | Supports | Name, email, phone, organisation and address fields have `autocomplete`. |
| 1.4.3 Contrast (Minimum) | Supports | With the default theme. The Theme settings warn when a chosen colour is below 4.5:1, and light tints are computed to pass. |
| 1.4.4 Resize Text | Supports | Content reflows at 320px, the width of 400% zoom. |
| 1.4.5 Images of Text | Depends on content | Bulletins uploaded as images should also be published as text or PDF. |
| 1.4.10 Reflow | Supports | Checked at 320px on 11 page types: no sideways scrolling or clipped text. |
| 1.4.11 Non-text Contrast | Partially supports | Focus ring, icons, buttons and chart marks pass. **Search and form field borders** are light grey (1.2–1.4:1); this was kept as a design decision. |
| 1.4.12 Text Spacing | Not yet verified | |
| 1.4.13 Content on Hover or Focus | Not yet verified | Menu dropdowns stay open while hovered and close with Esc. Chart tooltips and map popups haven't been checked. |
| 2.4.5 Multiple Ways | Supports | Main menu, footer menu and site search. |
| 2.4.6 Headings and Labels | Depends on content | Platform headings and labels are descriptive. |
| 2.4.7 Focus Visible | Supports | A two-tone focus ring on every focusable element. |
| 3.1.2 Language of Parts | Supports | Language options are marked with their own language. Passages in another language in editor content depend on content. |
| 3.2.3 Consistent Navigation | Supports | |
| 3.2.4 Consistent Identification | Supports | |
| 3.3.3 Error Suggestion | Supports | |
| 3.3.4 Error Prevention (Legal, Financial, Data) | Not applicable | Public forms don't create legal or financial commitments. |
| 4.1.3 Status Messages | Supports | Toasts, search result counts, form errors and copy confirmations are announced. |

## Known limitations

| Limitation | Criteria | Plan |
|---|---|---|
| Listing filters reload the page on change without advance notice | 3.2.2 | Add a short note above the filters ("Results update when you change a filter"), or an Apply button |
| Search and form field borders below 3:1 | 1.4.11 | Darken to `#8a8a8a` if the design allows |
| Confirmation messages close after 2.5 seconds | 2.2.1 | Keep confirmations until dismissed, or show them on the page |
| Text spacing and hover/focus content not yet tested | 1.4.12, 1.4.13 | Include in the next manual test pass |
| CAP alert widgets (top banner, alerts list, email, PDF) come from cap-composer | 1.4.3 | Fixed in cap-composer after 1.3.6. Upgrade cap-composer to pick it up; ClimWeb's own alert list already passes |
| Some map and slider labels on the home map are English-only in Arabic, Amharic and Swahili | 3.1.2 | Add translations to the home map locale files |
| Home map zoom buttons are named "+" and "−" | 2.4.6 | Add `aria-label` "Zoom in" / "Zoom out" in `Map.vue` and rebuild |
| Screen reader pass not yet completed | All | Complete the [manual testing checklist](manual-testing.md) |
