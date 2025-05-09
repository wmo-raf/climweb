# Climweb Technical Introduction

## Architecture

### Overview

Climweb is a Django-based web application with Wagtail CMS integration, designed for use by National Meteorological and
Hydrological Services (NMHSs) in their content management and deliver of climate information and services.

The system is designed to be modular and extensible, allowing for easy addition of new features and content types. It is
built with a focus on customization and flexibility, enabling NMHSs to tailor the system to their specific needs.

### Core Components

#### Web Framework & CMS

- Built on Django framework with Wagtail CMS integration
- Uses ASGI (Asynchronous Server Gateway Interface) for modern web capabilities
- The system Implements both WSGI and ASGI configurations for flexibility

#### Backend Architecture:

##### Base Module (`/base/`)**

- Core models and database schema
- Custom blocks and templates
- Form handling and validation
- View controllers
- Utility functions and mixins
- Task management system using Celery

##### Configuration (`/config/`):

- Environment-specific settings
- URL routing
- API endpoints
- Database engine configuration
- Static file handling
- Internationalization support

##### Content Structure

The system is organized into several key content sections, each implemented as a Django/Wagtail app:

1. **Core Content Sections**

- Home (/`pages/home/`)
    - Custom home page implementation
    - Interactive map component (Vue.js integration)
    - Custom blocks and templates
    - Localization support

2. **Information Services**

- Publications (`/pages/publications/`)
- Products (`/pages/products/`)
- Services (`/pages/services/`)
- News (`/pages/news/`)
- Events (`/pages/events/`)

3. **Data & Research**

- Weather (`/pages/weather/`)
- Satellite Imagery (`/pages/satellite_imagery/`)
- City Climate (`/pages/cityclimate/`)
- Stations (`/pages/stations/`)
- Data Request (`/pages/data_request/`)

4. **User Interaction**

- Contact (`/pages/contact/`)
- Feedback (`/pages/feedback/`)
- Email Subscription (`/pages/email_subscription/`)
- Surveys (`/pages/surveys/`)

5. **Media & Resources**

- Media Center (`/pages/mediacenter/`)
- Videos (`/pages/videos/`)
- Web Stories (`/pages/webstories/`)

6. **Specialized Features**

- WDQMS (WIGOS Data Quality Management System) (`/pages/wdqms/`)
- Glossary (`/pages/glossary/`)
- Search (`/pages/search/`)

##### Page Architecture

Each page type, where fully implmented as a Django/Wagtail app, follows a consistent structure:

1. **Models (`models.py`)**

- Database schema
- Content structure
- Custom fields and relationships

2. **Views (`views.py`)**

- Page rendering logic
- Data processing
- Custom view handlers

3. **Templates (`/templates/`)**

- Page layouts
- Component templates
- Custom blocks

4. **Static Assets (`/static/`)**

- CSS/JS files
- Static Images and media
- Frontend components

4. **Configuration**

- URL routing (`urls.py`)
- Wagtail hooks (`wagtail_hooks.py`)
- App configuration (`apps.py`)

### Extending Climweb

At the base, Climweb provides a generic, well researched and tested content structure that addresses most of the
needs of the NMHSs, in providing a functional and user-friendly website. This structure is designed to be flexible and
extensible, allowing for easy addition of services and products provided by the NMHSs.

However, the needs of each NMHSs may vary, and some may require additional features or customizations to meet their
specific requirements. To address this, ClimWeb can be extended by creating new modules, that we call `Plugins`, which
can then be integrated into the system.

These plugins can be used to add new features, modify existing functionality, or integrate with external systems.
These can be developed by third-party developers, allowing for a wide range of customization options.

Read more about the plugin system in the [Plugin System](../technical/plugins.md) section.