from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .wiki import Wiki
    from .page import Page, TalkPage

class User:
    """
    A handle on a wiki user, uniquely identified by their :attr:`name`. There
    is only one :class:`User` instance per :class:`~wiki.Wiki` per
    MediaWiki-normalized username.

    The :attr:`name` |key-attr| |population| :meth:`update_info`.

    Attributes:
        name: The username of the user.
    """
    name: str
    wiki: Wiki

    def __init__(self) -> None:
        """|noinit| Use :meth:`Wiki.user`."""
        raise NotImplementedError

    async def update_info(self) -> None:
        """Fetch all available metadata about the user and cache it, updating
        the cache if previously fetched.

        If the user exists, after calling this method every :class:`property`
        of this instance should return data instead of raising :exc:`KeyError`.

        If the user does not exist, this method is of limited use beyond
        checking whether they exist yet or whether the username is registrable.
        """
        raise NotImplementedError

    @property
    def page(self) -> Page:
        """The user's userpage."""
        raise NotImplementedError

    @property
    def talk(self) -> TalkPage:
        """The user's talk page."""
        raise NotImplementedError

class CurrentUser(User):
    """The currently logged-in user."""

    def __init__(self) -> None:
        """|noinit| Use :attr:`Wiki.me`."""
        raise NotImplementedError
