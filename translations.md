# Manage Translations

## Docs Translations

1. While in **docs** directory, Generate ***.po** translation files

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

2. While at **root of project**, Translate ***.po** locales files listed in LOCALE_PATHS 

```sh
python manage.py translate_messages -l fr
```

---

3. While in **docs** directory, Build docs in target language (generate ***.mo** files)

```sh
sphinx-build -b html -D language=fr . _build/html/fr
```

---

## ClimWeb Translations

1. Generate ***.po** translation files for locale folders listed in LOCALE_PATHS

```sh
python manage.py makemessages -l fr
```

2. Translate ***.po** locales files listed in LOCALE_PATHS 

```sh
python manage.py translate_messages -l fr
```

3. Build docs in target language (generate ***.mo** files)

```sh
python manage.py compilemessages
```
