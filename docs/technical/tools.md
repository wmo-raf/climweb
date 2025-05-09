# Development tools & Stack

## Backend

### PostgreSQL + PostGIS

Climweb uses PostgreSQL for persistent storage.

PostGIS is an extension to PostgreSQL that adds support for geographic objects

https://www.postgresql.org/

### Django + Wagtail CMS

At the core of the system we run the Django framework. A popular framework was chosen
to lower the barrier of creating custom modules that extend Climweb. We also looked for a batteries included,
simple, and proven framework. Django was the obvious choice.

https://www.djangoproject.com

Wagtail is an open-source content management system (CMS) built on top of Django, a popular Python web framework. It's
designed to be developer-friendly, flexible, and provide a modern, intuitive editing experience for content creators.

The user interface of the Wagtail Admin and the overall editing experience provided by Wagtail made it a good choice for
Climweb, as it allows for easy content creation and management.

https://wagtail.org/

### Django REST framework

To quickly create endpoints, handle external authentication, object serialization, validation,
and do many more things we use Django REST Framework.

https://www.django-rest-framework.org/

### Internationalization

For internationalization (i18n), we leverage Django's built-in support. Django's internationalization framework allows
us to easily translate our web application into multiple languages.

To use Django's internationalization features, we wrap our text with a special function called `gettext` or
`gettext_lazy`.
For more information, refer to
the [Django Internationalization and Localization documentation](https://docs.djangoproject.com/en/3.2/topics/i18n/).

https://mjml.io/

## Frontend

We mostly use Django templates for the frontend. However, we also use `Vue.js` for some parts of the frontend that
require more interactivity, such as the home page map component.

We use a custom approach to integrate Vue.js with Django. This approach combines the strengths of Django's templating
system with Vue's reactive components and is summarized as follows:

**Key steps in the integration of Vue into Django/Wagtail:**

- **Vue Project Setup**: Use Vite to scaffold a Vue project within the Django project directory, enabling modern
  JavaScript development with features like hot module replacement.

- **Django Template Integration**: Embed Vue components directly into Django templates by adding a <div id="app"></div>
  and including the Vue application's script via a <script type="module"> tag pointing to the Vite dev server.

- **Development Workflow:** Leverage Vite's development server for rapid development and testing, allowing real-time
  updates to Vue components without full page reloads.

- **Production Build**: Configure Vite to output a production-ready build, and adjust Django's static files settings to
  serve the compiled assets appropriately.

- **State Management:** Incorporate Pinia for state management within Vue components, facilitating organized and
  maintainable application state.

This integration strategy enables us to enhance our templates with dynamic Vue components while
maintaining the benefits of Django's server-side rendering and template system.

The approach is explained in
details [here](https://ilikerobots.medium.com/django-vue-vite-rest-not-required-ca63cfa558fd)

### Icons

We mostly use Font Awesome for SVG icons. Font Awesome is a popular icon library that provides a wide range of scalable
vector icons. We use [wagtail-font-awesome-svg](https://github.com/wagtail-nest/wagtail-font-awesome-svg), a Wagtail
package that allows us to use Font Awesome icons in Wagtail projects.

https://fontawesome.com/