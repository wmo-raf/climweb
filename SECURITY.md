# Security Policy

ClimWeb is deployed by National Meteorological and Hydrological Services (NMHSs) to publish
weather warnings, forecasts and climate information to the public. A vulnerability in ClimWeb
can affect the delivery of early warning information to people at risk, so we take security
reports seriously and ask that you report them privately.

---

## Supported Versions

Security fixes are released on the **latest minor release line only**. Older tags do not
receive backported patches.

| Version | Supported |
|---|---|
| 1.2.x   | ✅ Security fixes provided |
| < 1.2   | ❌ Not supported — upgrade to the latest release |

Deployments are expected to track the latest release image published to
[GHCR](https://github.com/wmo-raf/climweb/pkgs/container/climweb). If you are running an older
version, upgrading to the current release is the supported path to receiving a fix.

Note that ClimWeb bundles third-party components (Wagtail, Django, and the plugins listed in
`climweb/requirements/base.in`). Vulnerabilities in those projects are addressed by upgrading
the dependency in a ClimWeb release; report them upstream as well where appropriate.

---

## Reporting a Vulnerability

**Do not open a public GitHub issue, pull request or discussion for a security vulnerability.**

Report it privately using GitHub's private vulnerability reporting:

1. Go to <https://github.com/wmo-raf/climweb/security/advisories/new>, or
2. Open the **Security** tab on [`wmo-raf/climweb`](https://github.com/wmo-raf/climweb) and
   click **Report a vulnerability**.

This creates a private advisory visible only to you and the maintainers.

### What to include

A report is much easier to act on when it contains:

- The ClimWeb version or commit SHA, and whether the instance is Docker or a source install
- The affected component (e.g. CMS admin, MapViewer, CAP composer, a specific page type or API endpoint)
- Steps to reproduce, including any request payloads or screenshots
- What an attacker can achieve — data disclosure, privilege escalation, defacement, denial of service
- The privilege level required (anonymous visitor, authenticated CMS editor, administrator)
- Any suggested fix or patch, if you have one

Reports in English or French are both welcome.

### What to expect

| Stage | Target |
|---|---|
| Acknowledgement of your report | Within 5 working days |
| Initial assessment and severity triage | Within 10 working days |
| Fix released, or a remediation plan shared with you | Within 90 days of triage |

Severity is assessed using [CVSS v3.1](https://www.first.org/cvss/calculator/3.1). Critical
issues that are exploitable by an unauthenticated user against a public instance are
prioritised ahead of the normal release cycle.

We will keep you updated through the private advisory thread, and we will tell you if we
disagree that the issue is a vulnerability and why.

---

## Disclosure Process

We follow coordinated disclosure:

1. You report privately; we confirm and triage.
2. We develop and test a fix in private, and notify NMHS administrators running affected
   instances where the severity warrants it.
3. We publish a patched release and, where a CVE is warranted, a GitHub Security Advisory.
4. Public details are disclosed after the patched release is available, normally within
   90 days of triage. If a fix will take longer, we will agree a revised timeline with you.

If a vulnerability is already being exploited in the wild, we may shorten this timeline and
publish mitigation guidance before a full fix is ready.

**Credit:** reporters are credited by name in the advisory and release notes unless you ask to
remain anonymous.

---

## Scope

### In scope

- The ClimWeb application in this repository, at the latest release
- The deployment configuration in [`wmo-raf/climweb-docker`](https://github.com/wmo-raf/climweb-docker)
- ClimWeb-maintained plugins and packages published under [`wmo-raf`](https://github.com/wmo-raf)

### Out of scope

- Vulnerabilities in third-party dependencies that already have a public advisory and a fix —
  open a normal issue or pull request to bump the pin instead
- Findings against a specific NMHS's live site that stem from that site's own configuration,
  hosting or content rather than the ClimWeb codebase. Please report those to us privately and
  we will contact the operator; do not contact them directly and do not test against live
  instances
- Missing security headers, cookie flags or TLS configuration on a live instance without a
  demonstrated impact
- Findings produced solely by an automated scanner with no proof of exploitability
- Social engineering, physical attacks and denial of service through traffic volume

### Testing rules

Please test against **your own local or staging installation**, never against a live NMHS
instance. These sites carry operational warning information for the public, and disruption has
real consequences. Do not access, modify or exfiltrate data belonging to any organisation, and
stop as soon as you have enough to demonstrate the issue.

We will not pursue action against researchers who follow this policy in good faith. ClimWeb has
no bug bounty programme; reports are handled on a volunteer and best-effort basis by the
WMO Regional Office for Africa and contributors.

---

## For Administrators Running ClimWeb

If you operate an NMHS instance, the following reduce your exposure regardless of any specific
vulnerability:

- Track the latest release; subscribe to repository releases and security advisories on
  [`wmo-raf/climweb`](https://github.com/wmo-raf/climweb) to be notified of patches
- Serve the site over HTTPS only, with a valid certificate and automated renewal
- Keep `DEBUG` off in production and keep `.env` files out of version control and off
  world-readable paths
- Rotate `SECRET_KEY`, database credentials and any third-party API keys if they may have been
  exposed
- Enforce two-factor authentication for CMS accounts (`wagtail-2fa` is included) and remove
  accounts of staff who have left
- Grant editors the minimum roles they need rather than superuser access
- Keep verified, restorable backups of both the database and the media directory, and test a
  restore periodically
- Keep the host operating system, Docker and the reverse proxy patched

Deployment and configuration guidance is maintained at
[climweb.readthedocs.io](https://climweb.readthedocs.io/).

---

## Questions

For questions about this policy that are **not** themselves a vulnerability report, open a
[GitHub issue](https://github.com/wmo-raf/climweb/issues) or see
[CONTRIBUTING.md](CONTRIBUTING.md).

See also [LEGAL.md](LEGAL.md) for terms governing the use of this software.
