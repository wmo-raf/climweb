#
#
# This file is execfile()d with the current directory set to its
# containing dir.
#
# Note that not all possible configuration values are present in this
# autogenerated file.
#
# All configuration values have a default; values that are commented out
# serve to show the default.

import os
import sys
from datetime import datetime

# on_rtd is whether we are on readthedocs.org, this line of code grabbed from docs.readthedocs.org
on_rtd = os.environ.get("READTHEDOCS", None) == "True"

html_theme = 'sphinx_wagtail_theme'

html_theme_options = {
    "project_name": "ClimWeb Documentation",
    "github_url": "https://github.com/wmo-raf/climweb/blob/main/docs/",
    "header_links": "En|https://climweb.readthedocs.io/en, Fr|https://climweb.readthedocs.io/fr, Sw|https://climweb.readthedocs.io/sw",
    "footer_links": ",".join([
        "Demo|http://20.56.94.119/cms/",
        "Packages|https://github.com/wmo-raf",
        "Developers|https://github.com/wmo-raf/climweb-docker"
    ]),
}

html_css_files = ["css/theme.overrides.css"]

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
sys.path.insert(0, os.path.abspath(".."))

import django

# Autodoc may need to import some models modules which require django settings
# be configured
os.environ["DJANGO_SETTINGS_MODULE"] = "wagtail.test.settings"
django.setup()

# Use SQLite3 database engine so it doesn't attempt to use psycopg2 on RTD
os.environ["DATABASE_ENGINE"] = "django.db.backends.sqlite3"

# -- General configuration ------------------------------------------------

# If your documentation needs a minimal Sphinx version, state it here.
# needs_sphinx = '1.0'

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx_copybutton",
    "myst_parser",
    "sphinx_wagtail_theme",
]

if not on_rtd:
    extensions.append("sphinxcontrib.spelling")

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# The suffix of source filenames.
source_suffix = ".rst"

# The encoding of source files.
# source_encoding = 'utf-8-sig'

# The master toctree document.
master_doc = "index"

# General information about the project.
project = "ClimWeb Documentation"
copyright = f"{datetime.now().year}, WMO Regional Office For Africa"

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.

import re

# The full version, including alpha/beta/rc tags.
release = re.sub('^v', '', os.popen('git describe --tags').read().strip())
# The short X.Y version.
version = release

# from nmhs_cms import VERSION, __version__

# # The short X.Y version.
# version = "{}.{}".format(VERSION[0], VERSION[1])


# # The full version, including alpha/beta/rc tags.
# release = __version__

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
# language = 'en'
# gettext_uuid = True
# gettext_compact = False
locales_dirs = ['locale']

# There are two options for replacing |today|: either, you set today to some
# non-false value, then it is used:
# today = ''
# Else, today_fmt is used as the format for a strftime call.
# today_fmt = '%B %d, %Y'

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns = ["_build", "README.md"]

# The reST default role (used for this markup: `text`) to use for all
# documents.
# default_role = None

# If true, '()' will be appended to :func: etc. cross-reference text.
# add_function_parentheses = True

# If true, the current module name will be prepended to all description
# unit titles (such as .. function::).
# add_module_names = True

# If true, sectionauthor and moduleauthor directives will be shown in the
# output. They are ignored by default.
# show_authors = False

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = None

# A list of ignored prefixes for module index sorting.
# modindex_common_prefix = []

# If true, keep warnings as "system message" paragraphs in the built documents.
# keep_warnings = False

# splhinxcontrib.spelling settings

spelling_lang = "en"
spelling_word_list_filename = "spelling_wordlist.txt"

# sphinx.ext.intersphinx settings
intersphinx_mapping = {
    "django": (
        "https://docs.djangoproject.com/en/stable/",
        "https://docs.djangoproject.com/en/stable/_objects/",
    )
}

# -- Options for HTML output ----------------------------------------------

# Theme options are theme-specific and customise the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
# html_theme_options = {
#     }

# The name for this set of Sphinx documents.  If None, it defaults to
# "<project> v<release> documentation".
# html_title = None

# A shorter title for the navigation bar.  Default is the same as html_title.
# html_short_title = None

