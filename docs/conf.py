from __future__ import annotations
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
    'sphinxcontrib.mermaid',
]

python_use_unqualified_type_names = True
autodoc_member_order = 'bysource'
autoclass_content = 'both'
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
html_theme_options = {
    'source_repository': 'https://github.com/Kenny2github/mw-api-client',
    'source_branch': 'main',
}
html_static_path = ['_static']

# -- Hooks -------------------------------------------------------------------
from typing import TYPE_CHECKING, get_overloads
import inspect

if TYPE_CHECKING:
    # import sphinx
    import sphinx.application
    from typing import Any, Literal

## Update return annotations based on overloads
def overloaded_retann(
    app: sphinx.application.Sphinx,
    objtype: Literal['module', 'class', 'exception', 'function', 'method', 'attribute'],
    fullname: str,
    obj: Any,
    options: dict[str, bool],
    args: str | None,
    retann: str | None
) -> (tuple[str | None, str | None] | None):
    if objtype != 'method':
        return None
    for overload in get_overloads(obj):
        anns = inspect.get_annotations(overload, eval_str=False)
        cls = fullname.split('.')[-2]
        if anns.get('limit', '').strip().casefold() == 'literal[1]':
            continue # ignore the One[]Generator overloads
        if anns.get('self', '').split('[')[0].endswith(cls):
            retann = anns['return']
            break
    return args, retann

def setup(app: sphinx.application.Sphinx) -> None:
    app.connect('autodoc-process-signature', overloaded_retann)
