from dataclasses import dataclass
from typing import Literal

Limit = int | Literal['max'] | None

@dataclass
class Namespace:
    """
    A (built-in or custom) namespace. |noinit|

    Attributes:
        id: Namespace ID configured in MediaWiki.
        name: Displayed name for the namespace.
        canonical: Canonical (MediaWiki) name for the namespace. On Wikipedia,
            this is "Project" for the "Wikipedia" namespace.
        subpages: If :const:`False`, slashes ``/`` in titles of pages in this
            namespace do not separate pages from subpages.
        content: If :const:`True`, pages in this namespace are `content pages`_.
        nonincludable: If :const:`True`, pages in this namespace cannot be
            transcluded (via ``{{page}}``).
        defaultcontentmodel: The default `content model`_ of pages in this
            namespace on creation.

    .. _content pages: https://www.mediawiki.org/wiki/Manual:$wgContentNamespaces
    .. _content model: https://www.mediawiki.org/wiki/Content_model
    """
    id: int
    name: str
    first_letter_case: bool
    subpages: bool
    content: bool
    nonincludable: bool
    canonical: str = ''
    defaultcontentmodel: str = 'wikitext'
