from __future__ import annotations
from typing import TYPE_CHECKING, Any, Literal, overload
from datetime import datetime

if TYPE_CHECKING:
    from .page import Page, File, Revision
    from .user import User
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

    @property
    def tags(self) -> list[Tag]:
        """The tags associated with this change."""
        raise NotImplementedError

    @property
    def change(self) -> Revision | LogEntry:
        """The actual change being made."""
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

class LogEntry:
    """
    A handle on a wiki log entry, uniquely identified by its :attr:`id`.
    There is only one :class:`LogEntry` instance per :class:`Wiki` per ID.

    The :attr:`id` |key-attr| |population| :meth:`update_info`.

    Attributes:
        id: The log ID.
    """

    id: int
    wiki: Wiki

    def __init__(self) -> None:
        """|noinit|"""
        raise NotImplementedError

    async def update_info(self) -> None:
        """Fetch all available metadata about the log entry and cache it,
        updating the cache if previously fetched.

        After calling this method, every :class:`property` of this instance
        should return data instead of raising :exc:`KeyError`.

        Raises:
            APIError: If fetching data failed (e.g. because the log entry does
                not exist)
        """
        raise NotImplementedError

    async def patrol(self) -> bool:
        """Patrol the recent change corresponding to this log entry.

        This is an expensive call. It requires first looking up the recent
        change corresponding to this log entry, then patrolling it if it is
        unpatrolled. The corresponding MediaWiki diff functionality really
        does do this too, but it has the advantage of direct database access.

        Returns:
            :const:`True` if the log entry was patrolled, or :const:`False`
            if it was already patrolled.

        Raises:
            APIError: If fetching data failed (e.g. because the log entry does
                not exist) or patrolling failed.
        """
        raise NotImplementedError

    @property
    def page(self) -> Page:
        """The page targeted by this log entry."""
        raise NotImplementedError

    @property
    def type(self) -> str:
        """The high-level type of this log entry."""
        raise NotImplementedError

    @property
    def action(self) -> str:
        """The granular action of this log entry."""
        raise NotImplementedError

    @property
    def user(self) -> User:
        """The user responsible for this log entry."""
        raise NotImplementedError

    @property
    def timestamp(self) -> datetime:
        """The timestamp when this log entry was made."""
        raise NotImplementedError

    @property
    def comment(self) -> str:
        """The action summary for this log entry."""
        raise NotImplementedError

    @property
    def params(self) -> dict[str, Any]:
        """Additional details associated with this log entry."""
        raise NotImplementedError

    @property
    def tags(self) -> list[Tag]:
        """The recent change tags associated with this log entry."""
        raise NotImplementedError

class ImageInfo:
    """
    A handle on a file image revision, uniquely identified by its :attr:`file`
    and :attr:`timestamp` (file revisions have no IDs). There is only one
    :class:`ImageInfo` instance per :class:`File` and timestamp.

    The :attr:`file` and :attr:`timestamp` data |key-attr| That said, only one
    API endpoint provides the data for image info, so any situation where the
    respective data is unavailable is likely a bug and should be reported as such.

    Attributes:
        file: The file of which this is a revision.
        timestamp: The file upload timestamp.
    """

    file: File
    timestamp: datetime
    wiki: Wiki

    def __init__(self) -> None:
        """|noinit|"""
        raise NotImplementedError

    async def update_info(self) -> None:
        """Fetch all available metadata about the log entry and cache it,
        updating the cache if previously fetched.

        After calling this method, every :class:`property` of this instance
        should return data instead of raising :exc:`KeyError`.

        Raises:
            APIError: If fetching data failed (e.g. because the log entry does
                not exist)
        """
        raise NotImplementedError

    async def patrol(self) -> bool:
        """Patrol the recent change corresponding to this log entry.

        This is an expensive call. It requires first looking up the recent
        change corresponding to this log entry, then patrolling it if it is
        unpatrolled. The corresponding MediaWiki diff functionality really
        does do this too, but it has the advantage of direct database access.

        Returns:
            :const:`True` if the log entry was patrolled, or :const:`False`
            if it was already patrolled.

        Raises:
            APIError: If fetching data failed (e.g. because the log entry does
                not exist) or patrolling failed.
        """
        raise NotImplementedError

    @property
    def user(self) -> User:
        """The user responsible for this log entry."""
        raise NotImplementedError

    @property
    def comment(self) -> str:
        """The action summary for this log entry."""
        raise NotImplementedError

    @property
    def size(self) -> int:
        """File size in bytes."""
        raise NotImplementedError

    @property
    def width(self) -> int:
        """Image width in pixels."""
        raise NotImplementedError

    @property
    def height(self) -> int:
        """Image height in pixels."""
        raise NotImplementedError

    @property
    def mime(self) -> str:
        """File MIME type."""
        raise NotImplementedError

    @property
    def url(self) -> str:
        """Direct URL to the file."""
        raise NotImplementedError
