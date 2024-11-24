from __future__ import annotations

class User:
    """
    Attributes:
        name: The username of the user.
    """
    name: str
    wiki: Wiki

    def __init__(self) -> None:
	    """Not meant to be constructed directly. Use :meth:`Wiki.user`."""

class CurrentUser(User):
    """The currently logged-in user."""

    def __init__(self) -> None:
        """Not meant to be constructed directly. Use :attr:`Wiki.me`."""

from .wiki import Wiki
