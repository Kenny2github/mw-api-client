from __future__ import annotations
from datetime import datetime
from typing import Literal, LiteralString, Self

class Wiki:
    """
    A handle on the site itself and the construction point for all objects
    related to it.

    |noinit| For construction, see :meth:`new`.

    Attributes:
        me: The currently logged-in/anonymous user.
    """

    me: CurrentUser

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

    def file_cast(self, title: str) -> File:
        """Same as :meth:`file` but adds namespace instead of raising."""
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

    def template_cast(self, title: str) -> Template:
        """Same as :meth:`template` but adds namespace instead of raising."""
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

    def category_cast(self, title: str) -> Category:
        """Same as :meth:`category` but adds namespace instead of raising."""
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
            limit: |see-limit|
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
    ) -> genr.PageGenerator:
        """Fetch recently changed pages. As it would be pointless to fetch
        recently changed pages and filter to a known page, the ``page``
        parameter is not supported for this method. Additionally, as it would
        be pointless to generate the same page multiple times, the ``top_only``
        parameter is forced to :const:`True`.

        Parameters:
            limit: |see-limit|
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

        Yields:
            If iterated with ``async for``, each recently changed page.
        """
        raise NotImplementedError

    def random_pages(
        self, limit: Limit = None, *,
        namespaces: list[Namespace] | None = None,
        redirects: bool | None = False,
        min_size: int | None = None,
        max_size: int | None = None,
        content_model: str | None = None,
    ) -> genr.PageGenerator:
        """Fetch random pages.

        Parameters:
            limit: |see-limit|
            namespaces: Only generate pages in these namespaces.
            redirects: If :const:`True`, only generate random redirects.
                If :const:`False` (the default), only generate random
                non-redirects. Otherwise, generate all pages.
            min_size: Only generate pages of at least this size in bytes.
            max_size: Only generate pages of at most this size in bytes.
            content_model: Only generate pages with this `content model`_.

        Yields:
            If iterated with ``async for``, randomly generated pages.

        .. _content model: https://www.mediawiki.org/wiki/Content_model
        """
        raise NotImplementedError

    def log_events(
        self, limit: Limit = None, *,
        type: LiteralString | None = None,
        action: str | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
        oldest_first: bool = False,
        user: User | None = None,
        page: Page | None = None,
        namespaces: list[Namespace] | None = None,
        prefix: str | None = None,
        tag: Tag | None = None,
    ) -> genr.LogEntryGenerator:
        """Fetch log events.

        Parameters:
            limit: |see-limit|
            type: Filter log entries to only this type. Available types depend
                on the wiki's configuration.
            action: Filter log actions to only this action, overriding ``type``
                if specified. Available actions depend on configuration.
            start: The timestamp to start enumerating from.
            end: The timestamp to end enumerating.
            oldest_first: If :const:`True`, list oldest first instead of
                newest first.
            user: Only list log entries by this user.
            page: Only show log entries targeting this page.
            namespaces: Only show log entries in these namespaces.
            prefix: Filter entries that start with this prefix.
            tag: Only list log entries with this tag.

        Yields:
            If iterated with ``async for``, each log entry.
        """
        raise NotImplementedError

    ##### "All" lists #####

    def all_users(
        self, limit: Limit = None, *,
        from_: str | None = None,
        to: str | None = None,
        prefix: str | None = None,
        descending: bool = False,
        group: list[str] | None = None,
        exclude_group: list[str] | None = None,
        rights: list[str] | None = None,
        edited_only: bool = False,
        active_only: bool = False,
        exclude_named: bool = False,
        exclude_temp: bool = False,
    ) -> genr.UserGenerator:
        """Generate all users on this wiki.

        Parameters:
            limit: |see-limit|
            from_: The string to start enumerating usernames from.
            to: The string to stop enumerating usernames at.
            prefix: Search for all users that begin with this value.
            descending: If :const:`True`, list in descending order instead
                of ascending.
            group: Only include users explicitly given these groups.
            exclude_group: Exclude users explicitly given these groups.
            rights: Only include users explicitly given these rights.
            edited_only: If :const:`True`, only list users who have made edits.
            active_only: If :const:`True`, only list Special:ActiveUsers.
            exclude_named: If :const:`True`, exclude users of named accounts.
            exclude_temp: if :const:`True`, exclude users of temp accounts.

        Yields:
            If iterated with ``async for``, each existing user.
        """
        raise NotImplementedError

from .page import Page, TalkPage, File, Template, Category
from . import genr
from .user import User, CurrentUser
from .misc import Limit, Namespace, Tag
