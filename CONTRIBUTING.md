# Contributing to ClimWeb

Thank you for your interest in contributing to **ClimWeb**, an open-source Content Management System built for National Meteorological and Hydrological Services (NMHSs) across Africa. ClimWeb is recognised as a [Digital Public Good](https://digitalpublicgoods.net/) and your contributions directly support climate action and early warning systems for vulnerable communities.

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [About the Project](#about-the-project)
- [How to Contribute](#how-to-contribute)
  - [Reporting Bugs](#reporting-bugs)
  - [Requesting Features](#requesting-features)
  - [Improving Documentation](#improving-documentation)
  - [Contributing Translations](#contributing-translations)
  - [Submitting Code](#submitting-code)
- [Development Setup](#development-setup)
- [Tech Stack](#tech-stack)
- [Coding Standards](#coding-standards)
- [Branching Strategy](#branching-strategy)
- [Commit Message Guidelines](#commit-message-guidelines)
- [Pull Request Process](#pull-request-process)
- [Issue Labels](#issue-labels)
- [Release Process](#release-process)
- [Getting Help](#getting-help)

---

## Code of Conduct

By participating in this project, you agree to uphold a respectful and inclusive environment. We expect all contributors to:

- Be respectful of differing viewpoints and experiences
- Use welcoming and inclusive language
- Gracefully accept constructive criticism
- Show empathy towards other community members

Unacceptable behaviour should be reported to the project maintainers at the [WMO Regional Office for Africa](https://github.com/wmo-raf).

---

## About the Project

ClimWeb is built on the [Wagtail CMS](https://wagtail.org/) framework, which itself is built on [Django](https://www.djangoproject.com/), a high-level Python web framework. The production-ready system is containerised with [Docker](https://www.docker.com/) and deployed via Docker Compose. 
It can also be run in development within a python virtual environment.

Key repositories in the ClimWeb ecosystem:

| Repository | Purpose |
|---|---|
| [`wmo-raf/climweb`](https://github.com/wmo-raf/climweb) | Core CMS application |
| [`wmo-raf/climweb-docker`](https://github.com/wmo-raf/climweb-docker) | Docker Compose deployment configuration (Production ready) |

Full documentation is available at [climweb.readthedocs.io](https://climweb.readthedocs.io/).

---

## How to Contribute

### Reporting Bugs

Before opening a bug report, please search [existing issues](https://github.com/wmo-raf/climweb/issues) to avoid duplicates.

When filing a bug, include:

- A clear and descriptive title
- Steps to reproduce the problem
- Expected behaviour vs. actual behaviour
- ClimWeb version and deployment environment (OS, Docker version, browser if applicable)
- Relevant logs or screenshots

Use the **`bug`** label when creating the issue.

### Requesting Features

Feature requests are welcome. Please open an issue and:

- Describe the feature clearly and explain the use case
- Indicate whether it is specific to a particular NMHS context or broadly applicable
- If possible, reference any related WMO standards or guidelines that the feature should align with

Use the **`enhancement`** label. 

### Improving Documentation

Documentation lives at [climweb.readthedocs.io](https://climweb.readthedocs.io/) and is maintained alongside the codebase. If you spot errors, missing content, or areas that need clarification:

- Open an issue with the **`documentation`** label, or
- Submit a pull request with the proposed changes directly in the docs/ directory

### Contributing Translations

ClimWeb supports multiple languages to serve NMHSs across Africa's diverse linguistic landscape. Supported language codes include:

| Code | Language |
|---|---|
| `en` | English |
| `fr` | French |
| `ar` | Arabic |
| `am` | Amharic |
| `es` | Spanish |
| `sw` | Swahili |

Translation and proofreading contributions are made at https://crowdin.com/project/nmhs-cms. To contribute a language read the [Translations contribution guide here](https://climweb.readthedocs.io/en/latest/_docs/Climweb-Translations-Contribution-Guide.html).

If you represent an NMHS and need a language not yet supported, please open a feature request.

### Submitting Code

All code contributions go through pull requests. Before writing code, please:

1. Search open issues and PRs to avoid duplicate effort
2. For non-trivial changes, open an discussion first to discuss the approach with maintainers. The discussion will be escalated to an issue depending on the clarity of it's implementation.
3. Fork the repository and create a feature branch from `main`. Label the branch "feature/{feature_name}" e.g "feature/drawing-polygons"
4. Sumbit a pull request to the wmo-raf/main main branch

---

## Development Setup

### Prerequisites

- Python 3.10 or higher
- Node.js (for frontend assets)
- Docker and Docker Compose
- Git

### Local Setup

```bash
# Clone the repository
git clone https://github.com/wmo-raf/climweb.git
cd climweb

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e climweb

# Copy and configure environment variables
cp .env.sample .env
# Edit .env with your local settings

# Apply database migrations
climweb migrate

# Create a superuser
climweb createsuperuser

# Run the development server
climweb runserver
```

For Docker-based local development, refer to the [Technical Guide](https://climweb.readthedocs.io/en/stable/_docs/Technology.html) in the documentation.

---

## Tech Stack

Understanding the stack helps you contribute effectively:

| Layer | Technology |
|---|---|
| Web framework | [Django](https://www.djangoproject.com/) |
| CMS framework | [Wagtail](https://wagtail.org/) |
| Language | Python |
| Containerisation | Docker / Docker Compose |
| Message broker | Eclipse Mosquitto (MQTT, used for CAP alerts) |
| Frontend | HTML, CSS, JavaScript (served via Django templates) |

ClimWeb follows a **modular Django application** architecture. Each feature area (CAP warnings, forecasts, climate data, etc.) is a self-contained Django app within the project. When adding new functionality, prefer creating or extending an existing app rather than adding to the core.

---

## Coding Standards

### Python

- Follow [PEP 8](https://peps.python.org/pep-0008/) style guidelines
- Use `black` for code formatting: `black .`
- Use `flake8` for linting: `flake8 .`
- Write docstrings for all public classes and functions (Google-style preferred)
- Maintain test coverage for any new logic

### Django / Wagtail

- Follow [Django best practices](https://docs.djangoproject.com/en/stable/misc/design-philosophies/) for models, views, and URL configuration
- Use Wagtail's `StreamField` and page models appropriately — avoid overloading the base `Page` model
- Place model logic in the model, business logic in services or utility modules, and keep views thin
- All new Wagtail page types must include appropriate `content_panels`

### Frontend

- Keep JavaScript dependencies minimal
- Ensure all UI changes are mobile-friendly and work on low-bandwidth connections, consistent with ClimWeb's target deployment environments
- Follow accessibility best practices (WCAG 2.1 AA as a baseline)

---

## Branching Strategy

| Branch | Purpose |
|---|---|
| `main` | Stable, production-ready code |
| `develop` | Active development branch (target your PRs here) |
| `feature/<name>` | New features |
| `bugfix/<name>` | Bug fixes |
| `hotfix/<name>` | Critical fixes for production |
| `docs/<name>` | Documentation-only changes |

Always branch from `develop` (or `main` for hotfixes) and open PRs targeting `develop`.

---

## Commit Message Guidelines

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <short summary>

[optional body]

[optional footer(s)]
```

**Types:**

| Type | When to use |
|---|---|
| `feat` | A new feature |
| `fix` | A bug fix |
| `docs` | Documentation changes only |
| `style` | Formatting changes, no logic change |
| `refactor` | Code refactor without feature or fix |
| `test` | Adding or updating tests |
| `chore` | Build process, dependency updates |
| `i18n` | Translation or localisation changes |

**Examples:**

```
feat(cap): add multi-language support for alert descriptions

fix(dashboard): correct date display format in admin area

docs(installation): update Docker Compose environment variable reference

i18n(sw): add Swahili translations for forecast pages
```

---

## Pull Request Process

1. **Ensure your branch is up to date** with the target branch before submitting
2. **Write a clear PR description** that explains what the change does and why
3. **Link the related issue** using GitHub keywords (e.g. `Closes #123`)
4. **Confirm all tests pass** locally before opening the PR
5. **Request a review** from at least one maintainer
6. **Address review feedback** promptly — PRs that are inactive for more than 30 days may be closed
7. **Do not merge your own PRs** — a maintainer will merge once approved

PRs should be kept focused and small where possible. Large, multi-purpose PRs are harder to review and slower to merge.

---

## Issue Labels

| Label | Description |
|---|---|
| `bug` | Something isn't working |
| `enhancement` | New feature or improvement request |
| `documentation` | Improvements or additions to documentation |
| `translations` | Translation or localisation work |
| `good first issue` | A good starting point for new contributors |
| `help wanted` | Extra attention or outside expertise needed |
| `climtech` | Issues specific to ClimTech deployments |
| `Priority: high` | High-priority items requiring urgent attention |
| `v1.2` | Milestone-tagged issues |

---

## Release Process

ClimWeb follows a version-based release process. New releases are published on the [GitHub Releases page](https://github.com/wmo-raf/climweb/releases) and include:

- A changelog summarising new features, bug fixes, and breaking changes
- Updated Docker image tags on the associated container registry
- Release notes linked from the Wagtail admin upgrade notification

When a new release is available, the ClimWeb admin interface displays an upgrade notification. NMHS administrators can review release notes and choose when to upgrade their deployment.

If you discover a security vulnerability, please **do not open a public issue**. Contact the maintainers directly via the WMO Regional Office for Africa.

---

## Getting Help

- **Documentation:** [climweb.readthedocs.io](https://climweb.readthedocs.io/)
- **GitHub Issues:** [github.com/wmo-raf/climweb/issues](https://github.com/wmo-raf/climweb/issues)
- **Docker deployment:** [github.com/wmo-raf/climweb-docker](https://github.com/wmo-raf/climweb-docker)
- **WMO Regional Office for Africa:** [github.com/wmo-raf](https://github.com/wmo-raf)

We appreciate every contribution — from bug reports and translations to new features and documentation. Thank you for helping make ClimWeb better for meteorological and hydrological services across Africa.
