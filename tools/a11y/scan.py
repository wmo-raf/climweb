#!/usr/bin/env python3
"""
Scan ClimWeb pages for WCAG 2.1 A/AA problems with axe-core.

Runs against any running site (local dev server, staging) - it doesn't need Django.
See README.md in this folder for setup.

    python tools/a11y/scan.py --base-url http://localhost:8000
    python tools/a11y/scan.py --base-url http://localhost:8000 --pages /news/ /stations/ --width 375

Exit code is 1 when any page has a violation at or above --fail-on (default: serious),
so the same command can gate CI later.
"""
import argparse
import json
import sys
from importlib import resources
from pathlib import Path
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
IMPACT_ORDER = ["minor", "moderate", "serious", "critical"]
WCAG_TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]

# Third-party widgets ClimWeb can't change; their own accessibility is the vendor's responsibility.
EXCLUDE = [
    ["#google_language_translator"],
    [".goog-te-banner-frame"],
    ["iframe[src*='recaptcha']"],
    ["#wagtail-userbar"],
]


def read_pages(path):
    pages = []
    for line in Path(path).read_text().splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            pages.append(line)
    return pages


def scan_page(page, url, axe_js):
    response = page.goto(url, wait_until="load", timeout=60_000)
    try:
        page.wait_for_load_state("networkidle", timeout=10_000)
    except Exception:
        pass  # pages with live maps keep fetching tiles; "load" is enough
    page.add_script_tag(content=axe_js)
    result = page.evaluate(
        """async ([tags, exclude]) => {
            const r = await axe.run({include: [document], exclude},
                                    {runOnly: {type: "tag", values: tags}, resultTypes: ["violations"]});
            return r.violations.map(v => ({
                id: v.id, impact: v.impact, help: v.help, helpUrl: v.helpUrl,
                nodes: v.nodes.map(n => ({target: n.target.join(" "), summary: n.failureSummary}))
            }));
        }""",
        [WCAG_TAGS, EXCLUDE],
    )
    return (response.status if response else None), result


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--base-url", required=True, help="site to scan, e.g. http://localhost:8000")
    parser.add_argument("--pages", nargs="*", help="paths to scan (default: pages.txt)")
    parser.add_argument("--pages-file", default=HERE / "pages.txt")
    parser.add_argument("--width", type=int, default=1280, help="viewport width; 375 checks the mobile layout")
    parser.add_argument("--channel", default="chrome",
                        help="installed browser to use ('chrome', 'msedge'); pass '' to use Playwright's Chromium")
    parser.add_argument("--fail-on", choices=IMPACT_ORDER, default="serious",
                        help="lowest impact that makes the scan fail")
    parser.add_argument("--json", help="also write the full results to this file")
    args = parser.parse_args()

    paths = args.pages or read_pages(args.pages_file)
    axe_js = resources.files("axe_playwright_python").joinpath("axe.min.js").read_text()
    threshold = IMPACT_ORDER.index(args.fail_on)

    report, failing = {}, 0
    with sync_playwright() as p:
        browser = p.chromium.launch(channel=args.channel or None)
        page = browser.new_page(viewport={"width": args.width, "height": 900})
        for path in paths:
            url = urljoin(args.base_url.rstrip("/") + "/", path.lstrip("/"))
            try:
                status, violations = scan_page(page, url, axe_js)
            except Exception as exc:  # report and keep going
                print(f"\n{path}\n  could not scan: {exc}")
                failing += 1
                continue
            report[path] = {"status": status, "violations": violations}
            blocking = [v for v in violations if IMPACT_ORDER.index(v["impact"] or "minor") >= threshold]
            failing += bool(blocking)

            print(f"\n{path}  (HTTP {status}) - {len(violations)} issue(s)" + ("  FAIL" if blocking else ""))
            for v in sorted(violations, key=lambda v: -IMPACT_ORDER.index(v["impact"] or "minor")):
                print(f"  [{v['impact']}] {v['id']}: {v['help']} ({len(v['nodes'])} element(s))")
                for node in v["nodes"][:3]:
                    print(f"      {node['target']}")
                if len(v["nodes"]) > 3:
                    print(f"      ... and {len(v['nodes']) - 3} more")
        browser.close()

    if args.json:
        Path(args.json).write_text(json.dumps(report, indent=2))
    print(f"\n{len(paths)} page(s) scanned, {failing} with {args.fail_on}+ issues (WCAG 2.1 A/AA, axe-core).")
    return 1 if failing else 0


if __name__ == "__main__":
    sys.exit(main())
