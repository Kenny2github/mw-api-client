"""
mw_api_client.excs - Exceptions and exception handling for API
requests.

To catch a permission error:

..code-block:: python

    def denied(exc):
        print('Permission denied:', exc)
    with mw.catch('permissiondenied', denied):
        page.edit(contents, summary)

To catch an edit conflict, however, use the following:

..code-block:: python

    try:
        contents = page.read()
        page.edit(contents + 'hi', summary)
    except mw.EditConflict:
        # handle edit conflict
"""
from contextlib import contextmanager

__all__ = [
    'WikiError',
    'EditConflict',
    'catch'
]

class WikiError(Exception):
    """An arbitrary wiki error. Raised by Wiki.request."""
    def __init__(self, code=None, *args):
        if code is None:
            raise TypeError('``code`` must not be None')
        Exception.__init__(self, *args)
        self.code = code

class EditConflict(Exception):
    """The last content fetch was before the most recent revision.

    Note: do NOT use ``excs.catch`` with this error! It does not inherit
    from WikiError. Use a normal try/except statement instead.
    """
    pass

@contextmanager
def catch(code=None, caught=None, always=None):
    """Catch a certain error code.
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
    try:
        yield
    except WikiError as exc:
        if (code is not None) and (exc.code != code
                                   if isinstance(code, str)
                                   else exc.code not in code):
            raise
        if caught is not None:
            caught(exc)
    finally:
        if always is not None:
            always()
