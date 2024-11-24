# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'mw-api-client'
copyright = '2024, AbyxDev'
author = 'AbyxDev'
from importlib.metadata import version as get_version

release = get_version('mw-api-client')

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.intersphinx',
    'sphinx.ext.napoleon',
]

autodoc_member_order = 'bysource'
autodoc_default_options = {
    'members': True,
    'show-inheritance': True,
    'member-order': 'bysource',
    'exclude-members': '__weakref__',
}
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
}

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'furo'
html_static_path = ['_static']
