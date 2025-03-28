# -*- coding: utf-8 -*-
#
# Configuration file for the Sphinx documentation builder.
#
# This file does only contain a selection of the most common options. For a
# full list see the documentation:
# http://www.sphinx-doc.org/en/master/config

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
from importlib.metadata import version as get_version
sys.path.insert(0, os.path.abspath('../notebook/'))


# -- Project information -----------------------------------------------------

project = 'pyecsca'
copyright = '2018-2025, Jan Jancar'
author = 'Jan Jancar'

sys.path.append(os.path.abspath('..'))

release: str = get_version("pyecsca")
# for example take major/minor
version: str = ".".join(release.split('.')[:2])


# -- General configuration ---------------------------------------------------

# If your documentation needs a minimal Sphinx version, state it here.
#
# needs_sphinx = '1.0'

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx_autodoc_typehints',
    'sphinx.ext.todo',
    'sphinx.ext.mathjax',
    'sphinx.ext.linkcode',
    'sphinx_paramlinks',
    'sphinx_design',
    'nbsphinx',
    'sphinx_plausible',
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# The suffix(es) of source filenames.
# You can specify multiple suffix as a list of string:
#
# source_suffix = ['.rst', '.md']
source_suffix = {'.rst': 'restructuredtext'}

# The master toctree document.
master_doc = 'index'

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#
# This is also used if you do content translation via gettext catalogs.
# Usually you set "language" from the command line for these cases.
language = "en"

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store', '**.ipynb_checkpoints']

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = "trac"

add_module_names = False


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'alabaster'

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
#
html_theme_options = {
    'logo': 'logo_black.png',
    'logo_name': True,
    'logo_text_align': 'center',
    'fixed_sidebar': True,
    'code_font_family': "'IBM Plex Mono', 'Consolas', 'Menlo', 'DejaVu Sans Mono', 'Bitstream Vera Sans Mono', monospace",
    'caption_font_family': "'IBM Plex Sans', 'Helvetica Neue', sans-serif",
    'head_font_family': "'IBM Plex Sans', 'Helvetica Neue', sans-serif",
    'font_family': "'IBM Plex Sans', 'Helvetica Neue', sans-serif",
    'github_button': False,
    'github_banner': False,
    'github_user': 'J08nY',
    'github_repo': 'pyecsca'
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

html_favicon = "_static/logo_black.png"

html_css_files = [
    'custom.css',
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.3.0/css/all.min.css',
    'https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:ital,wght@0,100;0,200;0,300;0,400;0,500;0,600;0,700;1,100;1,200;1,300;1,400;1,500;1,600;1,700&family=IBM+Plex+Sans:ital,wght@0,100;0,200;0,300;0,400;0,500;0,600;0,700;1,100;1,200;1,300;1,400;1,500;1,600;1,700&display=swap'
]

# Custom sidebar templates, must be a dictionary that maps document names
# to template names.
#
# The default sidebars (for documents that don't match any pattern) are
# defined by theme itself.  Builtin themes are using these templates by
# default: ``['localtoc.html', 'relations.html', 'sourcelink.html',
# 'searchbox.html']``.
#

html_sidebars = {
    '**': [
        'about.html',
        'navigation.html',
        'nav.html',
        'relations.html',
        'searchfield.html'
    ]
}

# -- Options for HTMLHelp output ---------------------------------------------

# Output file base name for HTML help builder.
htmlhelp_basename = 'pyecscadoc'


# -- Options for LaTeX output ------------------------------------------------

latex_elements = {
    # The paper size ('letterpaper' or 'a4paper').
    #
    'papersize': 'a4paper',

    # The font size ('10pt', '11pt' or '12pt').
    #
    # 'pointsize': '10pt',

    # Additional stuff for the LaTeX preamble.
    #
    'preamble': r"""\usepackage{pmboxdraw}""",

    # Latex figure (float) alignment
    #
    # 'figure_align': 'htbp',
}

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title,
#  author, documentclass [howto, manual, or own class]).
latex_documents = [
    (master_doc, 'pyecsca.tex', 'pyecsca Documentation',
     'Jan Jancar', 'manual'),
]


# -- Options for manual page output ------------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [
    (master_doc, 'pyecsca', 'pyecsca Documentation',
     [author], 1)
]


# -- Options for Texinfo output ----------------------------------------------

# Grouping the document tree into Texinfo files. List of tuples
# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [
    (master_doc, 'pyecsca', 'pyecsca Documentation',
     author, 'pyecsca', 'Python Elliptic Curve Side-Channel Analysis toolkit',
     'Miscellaneous'),
]


# -- Options for Epub output -------------------------------------------------

# Bibliographic Dublin Core info.
epub_title = project

# The unique identifier of the text. This can be a ISBN number
# or the project homepage.
#
# epub_identifier = ''

# A unique identification for the text.
#
# epub_uid = ''

# A list of files that should not be packed into the epub file.
epub_exclude_files = ['search.html']


# -- Extension configuration -------------------------------------------------

todo_include_todos = True

autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "inherited-members": "object, int, float, str, list, dict, set",
    "show-inheritance": True,
    "member-order": "bysource",
    # "special-members": "__init__"
}
autodoc_typehints = "signature"
autodoc_typehints_format = "short"

sd_fontawesome_latex = True

autoclass_content = "both"

nbsphinx_allow_errors = True
nbsphinx_execute = "never"

nbsphinx_prolog = """
{% set notebook_path = env.doc2path(env.docname, base=None) | replace("notebook/", "") %}
.. raw:: html

    <a href="https://mybinder.org/v2/gh/J08nY/pyecsca-notebook/HEAD?labpath={{ notebook_path }}" class="sd-badge sd-outline-primary">MyBinder</a>

"""


def linkcode_resolve(domain, info):
    if domain != 'py':
        return None
    if not info['module']:
        return None
    filename = info['module'].replace('.', '/')
    if "codegen" in filename:
        return "https://github.com/J08nY/pyecsca-codegen/tree/master/%s.py" % filename
    else:
        return "https://github.com/J08nY/pyecsca/tree/master/%s.py" % filename


plausible_domain = "pyecsca.org"
plausible_script = "https://plausible.neuromancer.sk/js/script.js"
plausible_enabled = (
    'GITHUB_ACTION' in os.environ
    and os.environ.get('GITHUB_REPOSITORY', '').lower() == 'j08ny/pyecsca'
    and os.environ.get('GITHUB_REF') == 'refs/heads/master'
    )
