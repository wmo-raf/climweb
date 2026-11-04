# Manual testing checklist

Automated checks (`tools/a11y`) catch roughly a third of accessibility problems. Run this checklist before each release, or after changes to templates, menus, forms, maps or charts. It takes about an hour for one person.

Test on a staging site with real content. Record the date, browser, screen reader and anything that failed, and fix or list failures in the [accessibility statement](statement.md).

## Before you start: automated scan

```bash
.venv-a11y/bin/python tools/a11y/scan.py --base-url https://staging.example.org
```

```bash
.venv-a11y/bin/python tools/a11y/scan.py --base-url https://staging.example.org --width 375
```

Both should finish with "0 with serious+ issues". See `tools/a11y/README.md` for setup.

## 1. Keyboard only

Put the mouse away. Use Tab, Shift+Tab, Enter, Space, the arrow keys and Esc.

- [ ] The first Tab shows **Skip to main content**; Enter moves past the header.
- [ ] Every link, button and field can be reached, in a sensible order, with a **visible focus ring**.
- [ ] **Main menu:** dropdowns open as you tab into them; Esc closes them.
- [ ] **Language and search** in the header open with Enter and close with Esc.
- [ ] **Mobile menu** (narrow window): the burger opens it, Esc closes it, and focus returns to the burger.
- [ ] **Filters** (publications, news): headings expand with Enter; checkboxes toggle with Space.
- [ ] **Tabs** (products, forecast days): tabs can be reached and selected with Enter.
- [ ] **Dialogs** (staff profile, dashboard info ⓘ): focus moves into the dialog, Tab stays inside, and Esc closes it and returns focus.
- [ ] **City and station search:** type, use ↓/↑ to pick a result, then Enter.
- [ ] **Maps:** Tab to the map, then pan with the arrow keys and zoom with + and −.
- [ ] **Forms:** submit a form empty. The error summary appears and is focused, and its links move to each field.
- [ ] Nowhere does focus get stuck or disappear.

## 2. Screen reader

Test with at least one desktop and one mobile pairing:

| Platform | Screen reader | Browser | Start / stop |
|---|---|---|---|
| Windows | NVDA (free) | Firefox or Chrome | Ctrl+Alt+N / Insert+Q |
| Windows | JAWS | Chrome | from the Start menu |
| macOS | VoiceOver | Safari | Cmd+F5 |
| iOS | VoiceOver | Safari | Settings → Accessibility, or triple-click the side button |
| Android | TalkBack | Chrome | Settings → Accessibility |

- [ ] The **page title** is read when each page loads.
- [ ] The **landmarks** list (NVDA: D; VoiceOver: rotor) shows banner, navigation, main and footer.
- [ ] The **headings** list (NVDA: H; VoiceOver: rotor) gives a sensible outline of the page.
- [ ] Images are described meaningfully; decorative images are skipped.
- [ ] Icon-only buttons say what they do ("Next page", "Clear search", "About this data").
- [ ] Menus, accordions and tabs announce "expanded"/"collapsed" or "selected".
- [ ] **Charts:** the chart is announced by name, and "View as data table" shows the values.
- [ ] **Maps:** each map has a descriptive label; the same information is available as text on the page.
- [ ] **Warnings:** each alert's severity is read as text.
- [ ] **Forms:** each field's label, "required" and errors are read; the error summary is announced.
- [ ] **Messages** (after submitting a form, copying a link) are read out without moving focus.
- [ ] **Language:** after switching language, text is read in the new language's voice.

## 3. Zoom, reflow and display settings

- [ ] **Browser zoom 200% and 400%:** nothing overlaps or is cut off, and there's no sideways scrolling except tables and maps.
- [ ] **Narrow window (320px):** the same.
- [ ] **Text spacing** (WCAG 1.4.12): apply a text-spacing bookmarklet; text still fits in its boxes.
- [ ] **Hover and focus content** (WCAG 1.4.13): chart tooltips, map popups and menus can be dismissed with Esc and stay open while you move the pointer onto them.
- [ ] **Reduce motion** (system setting) is on: nothing pulses, slides or scrolls smoothly.
- [ ] **Windows High Contrast / forced colours:** buttons, focus ring and form fields are still visible.

## 4. Content spot-checks

- [ ] Recently published images have meaningful descriptions, not file names.
- [ ] Recent videos have captions.
- [ ] Recent documents are tagged PDFs or have a web page version.
- [ ] Links don't say only "click here" or "read more".

## Recording results

Note for each failure: the page, steps to reproduce, what you expected, and the WCAG criterion from the [conformance checklist](conformance.md). Open an issue for each, and update the accessibility statement if it won't be fixed in this release.
