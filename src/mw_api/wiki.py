from __future__ import annotations
from datetime import datetime
from typing import Literal, Self

class Wiki:
    """
    A handle on the site itself and the construction point for all objects
    related to it.

    |noinit| For construction, see :meth:`new`.

    Attributes:
        me: The currently logged-in user, or :data:`None` if not logged in
            (not recommended).
    """

    me: CurrentUser | None = None

    @classmethod
    async def new(cls, api_url: str, user_agent: str) -> Self:
        """
        Parameters:
            api_url: URL to api.php - all requests will go here
            user_agent: User-Agent HTTP header to provide.
                In lieu of a reasonable default, this parameter is required.
        """
        raise NotImplementedError

    async def update_namespaces(self) -> None:
        """Fetch all available metadata about namespaces on this wiki and cache
        it, updating the cache if previously fetched. Called by :meth:`new`.
        """
        raise NotImplementedError

    async def update_tags(self) -> None:
        """Fetch all available metadata about tags on this wiki and cache it,
        updating the cache if previously fetched. Called by :meth:`new`.
        """
        raise NotImplementedError

    async def login(self, username: str, password: str) -> None:
        """Login with a bot password. For this to work, you need to have
        generated a password on Special:BotPasswords. Regular login using the
        clientlogin API module is not currently supported.

        Parameters:
            username: The name of the bot account to login to.
            password: The bot password from Special:BotPasswords.

        Raises:
            APIError: If login failed.
        """
        raise NotImplementedError

    def page(self, title: str) -> Page:
        """Get a handle on a wiki page.

        Note: Pages with special functionality like categories and files have
        corresponding subclasses (e.g. :class:`Category`, :class:`File`) whose
        instances may also be returned by this method based on the namespace
        included in the title.

        Parameters:
            title: The page's full title (Namespace:Title).

        Returns:
            Instance of :class:`Page` or subclass with the given title.
        """
        raise NotImplementedError

    def talk_page(self, title: str) -> TalkPage:
        """Get a handle on a wiki talk page (in any talk namespace).

        Parameters:
            title: The page's full title (Talk:Title, User talk:Title, etc.).

        Returns:
            Page handle.

        Raises:
            ValueError: If ``title`` is not the title of a talk page.
        """
        raise NotImplementedError

    def file(self, title: str) -> File:
        r"""Get a handle on a wiki file page.

        Parameters:
            title: The page's full title (File\:Title).

        Returns:
            Page handle.

        Raises:
            ValueError: If ``title`` is not the title of a file.
        """
        raise NotImplementedError

    def template(self, title: str) -> Template:
        """Get a handle on a wiki template page.

        Parameters:
            title: The page's full title (Template:Title).

        Returns:
            Page handle.

        Raises:
            ValueError: If ``title`` is not the title of a template.
        """
        raise NotImplementedError

    def category(self, title: str) -> Category:
        """Get a handle on a wiki category page.

        Parameters:
            title: The page's full title (Category:Title).

        Returns:
            Page handle.

        Raises:
            ValueError: If ``title`` is not the title of a category.
        """
        raise NotImplementedError

    def user(self, name: str) -> User:
        """Get a handle on a wiki user.

        Parameters:
            name: The username of the user.

        Returns:
            User handle.
        """
        raise NotImplementedError

    def namespace(self, key: int | str) -> Namespace:
        """Get a namespace by :attr:`~misc.Namespace.id`,
        :attr:`~misc.Namespace.name` or :attr:`~misc.Namespace.canonical` name.

        Parameters:
            key: The ID, local name, or canonical name of the namespace.

        Returns:
            Namespace handle.
        """
        raise NotImplementedError

    ##### Lists #####

    def recentchanges(
        self, limit: Limit = None, *,
        start: datetime | None = None,
        end: datetime | None = None,
        oldest_first: bool = False,
        namespaces: list[Namespace] | None = None,
        user: User | None = None,
        exclude_user: User | None = None,
        tag: Tag | None = None,
        show: list[Literal['!anon', '!autopatrolled', '!bot', '!minor', '!patrolled', '!redirect', 'anon', 'autopatrolled', 'bot', 'minor', 'patrolled', 'redirect', 'unpatrolled']] | None = None,
        types: list[Literal['categorize', 'edit', 'external', 'log', 'new']] | None = None,
        top_only: bool = False,
        page: Page | None = None,
    ) -> genr.RecentChangeGenerator:
        """Fetch recent changes.

        Parameters:
            start: The timestamp to start enumerating from.
            end: The timestamp to end enumerating.
            oldest_first: If :const:`True`, list oldest first instead of
                newest first.
            namespaces: Only show changes in these namespaces.
            user: Only list changes by this user.
            exclude_user: Don't list changes by this user.
            tag: Only list changes with this tag.
            show: Only show changes that are (not) made by anonymous users
                [(!)anon], (not) autopatrolled [(!)autopatrolled], (not) made
                by a bot [(!)bot], (not) minor edits [(!)minor], patrolled
                [patrolled], not patrolled [!patrolled or unpatrolled], and/or
                (not) changes to redirect pages [(!)redirect].
            types: Only show changes that are page edits [edit], log entries
                [log], categorizations [categorize], page creations [new], or
                external changes [external].
            top_only: Only show most recent edits to pages.
            page: Only show changes to this page.

        Yields:
            If iterated with ``async for``, each recent change.
        """
        raise NotImplementedError

    def recently_changed_pages(
        self, limit: Limit = None, *,
        start: datetime | None = None,
        end: datetime | None = None,
        oldest_first: bool = False,
        namespaces: list[Namespace] | None = None,
        user: User | None = None,
        exclude_user: User | None = None,
        tag: Tag | None = None,
        show: list[Literal['!anon', '!autopatrolled', '!bot', '!minor', '!patrolled', '!redirect', 'anon', 'autopatrolled', 'bot', 'minor', 'patrolled', 'redirect', 'unpatrolled']] | None = None,
        types: list[Literal['categorize', 'edit', 'external', 'log', 'new']] | None = None,
        top_only: bool = False,
    ) -> genr.PageGenerator:
        """Fetch recently changed pages. As it would be pointless to fetch
        recently changed pages and filter to a known page, the ``page``
        parameter is not supported for this method.

        Parameters:
            start: The timestamp to start enumerating from.
            end: The timestamp to end enumerating.
            oldest_first: If :const:`True`, list oldest first instead of
                newest first.
            namespaces: Only show changes in these namespaces.
            user: Only list changes by this user.
            exclude_user: Don't list changes by this user.
            tag: Only list changes with this tag.
            show: Only show changes that are (not) made by anonymous users
                [(!)anon], (not) autopatrolled [(!)autopatrolled], (not) made
                by a bot [(!)bot], (not) minor edits [(!)minor], patrolled
                [patrolled], not patrolled [!patrolled or unpatrolled], and/or
                (not) changes to redirect pages [(!)redirect].
            types: Only show changes that are page edits [edit], log entries
                [log], categorizations [categorize], page creations [new], or
                external changes [external].
            top_only: Only show most recent edits to pages.

        Yields:
            If iterated with ``async for``, each recently changed page.
        """
        raise NotImplementedError

from .page import Page, TalkPage, File, Template, Category
from . import genr
from .user import User, CurrentUser
from .misc import Limit, Namespace, Tag
