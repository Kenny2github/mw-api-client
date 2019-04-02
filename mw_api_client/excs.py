"""
mw_api_client.excs - Exceptions and exception handling for API
requests.

To catch a permission error:

..code-block:: python

    try:
        page.edit(contents, 'summary')
    except mw.WikiError.protectedpage as exc:
        print('Page is protected:', exc)

To catch an edit conflict, use the following:

..code-block:: python

    try:
        contents = page.read()
        page.edit(contents + 'hi', summary)
    except mw.EditConflict:
        # handling the edit conflict
        # is left as an exercise for the reader

Note that ``EditConflict`` does NOT inherit from WikiError.
"""
from contextlib import contextmanager
from warnings import warn as _warn
from six import with_metaclass

__all__ = [
    'WikiError',
    'EditConflict',
    'WikiWarning',
    'catch'
]

class _MetaGetattr(type):
    """Metaclass to provide __getattr__ on a class."""
    def __getattr__(cls, name):
        setattr(cls, name, type(name, (cls,), {}))
        return getattr(cls, name)

#pylint: disable=too-few-public-methods
class WikiError(with_metaclass(_MetaGetattr, Exception)):
    """An error returned by the wiki's API. Raised by Wiki.request."""
    @property
    def code(self):
        """Return the exception code. Retained for backwards compatibility."""
        return type(self).__name__

class EditConflict(Exception):
    """The last content fetch was before the most recent revision.

    Note: this exception does NOT inherit from WikiError! You must
    use it explicitly:
        try:
            page.edit(contents, summary)
        except (WikiError, EditConflict):
            print('API error or edit conflict')
    """
    pass

@contextmanager
def catch(code=None, caught=None, always=None):
    """Catch a certain error code.
    Note: This function is deprecated and remains only
    for backwards compatibility.

    ``code`` (either a string or an object with a __contains__ method)
    is the error code(s) to catch. If it is a string, it is directly compared.
    Otherwise, it is checked for membership. If it is None, all exceptions
    are caught.
    ``caught`` is a callback for the ``except`` part of try/except/finally. It
    must take a single argument for the exception object.
    ``always`` is a callback for the ``finally`` part of the try/except/finally.
    Use functools.partial for arguments.
    If ``caught`` or ``always`` are None, behavior is to pass.
    """
    _warn('``catch`` is deprecated in favor of normal try...except blocks with'
          ' arbitrary attributes of WikiError. It may be removed in future'
          ' releases.', DeprecationWarning)
    try:
        yield
    except WikiError as exc:
        if (code is not None) and isinstance(code, str):
            if type(exc).__name__ != code:
                raise
        elif code is not None:
            if type(exc).__name__ not in code:
                raise
        if caught is not None:
            caught(exc)
    finally:
        if always is not None:
            always()

class WikiWarning(with_metaclass(_MetaGetattr, UserWarning)):
    """The API sent a warning in the response."""
    pass
