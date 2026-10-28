# Accessibility

ClimWeb aims to meet the **Web Content Accessibility Guidelines (WCAG) 2.1 at level AA**, so that weather, climate and warning information reaches everyone, including blind and partially sighted people using screen readers or magnification, people who use only a keyboard, and people with low vision or colour blindness.

The platform handles most of this: page structure, keyboard access, colour contrast, forms, charts and maps. Some of it depends on what editors publish, such as image descriptions, link text and captions on videos. Each site also publishes its own accessibility statement.

```{toctree}
:maxdepth: 1

conformance
editors
statement
manual-testing
developers
```

## What ClimWeb does for you

- **Screen readers**: every page has a skip link, labelled landmarks (header, navigation, main content, footer) and a page title. Menus, tabs, accordions, dialogs and form errors announce their state. Toast messages and search results are read out.
- **Keyboard**: everything that works with a mouse works with the keyboard, with a clearly visible focus ring. Dialogs keep focus inside them and return it when closed.
- **Colour and contrast**: text meets the 4.5:1 contrast minimum, including on the brand colour, and warning severity is never shown by colour alone. The Theme settings warn you if a brand colour you choose is hard to read.
- **Images, charts and maps**: images have text alternatives, charts can be read as a data table, maps are labelled and their information is also available as text.
- **Forms**: every field is labelled, errors are linked to their field and summarised at the top, and browsers can autofill personal details.
- **Motion**: nothing moves on its own, and animations stop for visitors who turn on "reduce motion".
- **Mobile and zoom**: pages reflow down to 320 pixels wide without sideways scrolling.

## Where to start

| You are | Read |
|---|---|
| An editor publishing content | [Writing accessible content](editors.md) |
| A site administrator | [Publishing your accessibility statement](statement.md) and the [conformance checklist](conformance.md) |
| Testing a release | [Manual testing checklist](manual-testing.md) and the automated checks in `tools/a11y` |
| A developer | [Developer guide](developers.md) |
