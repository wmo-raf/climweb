# Accessibility checks

ClimWeb aims for WCAG 2.1 AA. Two kinds of automated check keep it there:

| Check | What it catches | How to run |
|---|---|---|
| Template tests (`climweb/base/tests/test_template_a11y.py`, `test_a11y_forms.py`, `test_contrast.py`, `test_image_block.py`) | `<img>` without `alt`, icon-only links/buttons without a name, positive `tabindex`, form labels and error linking, colour contrast helpers | Part of the normal test suite: `python manage.py test climweb.base` |
| Page scan (`scan.py`, axe-core) | Problems that only show on a rendered page: contrast, landmarks, ARIA misuse, duplicate ids, unlabelled controls, missing page language | Against a running site, see below |

Automated tools find roughly a third of accessibility problems. They don't replace a keyboard and screen reader pass before a release.

## Page scan

The scan runs in its own virtualenv and talks to the site over HTTP, so it works against a local dev server, staging or production, and doesn't need ClimWeb's dependencies.

```bash
python3 -m venv .venv-a11y
.venv-a11y/bin/pip install -r tools/a11y/requirements.txt
```

It uses your installed Google Chrome by default. Without Chrome, install Playwright's browser once and pass `--channel ''`:

```bash
.venv-a11y/bin/playwright install chromium
```

Scan the pages listed in `pages.txt`:

```bash
.venv-a11y/bin/python tools/a11y/scan.py --base-url http://localhost:8000
```

Useful options:

- `--pages /news/ /stations/` scans just those paths
- `--width 375` checks the mobile layout
- `--fail-on critical` only fails on critical issues (default: `serious`)
- `--json report.json` saves the full results, including each element and why it failed

The exit code is 1 when any page has an issue at or above `--fail-on`, so the same command can gate CI.

Edit `pages.txt` to add page types. Use paths that exist on the site you scan; missing pages are reported as HTTP 404.

### Reading the output

```
/news/  (HTTP 200) - 1 issue(s)  FAIL
  [serious] color-contrast: Elements must meet minimum color contrast ratio thresholds (2 element(s))
      .pub-date
```

Each issue names the axe rule (search it at https://dequeuniversity.com/rules/axe/), its impact and the CSS selectors of the failing elements.

Third-party widgets ClimWeb can't change (Google Translate, reCAPTCHA, the Wagtail user bar) are excluded in `scan.py`.
