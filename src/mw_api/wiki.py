from __future__ import annotations
from typing import Self

class Wiki:
    """
    A handle on the site itself and the construction point for all objects
    related to it.

    |noinit| For construction, see :meth:`new`.

    Attributes:
        me: The currently logged-in user, or :data:`None` if not logged in
            (not recommended).
    """

    me: CurrentUser | None

    @classmethod
    async def new(cls, api_url: str, user_agent: str) -> Self:
        """
        Parameters:
            api_url: URL to api.php - all requests will go here
            user_agent: User-Agent HTTP header to provide.
                In lieu of a reasonable default, this parameter is required.
        """

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

    def page(self, title: str) -> Page:
        """Get a handle on a wiki page.

        Note: Pages with special functionality like categories and files have
        corresponding subclasses (e.g. :class:`Category`, :class:`File`) whose
        instances may also be returned by this method based on the namespace
        included in the title.

        Parameters:
            title: The full title (Namespace:Title) of the page.

        Returns:
            Instance of :class:`Page` or subclass with the given title.
        """

    def file(self, title: str) -> File:
        r"""Get a handle on a wiki file page.

        Parameters:
            title: The full title (\File:Title) of the page.

        Returns:
            Page handle.

        Raises:
            ValueError: If ``title`` is not the title of a file.
        """

    def template(self, title: str) -> Template:
        """Get a handle on a wiki template page.

        Parameters:
            title: The full title (Template:Title) of the page.

        Returns:
            Page handle.

        Raises:
            ValueError: If ``title`` is not the title of a template.
        """

    def category(self, title: str) -> Category:
        """Get a handle on a wiki category page.

        Parameters:
            title: The full title (Category:Title) of the page.

        Returns:
            Page handle.

        Raises:
            ValueError: If ``title`` is not the title of a category.
        """

    def user(self, name: str) -> User:
        """Get a handle on a wiki user.

        Parameters:
            name: The username of the user.

        Returns:
            User handle.
        """

from .page import Page, File, Template, Category
from .user import User, CurrentUser
