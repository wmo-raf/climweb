# Technical Guides

## Architecture

### Overview

Climweb is a Django-based web application with Wagtail CMS integration, designed for use by National Meteorological and
Hydrological Services (NMHSs) in their content management and deliver of climate information and services.

The system is designed to be modular and extensible, allowing for easy addition of new features and content types. It is
built with a focus on customization and flexibility, enabling NMHSs to tailor the system to their specific needs.

### Web Framework & CMS

- Built on Django framework with Wagtail CMS integration
- Uses ASGI (Asynchronous Server Gateway Interface) for modern web capabilities
- The system Implements both WSGI and ASGI configurations for flexibility

### Backend Architecture

The backend architecture section describes the core components of Climweb's backend.

### Pages/Apps structure

The pages/apps structure section provides an overview of how the pages/apps are organized within Climweb, using the
conventional Django app structure.

### Extending Climweb

The extending Climweb section discusses how to extend the functionality of Climweb by creating custom plugins, which add
more features and capabilities to the system.

### Management Commands

Climweb provides a set of management commands that can be used to perform various tasks related to the system's
operation and maintenance.

The management commands section provides an overview of these commands and their usage.

```{toctree}
---
maxdepth: 1
---
development/index
general-architecture
backup-restore
management-commands
extending-climweb/index
```