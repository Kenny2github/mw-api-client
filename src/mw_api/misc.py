from __future__ import annotations
from typing import TYPE_CHECKING, Literal, overload

if TYPE_CHECKING:
    from .page import Page
    from .wiki import Wiki

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

class RecentChange:
    """
    A handle on a recent change, uniquely identified by its :attr:`id`. Unlike
    :class:`page.Page` and :class:`user.User`, recent changes are not cached as
    they are not user-constructible at all.

    The :attr:`id` |key-attr| That said, only one API endpoint provides the
    data for recent changes, so any situation where the respective data is
    unavailable is likely a bug and should be reported as such.

    Attributes:
        id: The recent change ID.
    """

    id: int
    wiki: Wiki

    def __init__(self) -> None:
        """|noinit| Use :meth:`Wiki.recentchanges`."""

    @property
    def page(self) -> Page:
        """The page to which the change was made."""
        raise NotImplementedError

    async def patrol(self) -> None:
        """Patrol this recent change.

        Raises:
            APIError: If patrolling failed.
        """
        raise NotImplementedError

    @overload
    async def tag(self, *, add: list[Tag], reason: str | None) -> None: ...
    @overload
    async def tag(self, *, remove: list[Tag], reason: str | None) -> None: ...
    @overload
    async def tag(self, *, add: list[Tag], remove: list[Tag], reason: str | None) -> None: ...
    async def tag(self, *, reason: str | None, add: list[Tag] | None = None, remove: list[Tag] | None = None) -> None:
        raise NotImplementedError

class Tag:
    """
    A handle on a recent change tag, uniquely identified by its :attr:`name`.
    There is only one :class:`Tag` instance per :class:`Wiki` per name.

    The :attr:`name` |key-attr| |population| :meth:`Wiki.update_tags`.

    Attributes:
        name: The recent change tag name.
    """

    name: str
    wiki: Wiki

    @property
    def displayname(self) -> str:
        r"""The HTML name displayed on Special\:Tags."""
        raise NotImplementedError

    @property
    def description(self) -> str:
        r"""The description displayed on Special\:Tags."""
        raise NotImplementedError

    @property
    def hitcount(self) -> int:
        """The number of times this tag has been hit used in a change (as of
        the last time it was cached).
        """
        raise NotImplementedError

    @property
    def defined(self) -> bool:
        """If :const:`False`, this tag is no longer defined by any source
        (the :attr:`source` property should be empty).
        """
        raise NotImplementedError

    @property
    def source(self) -> list[Literal['software', 'extension', 'manual']]:
        """The things that can apply the tag - MediaWiki software, including
        extensions [software], extensions specifically [extension], or users
        manually when making edits [manual].
        """
        raise NotImplementedError

    @property
    def active(self) -> bool:
        """If :const:`False`, this tag is no longer active and cannot be
        applied (but may still be :attr:`defined`).
        """
        raise NotImplementedError
