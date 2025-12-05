from __future__ import annotations

class User:
    """
    Attributes:
        name: The username of the user.
    """
    name: str
    wiki: Wiki

    def __init__(self) -> None:
        """|noinit| Use :meth:`Wiki.user`."""
        raise NotImplementedError

class CurrentUser(User):
    """The currently logged-in user."""

    def __init__(self) -> None:
        """|noinit| Use :attr:`Wiki.me`."""
        raise NotImplementedError

from .wiki import Wiki
