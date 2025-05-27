# General Architecture

## Base Module (`/base/`)

- Core models and database schema
- Custom blocks and templates
- Form handling and validation
- View controllers
- Utility functions and mixins
- Task management system using Celery

## Configuration (`/config/`):

- Environment-specific settings
- URL routing
- API endpoints
- Database engine configuration
- Static file handling
- Internationalization support

## Content Structure

The system is organized into several key content sections, each implemented as a Django/Wagtail app:

1. **Home** (/`pages/home/`)
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

## Page Structure

Each page type, where fully implemented as a Django/Wagtail app, follows a consistent structure:

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