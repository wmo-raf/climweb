# Manage Translations

## Docs Translations

Generate ***.po** translation files

```sh
sphinx-build -b gettext . _build/gettext
```

```sh
pip install sphinx-intl
```

```sh
sphinx-intl update -p _build/gettext -l fr
```

---

Translate ***.po** locales files listed in LOCALE_PATHS 

```sh
python manage.py translate_messages -l fr
```

---

Build docs in target language (generate ***.mo** files)

```sh
sphinx-build -b html -D language=fr . _build/html/fr
```

---

## CMS Translations

Generate ***.po** translation files for locale folders listed in LOCALE_PATHS

```sh
python manage.py makemessages -l fr
```

Translate ***.po** locales files listed in LOCALE_PATHS 

```sh
python manage.py translate_messages -l fr
```

Build docs in target language (generate ***.mo** files)

```sh
python manage.py compilemessages
```