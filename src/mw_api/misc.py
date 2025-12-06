from __future__ import annotations
from typing import Literal

Limit = int | Literal['max'] | None

class Namespace:
    """
    A (built-in or custom) namespace.

    The :attr:`id` |key-attr| |population| :meth:`Wiki.update_namespaces`.

    Attributes:
        id: Namespace ID configured in MediaWiki.
    """

    id: int

    def __init__(self) -> None:
        """|noinit| Use :meth:`Wiki.namespace`."""
        raise NotImplementedError

    @property
    def name(self) -> str:
        """Displayed name for the namespace."""
        raise NotImplementedError

    @property
    def canonical(self) -> str:
        """Canonical (MediaWiki) name for the namespace. On Wikipedia, this is
        "Project" for the "Wikipedia" namespace.
        """
        raise NotImplementedError

    @property
    def first_letter_case(self) -> bool:
        """If :const:`True` (the norm), the first letter of the title of every
        page in this namespace is normalized uppercase.
        """
        raise NotImplementedError

    @property
    def subpages(self) -> bool:
        """If :const:`False`, slashes ``/`` in titles of pages in this
        namespace do not separate pages from subpages.
        """
        raise NotImplementedError

    @property
    def content(self) -> bool:
        """If :const:`True`, pages in this namespace are `content pages`_.

        .. _content pages: https://www.mediawiki.org/wiki/Manual:$wgContentNamespaces
        """
        raise NotImplementedError

    @property
    def nonincludable(self) -> bool:
        """If :const:`True`, pages in this namespace cannot be transcluded (via
        ``{{page}}``).
        """
        raise NotImplementedError

    @property
    def defaultcontentmodel(self) -> str:
        """The default `content model`_ of pages in this namespace on creation.

        .. _content model: https://www.mediawiki.org/wiki/Content_model
        """
        raise NotImplementedError
