# RTL Audit — ClimWeb (YouthxGrowth 2026 / Arabic track)

> **Note on issue #542:** The public GitHub issue #542 (`wmo-raf/climweb`) is titled
> "Social share of MapViewer not working on Mobile" — unrelated to RTL.
> The **open** RTL issue is **#590** ("Alert blinking too close to text in Arabic version").
> Closed RTL prior art: #368 (RTL Styling for ar language), #376 (RTL lang fix),
> #387 (icon-text spacing), #524 (spacing follow-up).
> _(This audit was originally scoped as issue #542 internally.)_

**Author:** Ow Zheng Wei — YouthxGrowth 2026 Fellow (Arabic/RTL Track)  
**Date:** 2026-05-25  
**Issue reference:** #590 (open) + prior closed: #368, #376, #387, #524  
**Branch:** `main` (commit `ec5b5c09`)  
**Scope:** All Django HTML templates + CSS files under `climweb/src/climweb/`

---

## Audit Methodology

Grepped for the following LTR-hardcoded CSS properties across every `.html` and `.css` file
in the source tree (minified vendor files excluded):

- `margin-left` / `margin-right`
- `padding-left` / `padding-right`
- `text-align: left` / `text-align:left`
- `float: left` / `float: right`
- `direction:` (excluding `flex-direction`)

RTL fix strategy for each type:
| LTR property | RTL-safe replacement |
|---|---|
| `margin-left: Xpx` | `margin-inline-start: Xpx` |
| `margin-right: Xpx` | `margin-inline-end: Xpx` |
| `padding-left: Xpx` | `padding-inline-start: Xpx` |
| `padding-right: Xpx` | `padding-inline-end: Xpx` |
| `text-align: left` | `text-align: start` |
| `float: left` | `float: inline-start` (or use flexbox) |
| `float: right` | `float: inline-end` (or use flexbox) |

---

## Summary

| Category                    | Template hits  | CSS hits                 | Total   |
| --------------------------- | -------------- | ------------------------ | ------- |
| `margin-left`               | 4              | 11 (excl. Bulma grid)    | 15      |
| `margin-right`              | 9              | 22                       | 31      |
| `padding-left`              | 11             | 32                       | 43      |
| `padding-right`             | 0              | 17                       | 17      |
| `text-align: left`          | 1 (admin only) | 9                        | 10      |
| `float: left/right`         | 5              | 4                        | 9       |
| `direction:` (LTR override) | 0              | 3 (incl. 2 `ltr` resets) | 3       |
| **TOTAL actionable**        | **30**         | **98**                   | **128** |

> **Note:** `bulma-grid-only.css` contains ~100 `margin-left` entries for the Bulma CSS grid offset
> classes. These are third-party framework utilities and require a separate Bulma RTL solution
> (e.g., `bulma-rtl` or `@mixin` overrides). They are counted separately below, not in the
> actionable total above.

---

## 🔴 HIGH Priority — Navigation, Header, Sitewide UI

These affect every page load and are the most visible RTL regressions.

### H-01 · Navigation bar — icon spacing in navbar

**File:** [climweb/src/climweb/config/templates/navigation/app_navbar.html:26](climweb/src/climweb/config/templates/navigation/app_navbar.html#L26)  
**Type:** Template — `margin-right` inline style  
**Category:** Navigation element (icon-text pair)

```html
<span style="margin-right: 4px"> {% translate "Alerts" %} </span>
```

**RTL issue:** The 4 px gap between the bell icon and "Alerts" label will be on the wrong side in RTL.  
**Fix:** Replace with `margin-inline-end: 4px`.  
**Priority:** 🔴 HIGH

---

### H-02 · Navigation CSS — left margin on nav items

**File:** [climweb/src/climweb/config/static/css/navigation.css:30](climweb/src/climweb/config/static/css/navigation.css#L30)  
**Type:** CSS — `margin-left`  
**Category:** Navigation layout container

```css
margin-left: 8px;
```

**RTL issue:** Nav item indent will be on the wrong side.  
**Fix:** `margin-inline-start: 8px`  
**Priority:** 🔴 HIGH

---

### H-03 · Navigation CSS — submenu indent

**File:** [climweb/src/climweb/config/static/css/navigation.css:674](climweb/src/climweb/config/static/css/navigation.css#L674)  
**Type:** CSS — `margin-left`  
**Category:** Navigation layout container

```css
margin-left: 2rem;
```

**RTL issue:** Submenu will indent to the left instead of the right in RTL.  
**Fix:** `margin-inline-start: 2rem`  
**Priority:** 🔴 HIGH

---

### H-04 · Navigation CSS — nav list padding

**File:** [climweb/src/climweb/config/static/css/navigation.css:1280](climweb/src/climweb/config/static/css/navigation.css#L1280)  
**Type:** CSS — `padding-left`  
**Category:** Navigation layout container

```css
padding-left: 8px;
```

**RTL issue:** Left-side nav padding causes misalignment on RTL.  
**Fix:** `padding-inline-start: 8px`  
**Priority:** 🔴 HIGH

---

### H-05 · Navigation CSS — breadcrumb separator margin

**File:** [climweb/src/climweb/config/static/css/navigation.css:1282](climweb/src/climweb/config/static/css/navigation.css#L1282)  
**Type:** CSS — `margin-left`  
**Category:** Navigation element

```css
margin-left: 23px;
```

**RTL issue:** Breadcrumb indentation will be on wrong side.  
**Fix:** `margin-inline-start: 23px`  
**Priority:** 🔴 HIGH

---

### H-06 · Navigation CSS — icon right margin (multiple)

**File:** [climweb/src/climweb/config/static/css/navigation.css:134](climweb/src/climweb/config/static/css/navigation.css#L134)  
**Type:** CSS — `margin-right`  
**Category:** Navigation element

```css
margin-right: 0;
```

**RTL issue:** Resets LTR-specific margin without equivalent RTL reset.  
**Fix:** `margin-inline-end: 0`  
**Priority:** 🔴 HIGH

---

### H-07 · Sections CSS — `direction: ltr` override inside content areas

**File:** [climweb/src/climweb/config/static/css/sections.css:41](climweb/src/climweb/config/static/css/sections.css#L41) and [line 139](climweb/src/climweb/config/static/css/sections.css#L139)  
**Type:** CSS — `direction: ltr` hardcoded  
**Category:** Layout container (used sitewide)

```css
/* line 41 */
direction: ltr;
/* line 139 */
direction: ltr;
```

**RTL issue:** These explicitly force LTR in areas that should respect `direction: rtl` when the
page language is Arabic. The `direction: rtl` on line 37 will be overridden.  
**Fix:** Remove or wrap in `[dir="ltr"]` selector; rely on the `<html dir="rtl">` attribute
instead.  
**Priority:** 🔴 HIGH

---

### H-08 · Base CSS — global element right margin

**File:** [climweb/src/climweb/config/static/css/base.css:177](climweb/src/climweb/config/static/css/base.css#L177)  
**Type:** CSS — `margin-right`  
**Category:** Layout container (sitewide)

```css
margin-right: 10px;
```

**RTL issue:** Applied globally; will misalign icons/badges in RTL.  
**Fix:** `margin-inline-end: 10px`  
**Priority:** 🔴 HIGH

---

### H-09 · Home hero banner — massive LTR padding

**File:** [climweb/src/climweb/pages/home/static/css/home.css:66](climweb/src/climweb/pages/home/static/css/home.css#L66) and lines 95, 115, 131, 145  
**Type:** CSS — `padding-left` (100px, 85px, 80px, 70px, 65px at different breakpoints)  
**Category:** Homepage — hero banner

```css
padding-left: 100px   /* base */
padding-left: 85px    /* tablet */
padding-left: 80px    /* etc */
```

**RTL issue:** The entire hero text block is indented from the left with hardcoded pixel values.
In RTL, text should be indented from the right.  
**Fix:** Replace all with `padding-inline-start: <value>`  
**Priority:** 🔴 HIGH

---

### H-10 · Home CSS — language flag `float: right`

**File:** [climweb/src/climweb/pages/home/static/css/home.css:11](climweb/src/climweb/pages/home/static/css/home.css#L11)  
**Type:** CSS — `float: right`  
**Category:** Navigation element

```css
float: right;
```

**RTL issue:** Language switcher flag already floated right — but this is done with `float` not
logical properties, so a surrounding RTL layout won't reverse it automatically.  
**Fix:** Use flexbox `justify-content: flex-end` or `margin-inline-start: auto`.  
**Priority:** 🔴 HIGH

---

## 🟡 MEDIUM Priority — Homepage, Listings, Content Sections

### M-01 · Homepage — climate section `text-align: left`

**File:** [climweb/src/climweb/pages/home/static/css/climate.css:73](climweb/src/climweb/pages/home/static/css/climate.css#L73) and [line 87](climweb/src/climweb/pages/home/static/css/climate.css#L87)  
**Type:** CSS — `text-align: left`  
**Category:** Homepage content section

```css
text-align: left; /* line 73 */
text-align: left; /* line 87 */
```

**Fix:** `text-align: start`  
**Priority:** 🟡 MEDIUM

---

### M-02 · Homepage — forecast widget `text-align: left`

**File:** [climweb/src/climweb/pages/home/static/css/forecast_widget.css:55](climweb/src/climweb/pages/home/static/css/forecast_widget.css#L55)  
**Type:** CSS — `text-align: left`  
**Category:** Homepage content section

```css
text-align: left;
```

**Fix:** `text-align: start`  
**Priority:** 🟡 MEDIUM

---

### M-03 · Homepage — forecast widget `padding-right`

**File:** [climweb/src/climweb/pages/home/static/css/forecast_widget.css:79](climweb/src/climweb/pages/home/static/css/forecast_widget.css#L79)  
**Type:** CSS — `padding-right`  
**Category:** Homepage forecast widget

```css
padding-right: 10px;
```

**Fix:** `padding-inline-end: 10px`  
**Priority:** 🟡 MEDIUM

---

### M-04 · Homepage — climate icon `margin-right`

**File:** [climweb/src/climweb/pages/home/static/css/climate.css:97](climweb/src/climweb/pages/home/static/css/climate.css#L97)  
**Type:** CSS — `margin-right` (icon-text pair)  
**Category:** Homepage content section

```css
margin-right: 0.5em;
```

**Fix:** `margin-inline-end: 0.5em`  
**Priority:** 🟡 MEDIUM

---

### M-05 · Homepage — nav `margin-right` in content section

**File:** [climweb/src/climweb/pages/home/static/css/home.css:690](climweb/src/climweb/pages/home/static/css/home.css#L690) and [line 717](climweb/src/climweb/pages/home/static/css/home.css#L717)  
**Type:** CSS — `margin-right`  
**Category:** Homepage listing

```css
margin-right: 4px; /* line 690 — icon spacing */
margin-right: 20px; /* line 717 — card meta item */
```

**Fix:** `margin-inline-end: 4px` / `margin-inline-end: 20px`  
**Priority:** 🟡 MEDIUM

---

### M-06 · Hero banner template — `met_banner` left margin

**File:** [climweb/src/climweb/pages/home/templates/home/hero_types/met_banner.html:276](climweb/src/climweb/pages/home/templates/home/hero_types/met_banner.html#L276)  
**Type:** Template — `margin-left: auto` inline style  
**Category:** Homepage hero container

```html
style="margin-left: auto;"
```

**RTL issue:** `margin-left: auto` is used for centering which works in LTR but breaks in RTL
where `margin-right: auto` would be needed.  
**Fix:** Replace with `margin-inline-start: auto` (logical auto margin works in both directions).  
**Priority:** 🟡 MEDIUM

---

### M-07 · News listing card — `padding-left:0` conditional

**File:** [climweb/src/climweb/pages/news/templates/card_items_inline_include.html:26](climweb/src/climweb/pages/news/templates/card_items_inline_include.html#L26) and [line 54](climweb/src/climweb/pages/news/templates/card_items_inline_include.html#L54)  
**Type:** Template — `padding-left` inline style  
**Category:** Medium priority — news/media listings

```html
style="{% if show_thumbnail == False %}padding-left:0;{% endif %}"
style="padding-left: 0"
```

**Fix:** Change to `padding-inline-start:0`  
**Priority:** 🟡 MEDIUM

---

### M-08 · Mediacenter listing — same `padding-left:0` pattern

**File:** [climweb/src/climweb/pages/mediacenter/templates/news_include.html:25](climweb/src/climweb/pages/mediacenter/templates/news_include.html#L25)  
**Type:** Template — `padding-left` inline style  
**Category:** Media center listing

```html
style="{% if show_thumbnail == False %}padding-left:0;{% endif %}"
```

**Fix:** `padding-inline-start:0`  
**Priority:** 🟡 MEDIUM

---

### M-09 · News article external link icon spacing

**File:** [climweb/src/climweb/pages/news/templates/external_link_block.html:5](climweb/src/climweb/pages/news/templates/external_link_block.html#L5)  
**Type:** Template — `margin-right` inline style (icon-text pair)  
**Category:** News detail — content block

```html
<span class="icon" style="margin-right: 4px"></span>
```

**RTL issue:** External link icon gap is on wrong side for RTL.  
**Fix:** `margin-inline-end: 4px`  
**Priority:** 🟡 MEDIUM

---

### M-10 · News detail CSS — float left/right for images

**File:** [climweb/src/climweb/pages/news/static/css/news_detail.css:304](climweb/src/climweb/pages/news/static/css/news_detail.css#L304) and [line 313](climweb/src/climweb/pages/news/static/css/news_detail.css#L313)  
**Type:** CSS — `float: left` / `float: right`  
**Category:** News article detail page

```css
float: left; /* line 304 — left-floated image in article body */
float: right; /* line 313 — right-floated image in article body */
```

**RTL issue:** Floated images in article body won't mirror in RTL.  
**Fix:** Use `float: inline-start` / `float: inline-end` (CSS Logical Properties Level 1)  
**Priority:** 🟡 MEDIUM

---

### M-11 · Dashboard `text-align: left`

**File:** [climweb/src/climweb/pages/dashboards/static/css/dashboard.css:45](climweb/src/climweb/pages/dashboards/static/css/dashboard.css#L45) and [line 49](climweb/src/climweb/pages/dashboards/static/css/dashboard.css#L49)  
**Type:** CSS — `text-align: left`  
**Category:** Dashboard listing

```css
text-align: left; /* line 45 */
text-align: left; /* line 49 */
```

**Fix:** `text-align: start`  
**Priority:** 🟡 MEDIUM

---

### M-12 · Sections CSS — `padding-left` on shared content containers

**File:** [climweb/src/climweb/config/static/css/sections.css:806](climweb/src/climweb/config/static/css/sections.css#L806), [line 889](climweb/src/climweb/config/static/css/sections.css#L889), [line 903](climweb/src/climweb/config/static/css/sections.css#L903), [line 1134](climweb/src/climweb/config/static/css/sections.css#L1134), [line 1256](climweb/src/climweb/config/static/css/sections.css#L1256)  
**Type:** CSS — `padding-left` (5 instances)  
**Category:** Shared section layout containers

```css
padding-left: 1.75rem; /* line 806 */
padding-left: 1.25rem; /* line 889 */
padding-left: 1rem; /* line 903 */
padding-left: 6px; /* line 1134 */
padding-left: 4px; /* line 1256 */
```

**Fix:** All → `padding-inline-start: <value>`  
**Priority:** 🟡 MEDIUM

---

### M-13 · Sections CSS — `padding-right` symmetric instances

**File:** [climweb/src/climweb/config/static/css/sections.css:1135](climweb/src/climweb/config/static/css/sections.css#L1135) and [line 1257](climweb/src/climweb/config/static/css/sections.css#L1257)  
**Type:** CSS — `padding-right`  
**Category:** Shared section layout containers

```css
padding-right: 6px; /* line 1135 */
padding-right: 4px; /* line 1257 */
```

**Fix:** `padding-inline-end: 6px` / `padding-inline-end: 4px`  
**Priority:** 🟡 MEDIUM

---

### M-14 · Services common — `padding-left` icon column

**File:** [climweb/src/climweb/config/static/css/services_common.css:16](climweb/src/climweb/config/static/css/services_common.css#L16), [line 39](climweb/src/climweb/config/static/css/services_common.css#L39), [line 63](climweb/src/climweb/config/static/css/services_common.css#L63), [line 156](climweb/src/climweb/config/static/css/services_common.css#L156)  
**Type:** CSS — `padding-left` (4 instances)  
**Category:** Services listing

```css
padding-left: 70px; /* icon column offset — line 16 */
padding-left: 20px; /* line 39 */
padding-left: 40px; /* line 63 */
padding-left: 20px; /* line 156 */
```

**RTL issue:** Large icon offsets (40–70 px) will place content off-screen in RTL.  
**Fix:** `padding-inline-start: <value>`  
**Priority:** 🟡 MEDIUM

---

### M-15 · Services common — `margin-right` service card

**File:** [climweb/src/climweb/config/static/css/services_common.css:89](climweb/src/climweb/config/static/css/services_common.css#L89)  
**Type:** CSS — `margin-right`  
**Category:** Services listing

```css
margin-right: 20px;
```

**Fix:** `margin-inline-end: 20px`  
**Priority:** 🟡 MEDIUM

---

### M-16 · About page — `padding-left` and `text-align: left` (multiple)

**File:** [climweb/src/climweb/pages/organisation_pages/about/static/css/about.css](climweb/src/climweb/pages/organisation_pages/about/static/css/about.css) — lines 256, 298, 307, 432, 465, 486, 488, 502  
**Type:** CSS — `padding-left`, `text-align: left`, `padding-right`  
**Category:** About/Organisation listing

```css
padding-left: 2rem; /* line 256 */
padding-left: 1.5rem; /* line 298 */
text-align: left; /* line 431, 486 */
padding-left: 40px; /* line 465 — timeline row */
padding-left: 0.5rem; /* line 488, 502 */
padding-right: 1.5rem; /* line 427 */
```

**RTL issue:** The timeline layout uses hardcoded left-indent which will misplace year labels in RTL.  
**Fix:** Use logical properties throughout (`padding-inline-start`, `text-align: start`)  
**Priority:** 🟡 MEDIUM

---

### M-17 · CMS admin stylesheet — `text-align: left` in table

**File:** [climweb/src/climweb/config/static/css/cms_style.css:435](climweb/src/climweb/config/static/css/cms_style.css#L435)  
**Type:** CSS — `text-align: left`  
**Category:** Admin UI (medium — only editors see this)

```css
text-align: left;
```

**Fix:** `text-align: start`  
**Priority:** 🟡 MEDIUM

---

### M-18 · CMS admin stylesheet — `margin-left` / `margin-right` (multiple)

**File:** [climweb/src/climweb/config/static/css/cms_style.css](climweb/src/climweb/config/static/css/cms_style.css) — lines 284, 449, 490, 540, 613, 637, 763, 805  
**Type:** CSS — mixed directional margins  
**Category:** Admin UI

```css
margin-left: 8px; /* line 284 — icon spacing */
margin-left: 20px; /* line 449 */
margin-left: 4px; /* line 490 — icon-text pair */
margin-right: 10px; /* line 540 */
margin-right: 10px; /* line 613 */
margin-right: 20px; /* line 637 */
margin-right: 20px; /* line 763 */
margin-right: 10px; /* line 805 */
```

**Fix:** All → logical property equivalents  
**Priority:** 🟡 MEDIUM

---

### M-19 · CMS admin — `float: left`

**File:** [climweb/src/climweb/config/static/css/cms_style.css:906](climweb/src/climweb/config/static/css/cms_style.css#L906)  
**Type:** CSS — `float: left`  
**Category:** Admin UI

```css
float: left;
```

**Fix:** `float: inline-start`  
**Priority:** 🟡 MEDIUM

---

### M-20 · CMS admin `plugin_manager.html` — `text-align: left`

**File:** [climweb/src/climweb/base/templates/admin/plugin_manager.html:15](climweb/src/climweb/base/templates/admin/plugin_manager.html#L15)  
**Type:** Template — `text-align: left`  
**Category:** Admin UI

```html
style="text-align: left;"
```

**Fix:** `text-align: start`  
**Priority:** 🟡 MEDIUM

---

### M-21 · Email subscription — `float:left` on form labels (JS-generated)

**File:** [climweb/src/climweb/pages/email_subscription/templates/subscriber_integration_js.html:26](climweb/src/climweb/pages/email_subscription/templates/subscriber_integration_js.html#L26), [line 68](climweb/src/climweb/pages/email_subscription/templates/subscriber_integration_js.html#L68)  
**File:** [climweb/src/climweb/pages/email_subscription/templates/subscriber_optin_js.html:35](climweb/src/climweb/pages/email_subscription/templates/subscriber_optin_js.html#L35), [line 77](climweb/src/climweb/pages/email_subscription/templates/subscriber_optin_js.html#L77)  
**File:** [climweb/src/climweb/pages/email_subscription/templates/subscriber_integration_widget.html:13](climweb/src/climweb/pages/email_subscription/templates/subscriber_integration_widget.html#L13)  
**Type:** Template — `float:left` in JS-generated HTML strings  
**Category:** Subscription form (medium — used on homepage and dedicated page)

```javascript
merge_field_html += '<label style="float:left;">' + ...
interest_category_field_html += '<br /><label style="float:left;">' + ...
```

**RTL issue:** JS-generated inline styles hardcode LTR float; won't respond to HTML dir attribute.  
**Fix:** Use a CSS class instead of inline style; set `float: inline-start` in the CSS class.  
**Priority:** 🟡 MEDIUM

---

### M-22 · Email subscription — `padding-left` on interests section

**File:** [climweb/src/climweb/pages/email_subscription/templates/subscriber_optin_widget.html:19](climweb/src/climweb/pages/email_subscription/templates/subscriber_optin_widget.html#L19) and [line 32](climweb/src/climweb/pages/email_subscription/templates/subscriber_optin_widget.html#L32)  
**Type:** Template — `padding-left` inline style  
**Category:** Subscription form

```html
<div style="padding-left: 30px" id="interests_section">
  <span style="padding-left: 10px">{{ value }}</span>
</div>
```

**Fix:** `padding-inline-start: 30px` / `padding-inline-start: 10px`  
**Priority:** 🟡 MEDIUM

---

## 🟢 LOW Priority — Detail Pages, Specialty Pages

### L-01 · Events detail — `margin-right` on event icon-text pairs

**File:** [climweb/src/climweb/pages/events/templates/event_registration_page.html:47](climweb/src/climweb/pages/events/templates/event_registration_page.html#L47) and [line 54](climweb/src/climweb/pages/events/templates/event_registration_page.html#L54)  
**File:** [climweb/src/climweb/pages/events/templates/event_sessions_include.html:41](climweb/src/climweb/pages/events/templates/event_sessions_include.html#L41), [line 59](climweb/src/climweb/pages/events/templates/event_sessions_include.html#L59)  
**File:** [climweb/src/climweb/pages/events/templates/zoom_events_details_include.html:41](climweb/src/climweb/pages/events/templates/zoom_events_details_include.html#L41), [line 59](climweb/src/climweb/pages/events/templates/zoom_events_details_include.html#L59), [line 119](climweb/src/climweb/pages/events/templates/zoom_events_details_include.html#L119)  
**Type:** Template — `margin-right` / `margin-left` inline styles (icon-text pairs)  
**Category:** Events detail

```html
<span class="icon event-meta-item-icon" style="margin-right: 8px">
  margin-right: 4px; margin-right: 0; margin-left: 24px;</span
>
```

**Fix:** All → `margin-inline-end` / `margin-inline-start`  
**Priority:** 🟢 LOW

---

### L-02 · Events CSS — event detail margin/padding

**File:** [climweb/src/climweb/pages/events/static/css/event_detail.css](climweb/src/climweb/pages/events/static/css/event_detail.css) — lines 17, 53, 84, 117, 140, 149  
**Type:** CSS — mixed directional spacing  
**Category:** Events detail page

```css
padding-left: 10px; /* line 17 */
padding-left: 8px; /* line 53 */
padding-left: 30px; /* line 84 */
margin-right: 20px; /* line 117 */
margin-right: 0; /* line 140 */
padding-left: 20px; /* line 149 */
```

**Fix:** Use logical properties throughout  
**Priority:** 🟢 LOW

---

### L-03 · Publications / Document detail — `padding-left` on document icon

**File:** [climweb/src/climweb/config/static/css/document_detail.css](climweb/src/climweb/config/static/css/document_detail.css) — lines 11, 22, 141, 168  
**Type:** CSS — `padding-left`  
**Category:** Publications / Documents detail

```css
padding-left: 0; /* line 11 */
padding-left: 50px; /* line 22 — document icon offset */
padding-left: 8px; /* line 141 */
padding-left: 0.75rem; /* line 168 */
```

**RTL issue:** The 50 px icon offset will push the document title away from the icon in RTL.  
**Fix:** `padding-inline-start: 50px`  
**Priority:** 🟢 LOW

---

### L-04 · Document detail — `margin-right` metadata

**File:** [climweb/src/climweb/config/static/css/document_detail.css:78](climweb/src/climweb/config/static/css/document_detail.css#L78) and [line 123](climweb/src/climweb/config/static/css/document_detail.css#L123)  
**Type:** CSS — `margin-right`  
**Category:** Publications detail

```css
margin-right: 10px; /* line 78 */
margin-right: 20px; /* line 123 */
```

**Fix:** `margin-inline-end: 10px` / `margin-inline-end: 20px`  
**Priority:** 🟢 LOW

---

### L-05 · Forecast CSS — `padding-left` on forecast value column

**File:** [climweb/src/climweb/config/static/css/forecast.css:109](climweb/src/climweb/config/static/css/forecast.css#L109) and [line 150](climweb/src/climweb/config/static/css/forecast.css#L150)  
**Type:** CSS — `padding-left`  
**Category:** Weather/forecast detail

```css
padding-left: 30px; /* line 109 */
padding-left: 0; /* line 150 */
```

**Fix:** `padding-inline-start: 30px`  
**Priority:** 🟢 LOW

---

### L-06 · Weather detail page — `padding-left` / `text-align: left`

**File:** [climweb/src/climweb/pages/weather/static/weather/css/weather_detail_page.css:77](climweb/src/climweb/pages/weather/static/weather/css/weather_detail_page.css#L77) and [line 217](climweb/src/climweb/pages/weather/static/weather/css/weather_detail_page.css#L217)  
**Type:** CSS  
**Category:** Weather detail page

```css
padding-left: 32px !important; /* line 77 */
text-align: left; /* line 217 */
```

**Fix:** `padding-inline-start: 32px !important` / `text-align: start`  
**Priority:** 🟢 LOW

---

### L-07 · Weather forecast widget — `padding-left` / `margin-right`

**File:** [climweb/src/climweb/pages/weather/static/weather/css/forecast_widget.css:130](climweb/src/climweb/pages/weather/static/weather/css/forecast_widget.css#L130), [line 491](climweb/src/climweb/pages/weather/static/weather/css/forecast_widget.css#L491)  
**Type:** CSS  
**Category:** Weather forecast widget

```css
padding-left: 28px !important; /* line 130 */
margin-right: 0 !important; /* line 491 */
```

**Fix:** Logical property equivalents  
**Priority:** 🟢 LOW

---

### L-08 · Products CSS — `margin-left` / `margin-right` on product cards

**File:** [climweb/src/climweb/pages/products/static/products/css/product.css](climweb/src/climweb/pages/products/static/products/css/product.css) — lines 117, 146, 154  
**Type:** CSS  
**Category:** Products listing/detail

```css
margin-left: 10px; /* line 117 */
margin-right: 12px; /* line 146 */
margin-left: 8px; /* line 154 — icon-text pair */
```

**Fix:** Logical property equivalents  
**Priority:** 🟢 LOW

---

### L-09 · Tenders & Vacancies — `margin-right` on meta icons

**File:** [climweb/src/climweb/pages/organisation_pages/tenders/static/css/tenders.css:22](climweb/src/climweb/pages/organisation_pages/tenders/static/css/tenders.css#L22), [line 84](climweb/src/climweb/pages/organisation_pages/tenders/static/css/tenders.css#L84)  
**File:** [climweb/src/climweb/pages/organisation_pages/vacancies/static/css/vacancies.css:22](climweb/src/climweb/pages/organisation_pages/vacancies/static/css/vacancies.css#L22), [line 76](climweb/src/climweb/pages/organisation_pages/vacancies/static/css/vacancies.css#L76)  
**Type:** CSS — `margin-right`  
**Category:** Organisation detail pages

```css
margin-right: 20px; /* tenders/vacancies card icon spacing */
margin-right: 10px;
```

**Fix:** `margin-inline-end`  
**Priority:** 🟢 LOW

---

### L-10 · Stations detail — `text-align: left` on data table

**File:** [climweb/src/climweb/pages/stations/static/stations/css/stations_detail_page.css:309](climweb/src/climweb/pages/stations/static/stations/css/stations_detail_page.css#L309)  
**Type:** CSS — `text-align: left`  
**Category:** Stations detail page

```css
.std-row-val {
  text-align: left;
}
```

**Fix:** `text-align: start`  
**Priority:** 🟢 LOW

---

### L-11 · Contact page — `padding-left` on form layout

**File:** [climweb/src/climweb/pages/contact/static/css/contact_page.css:221](climweb/src/climweb/pages/contact/static/css/contact_page.css#L221)  
**Type:** CSS — `padding-left`  
**Category:** Contact page

```css
padding-left: 40px;
```

**Fix:** `padding-inline-start: 40px`  
**Priority:** 🟢 LOW

---

### L-12 · Feedback CSS — `margin-left` resets

**File:** [climweb/src/climweb/pages/feedback/static/feedback/css/feedback.css:169](climweb/src/climweb/pages/feedback/static/feedback/css/feedback.css#L169), [line 177](climweb/src/climweb/pages/feedback/static/feedback/css/feedback.css#L177), [line 187](climweb/src/climweb/pages/feedback/static/feedback/css/feedback.css#L187)  
**Type:** CSS  
**Category:** Feedback detail page

```css
margin-left: 0; /* line 169, 177 */
margin-left: 2px; /* line 187 */
```

**Fix:** `margin-inline-start: 0` / `margin-inline-start: 2px`  
**Priority:** 🟢 LOW

---

### L-13 · Data request — `padding-right` / `padding-left`

**File:** [climweb/src/climweb/pages/data_request/static/css/datarequest.css:16](climweb/src/climweb/pages/data_request/static/css/datarequest.css#L16), [line 44](climweb/src/climweb/pages/data_request/static/css/datarequest.css#L44), [line 51](climweb/src/climweb/pages/data_request/static/css/datarequest.css#L51), [line 73](climweb/src/climweb/pages/data_request/static/css/datarequest.css#L73)  
**Type:** CSS  
**Category:** Data request page

```css
padding-right: 70px; /* line 16 — large icon offset */
margin-left: 0; /* line 44, 51 */
padding-right: 0.75rem; /* line 73 */
```

**Fix:** Logical property equivalents  
**Priority:** 🟢 LOW

---

### L-14 · Satellite imagery — `margin-left` on animation progress bar

**File:** [climweb/src/climweb/pages/satellite_imagery/static/satellite_imagery/css/satellite_imagery.css:434](climweb/src/climweb/pages/satellite_imagery/static/satellite_imagery/css/satellite_imagery.css#L434), [line 440](climweb/src/climweb/pages/satellite_imagery/static/satellite_imagery/css/satellite_imagery.css#L440)  
**Type:** CSS — `margin-left`  
**Category:** Satellite imagery detail

```css
.anim-progress-line { width: 500px; margin-left: 20px; ... }
.ui-slider-tooltip::before { ... margin-left: -0.5em; }
```

**Fix:** `margin-inline-start: 20px` / `margin-inline-start: -0.5em`  
**Priority:** 🟢 LOW

---

### L-15 · StreamField title/text blocks — `padding-left` on bordered blocks

**File:** [climweb/src/climweb/base/templates/streams/title_only.html:6](climweb/src/climweb/base/templates/streams/title_only.html#L6)  
**File:** [climweb/src/climweb/base/templates/streams/text_only.html:6](climweb/src/climweb/base/templates/streams/text_only.html#L6)  
**File:** [climweb/src/climweb/base/templates/streams/title_text.html:6](climweb/src/climweb/base/templates/streams/title_text.html#L6)  
**Type:** Template — `padding-left` inline style  
**Category:** Generic content blocks (used sitewide)

```html
padding-left: 10px; /* left border accent on content blocks */
```

**RTL issue:** The left-border accent on content blocks won't mirror in RTL — the border and
padding will both be on the left while text flows right.  
**Fix:** `padding-inline-start: 10px` and use `border-inline-start` for the border.  
**Priority:** 🟢 LOW (but affects all pages using these stream blocks)

---

### L-16 · Glossary — `margin-left` on search clear button

**File:** [climweb/src/climweb/pages/glossary/templates/glossary/terms_list_include.html:51](climweb/src/climweb/pages/glossary/templates/glossary/terms_list_include.html#L51)  
**Type:** Template — `margin-left` inline style  
**Category:** Glossary detail page

```html
<a class="delete" style="margin-left: 14px" id="qClear"></a>
```

**Fix:** `margin-inline-start: 14px`  
**Priority:** 🟢 LOW

---

### L-17 · CityClimate checklist — `margin-left` on checkbox label

**File:** [climweb/src/climweb/pages/cityclimate/templates/cityclimate/cities_climate_data_checklist.html:34](climweb/src/climweb/pages/cityclimate/templates/cityclimate/cities_climate_data_checklist.html#L34)  
**Type:** Template — `margin-left` inline style  
**Category:** City climate data page

```html
margin-left: 10px;
```

**Fix:** `margin-inline-start: 10px`  
**Priority:** 🟢 LOW

---

### L-18 · Footer CSS — `padding-right`

**File:** [climweb/src/climweb/config/static/css/footer.css:39](climweb/src/climweb/config/static/css/footer.css#L39)  
**Type:** CSS — `padding-right`  
**Category:** Footer (every page)

```css
padding-right: 1rem;
```

**Fix:** `padding-inline-end: 1rem`  
**Note:** Footer appears on every page but is lower-traffic than navigation.  
**Priority:** 🟢 LOW (reclassify to MEDIUM if footer contains navigation links)

---

### L-19 · Services page — `padding-left` on service description

**File:** [climweb/src/climweb/pages/services/static/css/services_page.css:104](climweb/src/climweb/pages/services/static/css/services_page.css#L104)  
**Type:** CSS — `padding-left`  
**Category:** Services detail page

```css
padding-left: 40px;
```

**Fix:** `padding-inline-start: 40px`  
**Priority:** 🟢 LOW

---

### L-20 · Projects — `padding-left` on project description

**File:** [climweb/src/climweb/pages/organisation_pages/projects/static/css/project_detail.css:53](climweb/src/climweb/pages/organisation_pages/projects/static/css/project_detail.css#L53)  
**Type:** CSS — `padding-left`  
**Category:** Projects detail

```css
padding-left: 40px;
```

**Fix:** `padding-inline-start: 40px`  
**Priority:** 🟢 LOW

---

### L-21 · Dashboards — `margin-right` on boundary widget icon

**File:** [climweb/src/climweb/pages/dashboards/static/css/widget/boundary-widget.css:40](climweb/src/climweb/pages/dashboards/static/css/widget/boundary-widget.css#L40), [line 67](climweb/src/climweb/pages/dashboards/static/css/widget/boundary-widget.css#L67)  
**Type:** CSS  
**Category:** Dashboard widget

```css
margin-left: 30px; /* line 40 */
margin-right: 4px; /* line 67 — icon-text pair */
```

**Fix:** Logical property equivalents  
**Priority:** 🟢 LOW

---

### L-22 · Admin CMS version template — `margin-right` on icon

**File:** [climweb/src/climweb/base/templates/admin/cms_version.html:138](climweb/src/climweb/base/templates/admin/cms_version.html#L138)  
**Type:** Template — `margin-right` inline style (icon-text pair)  
**Category:** Admin panel

```html
<span style="margin-right: 4px"></span>
```

**Fix:** `margin-inline-end: 4px`  
**Priority:** 🟢 LOW (admin only)

---

### L-23 · Error pages (404/500) — `padding-left` on text block

**File:** [climweb/src/climweb/config/templates/404.html:16](climweb/src/climweb/config/templates/404.html#L16)  
**File:** [climweb/src/climweb/config/templates/500.html:15](climweb/src/climweb/config/templates/500.html#L15)  
**File:** [climweb/src/climweb/config/templates/empty_items.html:4](climweb/src/climweb/config/templates/empty_items.html#L4)  
**Type:** Template — `padding-left` inline style  
**Category:** Error/empty state pages

```html
<div style="padding-left: 20px; align-items: center; ...">
  <div style="padding-left: 20px"></div>
</div>
```

**Fix:** `padding-inline-start: 20px`  
**Priority:** 🟢 LOW

---

## ⚠️ Special: Bulma Grid Offset Classes

**File:** [climweb/src/climweb/config/static/css/bulma-grid-only.css](climweb/src/climweb/config/static/css/bulma-grid-only.css) — ~100 instances of `margin-left: X%` (offset utility classes)

These are the Bulma CSS framework's grid offset classes (`.is-offset-1`, `.is-offset-2`, etc.),
auto-generated for multiple breakpoints. They use `margin-left` for percentage offsets which will
break grid alignment in RTL.

**Options (in order of preference):**

1. **Preferred:** Replace with `bulma-rtl` — a community fork of Bulma that uses CSS logical
   properties. See [github.com/Ales-/bulma-rtl](https://github.com/Ales-/bulma-rtl)
2. Use CSS `[dir="rtl"]` overrides to flip all offset classes to `margin-right`.
3. Remove `bulma-grid-only.css` and use logical property grid utilities directly.

**This is a prerequisite for the full RTL layout to work correctly.**  
**Priority:** 🔴 HIGH (blocking — fix before the June milestone begins)

---

## 📊 Per-File Issue Counts

| File                                                                | Issues              | Priority    |
| ------------------------------------------------------------------- | ------------------- | ----------- |
| `config/static/css/bulma-grid-only.css`                             | ~100 (grid offsets) | 🔴 Blocking |
| `config/static/css/navigation.css`                                  | 8                   | 🔴 HIGH     |
| `pages/home/static/css/home.css`                                    | 8                   | 🔴 HIGH     |
| `config/static/css/cms_style.css`                                   | 9                   | 🟡 MEDIUM   |
| `config/static/css/sections.css`                                    | 7                   | 🟡 MEDIUM   |
| `pages/organisation_pages/about/static/css/about.css`               | 8                   | 🟡 MEDIUM   |
| `config/static/css/services_common.css`                             | 5                   | 🟡 MEDIUM   |
| `pages/events/static/css/event_detail.css`                          | 6                   | 🟢 LOW      |
| `config/static/css/document_detail.css`                             | 6                   | 🟢 LOW      |
| `pages/home/static/css/climate.css`                                 | 3                   | 🟡 MEDIUM   |
| `pages/email_subscription/templates/subscriber_integration_js.html` | 2                   | 🟡 MEDIUM   |
| `pages/email_subscription/templates/subscriber_optin_js.html`       | 2                   | 🟡 MEDIUM   |
| `pages/news/static/css/news_detail.css`                             | 3                   | 🟡 MEDIUM   |
| `pages/weather/static/weather/css/weather_detail_page.css`          | 2                   | 🟢 LOW      |
| `pages/weather/static/weather/css/forecast_widget.css`              | 2                   | 🟢 LOW      |
| `config/static/css/base.css`                                        | 1                   | 🔴 HIGH     |
| `config/static/css/footer.css`                                      | 1                   | 🟢 LOW      |
| `pages/home/static/css/forecast_widget.css`                         | 2                   | 🟡 MEDIUM   |
| `pages/products/static/products/css/product.css`                    | 3                   | 🟢 LOW      |
| `pages/tenders/static/css/tenders.css`                              | 2                   | 🟢 LOW      |
| `pages/vacancies/static/css/vacancies.css`                          | 2                   | 🟢 LOW      |
| `pages/feedback/static/feedback/css/feedback.css`                   | 3                   | 🟢 LOW      |
| `pages/data_request/static/css/datarequest.css`                     | 4                   | 🟢 LOW      |
| `config/static/css/services.css`                                    | 2                   | 🟡 MEDIUM   |
| `config/static/css/forecast.css`                                    | 2                   | 🟢 LOW      |
| `pages/contact/static/css/contact_page.css`                         | 1                   | 🟢 LOW      |
| `pages/stations/static/css/stations_detail_page.css`                | 1                   | 🟢 LOW      |
| `pages/satellite_imagery/static/css/satellite_imagery.css`          | 2                   | 🟢 LOW      |
| `pages/dashboards/static/css/widget/boundary-widget.css`            | 2                   | 🟢 LOW      |
| `pages/projects/static/css/project_detail.css`                      | 1                   | 🟢 LOW      |
| `pages/services/static/css/services_page.css`                       | 1                   | 🟢 LOW      |

---

## 🗓️ Propsed June Milestone Fix Order

1. **Week 1 — Blocking/Foundation**
   - Add `<html dir="rtl">` when `LANGUAGE_CODE=ar` (base template)
   - Replace `bulma-grid-only.css` with `bulma-rtl` or logical-property variant
   - Remove hardcoded `direction: ltr` in `sections.css` (H-07)

2. **Week 2 — Navigation & Hero**
   - Fix all 8 issues in `navigation.css` (H-02 through H-06)
   - Fix navbar Alerts icon inline style (H-01)
   - Fix hero banner `padding-left` in `home.css` (H-09)
   - Fix language flag float in `home.css` (H-10)
   - Fix `base.css` global margin-right (H-08)

3. **Week 3 — Homepage & Listings**
   - All `climate.css`, `forecast_widget.css` issues (M-01 through M-05)
   - `sections.css` padding (M-12, M-13)
   - `services_common.css` (M-14, M-15)
   - News listing templates (M-07, M-08, M-09, M-10)
   - Email subscription (M-21, M-22)

4. **Week 4 — Detail Pages & Admin**
   - About page, events, tenders, vacancies, document detail
   - CMS admin stylesheet cleanup
   - All remaining LOW items

---

---

## Existing RTL handling

### What already exists

**`base.html` line 11 — `<html dir>` is set for Arabic**

```html
{% get_current_language as LANGUAGE_CODE %}
{% get_current_language_bidi as LANGUAGE_BIDI %}   {# loaded but NOT used below #}

<html lang="{{ settings.base.LanguageSettings.default_language }}"
      dir="{% if settings.base.LanguageSettings.default_language|slice:":2" == "ar" %}rtl{% else %}ltr{% endif %}">
```

`dir=rtl` fires, so all `[dir=rtl]` CSS overrides **will** work once written. However, the check
reads a Wagtail DB admin setting (`LanguageSettings.default_language`), not the Django i18n
active language (`LANGUAGE_BIDI`). The BIDI variable is loaded on line 7 and then ignored.

**`base.html` lines 68–85 — Arabic text-align inline `<style>` block**

```css
{% if settings.base.LanguageSettings.default_language|slice:":2" == "ar" %}
  h1,h2,h3,h4,h5,p { text-align:right !important; }
  .table th          { text-align: right !important; }
  .has-text-left     { text-align: right !important; }
{% endif %}
```

A partial band-aid — forces right-align via `!important`. Breaks Bulma helpers like `.has-text-left`
intentionally (overrides them to right), but does nothing for paddings, borders, floats.

**`sections.css` lines 37–42 — `.fb-row--flip` layout trick**

```css
.fb-row--flip {
  direction: rtl;
} /* reverses image/text order */
.fb-row--flip > * {
  direction: ltr;
} /* restores child text direction */
```

This is a creative CSS trick for alternating feature-block layouts in LTR. **Under `<html dir=rtl>`
it breaks silently**: the outer `direction: rtl` cancels out (RTL is already active), and the child
`direction: ltr` forces all children to render LTR — text layout breaks.

**`jquery-ui.css` lines 446–476 — datepicker RTL**  
Full RTL support for `.ui-datepicker-rtl`. Third-party; do not touch.

### What does NOT exist

- No `[dir=rtl]` CSS overrides in any custom CSS file
- No Arabic font loaded (`base.html:42` loads Open Sans only — no Arabic glyphs)
- `LANGUAGE_BIDI` is loaded in `base.html:7` but never wired to the `dir` attribute

---

## ⚠️ Critical Bugs in Existing RTL Code

### Bug B-1 — `dir` attribute reads the wrong variable (`base.html:11`)

**Current (broken for i18n language switching):**

```django
dir="{% if settings.base.LanguageSettings.default_language|slice:":2" == "ar" %}rtl{% else %}ltr{% endif %}"
```

This checks `LanguageSettings.default_language` — a Wagtail DB setting that is **site-wide and
static**. If a user switches language via the Django i18n language switcher or an Accept-Language
header, the `dir` attribute remains `ltr` even though Arabic content is being served.

**Fix (one line):**

```django
dir="{% if LANGUAGE_BIDI %}rtl{% else %}ltr{% endif %}"
```

`LANGUAGE_BIDI` is already loaded on line 7 via `{% get_current_language_bidi as LANGUAGE_BIDI %}`.
It dynamically reflects the active i18n language per-request. This is the correct hook.

> Note: @erick-otenyo commented on issue #368: "I think we need to change only one file
> `climweb/src/climweb/config/templates/base.html` for this feature." — this is that one line.

### Bug B-2 — `.fb-row--flip` breaks under RTL pages (`sections.css:37–42`)

**Current (breaks in Arabic):**

```css
.fb-row--flip {
  direction: rtl;
} /* intentional image-flip trick */
.fb-row--flip > * {
  direction: ltr;
} /* restores text direction for children */
```

Under `<html dir=rtl>`, this CSS makes children render in `direction: ltr`, reversing the text
flow to LTR inside what should be an RTL page. The visual image-flip also cancels out.

**Fix:**

```css
/* Under RTL page, invert both rules to preserve the visual flip */
[dir="rtl"] .fb-row--flip {
  direction: ltr;
}
[dir="rtl"] .fb-row--flip > * {
  direction: rtl;
}
```

### Bug B-3 — No Arabic font loaded (`base.html:42`)

Open Sans has no Arabic Unicode coverage. The browser silently falls back to OS system fonts,
which vary by device and produce inconsistent typography. The font weight, line-height, and
letter-spacing rules written for Open Sans do not apply.

**Fix:** Add Noto Sans Arabic (or Amiri for a more formal style) to the existing Google Fonts link:

```html
<link
  href="https://fonts.googleapis.com/css2?
  family=Open+Sans:ital,wght@0,300..800;1,300..800&
  family=Noto+Sans+Arabic:wght@400;600;700&
  display=swap"
  rel="stylesheet"
/>
```

Then in CSS:

```css
[dir="rtl"] body {
  font-family: "Noto Sans Arabic", sans-serif;
}
```

---

## Final checklist

### Total RTL issues across templates and static files

**128 actionable issues** (excluding ~100 Bulma grid offsets which need a separate strategy).

- Template inline style issues: **30**
- CSS issues: **98** (across 30+ CSS files)
- Critical logic bugs in `base.html`: **3** (B-1, B-2, B-3 above)

### Single file with the most issues

**`config/static/css/cms_style.css`** and **`config/static/css/navigation.css`** tie at 8–9
each. `navigation.css` is higher priority (every-page, user-visible) but `cms_style.css` has
more raw instances. `bulma-grid-only.css` has ~100 instances but is a separate prerequisite.

### Existing RTL support to build on (not replace)

Yes — three things:

1. **`<html dir=rtl>` already fires** when the Wagtail admin language is set to Arabic. Fix Bug
   B-1 (one line) to make it also respond to the active i18n language. All `[dir=rtl]` CSS
   overrides will then work immediately.
2. **`{% get_current_language_bidi as LANGUAGE_BIDI %}`** is already loaded in `base.html:7`.
   Wire it to the `dir` attribute (B-1 fix).
3. **`jquery-ui.css` datepicker RTL** is already complete — do not modify.

Do **not** build on the `!important text-align:right` block in `base.html:68–85` — it is a blunt
override that conflicts with Bulma's intentional alignment utilities. Replace it with targeted
`[dir=rtl]` rules in a new `rtl.css` file.

### What to discuss with @justincred / the team before writing code

1. **`dir` source of truth (Bug B-1):** Should `dir=rtl` follow the Django i18n active language
   per-request (`LANGUAGE_BIDI`), or the Wagtail admin `LanguageSettings.default_language`
   site-wide setting? These are different for sites that serve both Arabic and English users.
   The single-language site (default_language = "ar") works either way; a bilingual site needs
   `LANGUAGE_BIDI`. Confirm before changing `base.html:11`.

2. **Issue #542 number:** The public issue #542 is "Social share of MapViewer not working on
   Mobile" — confirm the correct RTL issue number to reference in PR descriptions. Currently
   open RTL issue is #590.

3. **Issue #590 specifically:** "Alert blinking too close to text in Arabic version." Confirm
   which component this is (the nav CAP alert badge or the homepage map badge) and the CSS
   class involved, so the fix targets the right element.

4. **Google Translate vs Django i18n:** The site uses Google Translate for client-side language
   switching. GT does not update `<html dir>`. Is RTL support expected to work with GT-switched
   Arabic, or only with server-side Django i18n locale switching? This determines how much
   JavaScript RTL handling (if any) is needed alongside the CSS work.

5. **Arabic font (Bug B-3):** Is adding `Noto Sans Arabic` to the Google Fonts request in scope?
   It resolves inconsistent typography across devices at no cost but adds a network request.

---

## 🖥️ Local Dev Server — Start / Stop Reference

### Prerequisites (one-time)

| Tool | How it was installed |
|------|---------------------|
| PostgreSQL 18 | [Postgres.app](https://postgresapp.com) — data dir at `~/Library/Application Support/Postgres/var-18` |
| Redis | Homebrew (`brew install redis`) |
| Python venv | `venv/` inside the repo root |
| Node (optional, Vue hot-reload) | Only needed when editing Vue components in `home-map-vue/` |

---

### ▶️ Starting everything

Run each command in order. Use separate terminal tabs if you want to keep logs visible.

**Step 1 — PostgreSQL**
```bash
export PATH="/Applications/Postgres.app/Contents/Versions/18/bin:$PATH"
pg_ctl -D "$HOME/Library/Application Support/Postgres/var-18" \
       -l /tmp/pg_server.log start
```
Verify: `psql -h localhost -p 5432 -U postgres -c "SELECT 1;"` → should return `1`.

**Step 2 — Redis**
```bash
brew services start redis
```
Verify: `redis-cli ping` → should return `PONG`.

**Step 3 — ClimWeb dev server**
```bash
cd ~/Downloads/climweb
export PATH="/Applications/Postgres.app/Contents/Versions/18/bin:$PATH"
export $(cat .env | grep -v '^#' | grep -v '^$' | xargs)
venv/bin/climweb runserver 8000
```
- Homepage: [http://localhost:8000](http://localhost:8000)
- Admin: [http://localhost:8000/cms-admin](http://localhost:8000/cms-admin) — `admin` / `admin1234`
- Arabic news article: [http://localhost:8000/news/arabic-rtl-sample-article/](http://localhost:8000/news/arabic-rtl-sample-article/)
- Arabic CAP alert: [http://localhost:8000/alerts/arabic-rtl-sample-cap-alert/](http://localhost:8000/alerts/arabic-rtl-sample-cap-alert/)

> **Note:** The homepage map loads from the pre-built Vue bundle at `static/vue/home-map.js`.
> The Vite dev server (port 5173) is **not** needed for normal development — only if you are
> actively editing `pages/home/home-map-vue/src/` files.

---

### ⏹️ Stopping everything

```bash
# 1. Kill the Django dev server (Ctrl-C in its terminal, or from anywhere):
pkill -f "climweb runserver"

# 2. Stop Redis
brew services stop redis

# 3. Stop PostgreSQL
export PATH="/Applications/Postgres.app/Contents/Versions/18/bin:$PATH"
pg_ctl -D "$HOME/Library/Application Support/Postgres/var-18" stop
```

---

### 🔁 Quick copy-paste blocks

**Start all three:**
```bash
export PATH="/Applications/Postgres.app/Contents/Versions/18/bin:$PATH"
pg_ctl -D "$HOME/Library/Application Support/Postgres/var-18" -l /tmp/pg_server.log start
brew services start redis
cd ~/Downloads/climweb && \
  export $(cat .env | grep -v '^#' | grep -v '^$' | xargs) && \
  venv/bin/climweb runserver 8000
```

**Stop all three:**
```bash
pkill -f "climweb runserver"
brew services stop redis
export PATH="/Applications/Postgres.app/Contents/Versions/18/bin:$PATH"
pg_ctl -D "$HOME/Library/Application Support/Postgres/var-18" stop
```

---

### 🔧 Troubleshooting

| Symptom | Fix |
|---------|-----|
| `FATAL: role "zhengwei" does not exist` | Always connect with `-U postgres`: `psql -h localhost -p 5432 -U postgres` |
| `Address already in use` on port 8000 | `pkill -f "climweb runserver"` then retry |
| `ImportError: libpq.5.dylib not found` | `export PATH="/Applications/Postgres.app/Contents/Versions/18/bin:$PATH"` before starting |
| `ImportError: failed to find libmagic` | `brew install libmagic` |
| `OSError: cannot load library 'libpango'` | `brew install pango` |
| `TypeError: expected bytes, str found` (pyproj) | `pip install --upgrade "pyproj>=3.7"` |
| `TypeError: 'method' object is not iterable` | Python 3.13 stacked-decorator bug — already fixed in `home/models.py:209` |
| Homepage weather widget empty | Forecast dates may be in the past — run the SQL below to shift them forward |
| Homepage map badge shows 0 | Vue is loading from Vite dev server (port 5173) which is not running — add `VUE_FRONTEND_USE_DEV_SERVER = False` to `climweb/src/climweb/config/settings/dev.py` |

**Fix for expired forecast dates** (run if widget shows empty after a few days):
```bash
psql -h localhost -p 5432 -U postgres -d climweb << 'SQL'
BEGIN;
ALTER TABLE forecastmanager_forecast
  DROP CONSTRAINT forecastmanager_forecast_forecast_date_effective__fdecd7d1_uniq;
UPDATE forecastmanager_forecast
  SET forecast_date = forecast_date + INTERVAL '7 days';
ALTER TABLE forecastmanager_forecast
  ADD CONSTRAINT forecastmanager_forecast_forecast_date_effective__fdecd7d1_uniq
  UNIQUE (forecast_date, effective_period_id);
COMMIT;
SQL
```

---

_Original grep audit: 2026-05-25 (session 1)_
_Structural bugs, existing-RTL analysis, server docs added: 2026-05-25 (session 2)_