# The name of an image file (relative to this directory) to place at the top
# of the sidebar.
# html_logo = 'logo.png'

# The name of an image file (within the static path) to use as favicon of the
# docs.  This file should be a Windows icon file (.ico) being 16x16 or 32x32
# pixels large.
html_favicon = "favicon.ico"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]

# Add any extra paths that contain custom files (such as robots.txt or
# .htaccess) here, relative to this directory. These files are copied
# directly to the root of the documentation.
# html_extra_path = ["public"]

# If not '', a 'Last updated on:' timestamp is inserted at every page bottom,
# using the given strftime format.
html_last_updated_fmt = '%b %d, %Y'

# If true, SmartyPants will be used to convert quotes and dashes to
# typographically correct entities.
# html_use_smartypants = True

# Custom sidebar templates, maps document names to template names.
# html_sidebars = {}

# Additional templates that should be rendered to pages, maps page names to
# template names.
# html_additional_pages = {}

# If false, no module index is generated.
# html_domain_indices = True

# If false, no index is generated.
# Since we are implementing search with Algolia DocSearch, we do not need Sphinx to
# generate its own index. It might not hurt to keep the Sphinx index, but it
# could potentially speed up the build process.
html_use_index = True

# If true, the index is split into individual pages for each letter.
# html_split_index = False

# If true, links to the reST sources are added to the pages.
# html_show_sourcelink = True

# If true, "Created using Sphinx" is shown in the HTML footer. Default is True.
html_show_sphinx = True

# If true, "(C) Copyright ..." is shown in the HTML footer. Default is True.
# html_show_copyright = True

# If true, an OpenSearch description file will be output, and all pages will
# contain a <link> tag referring to it.  The value of this option must be the
# base URL from which the finished HTML is served.
# html_use_opensearch = ''

# This is the file name suffix for HTML files (for example ".xhtml").
# html_file_suffix = None

# Output file base name for HTML help builder.
htmlhelp_basename = "Climwebdoc"

# -- Options for LaTeX output ---------------------------------------------

# latex_elements = {
# The paper size ('letterpaper' or 'a4paper').
# 'papersize': 'a4paper',
# The font size ('10pt', '11pt' or '12pt').
# 'pointsize': '11pt',
# Additional stuff for the LaTeX preamble.
# 'preamble': '',
# 'preamble': r'''
#     \input{/Users/grace/Projects/WMO/nmhs-cms.wiki/cover.tex}
# ''',
# "maketitle": "\\input{_static/cover.tex}"
# }


# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title,
#  author, documentclass [howto, manual, or own class]).
latex_documents = [
    ("index", "climweb.tex", "ClimWeb Documentation", "ORGANISATION", "manual"),
]

# with open('./cover.tex', 'r') as cover_page_file:
#     custom_tex = cover_page_file.read()

# latex_elements['preamble'] = custom_tex

# The name of an image file (relative to this directory) to place at the top of
# the title page.
# latex_logo = None

# For "manual" documents, if this is true, then toplevel headings are parts,
# not chapters.
# latex_use_parts = False

# If true, show page references after internal links.
# latex_show_pagerefs = False

# If true, show URL addresses after external links.
# latex_show_urls = False

# Documents to append as an appendix to all manuals.
# latex_appendices = []

# If false, no module index is generated.
# latex_domain_indices = True

# -- Options for manual page output ---------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [("index", "ClimWeb", "ClimWeb Documentation", ["ORGANISATION"], 1)]

# If true, show URL addresses after external links.
# man_show_urls = False

# -- Options for Texinfo output -------------------------------------------

# Grouping the document tree into Texinfo files. List of tuples
# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [
    (
        "index",
        "ClimWeb",
        "ClimWeb Documentation",
        "One line description of project.",
        "Miscellaneous",
    ),
]


# Documents to append as an appendix to all manuals.
# texinfo_appendices = []

# If false, no module index is generated.
# texinfo_domain_indices = True

# How to display URL addresses: 'footnote', 'no', or 'inline'.
# texinfo_show_urls = 'footnote'

# If true, do not generate a @detailmenu in the "Top" node's menu.
# texinfo_no_detailmenu = False


def setup(app):
    app.add_js_file("js/banner.js")
