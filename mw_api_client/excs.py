from contextlib import contextmanager
from requests.exceptions import * #import requests exceptions for shorter names

class WikiError(Exception):
    """An arbitrary wiki error. Raised by Wiki.request."""
    def __init__(self, *args, code):
        Exception.__init__(self, *args)
        self.code = code

class EditConflict(Exception):
    """The last content fetch was before the most recent revision.

    Note: do NOT use ``excs.catch`` with this error! It does not inherit
    from WikiError. Use a normal try/except statement instead.
    """
    pass

@contextmanager
def catch(code, caught=lambda: None, always=lambda: None):
    """Catch a certain error code.
    ``code`` (either a string or an object with a __contains__ method)
    is the error code(s) to catch. If it is a string, it is directly compared.
    Otherwise, it is checked for membership.
    ``caught`` is a callback for the ``except`` part of try/except/finally. If
    arguments are needed, use functools.partial.
    ``always`` is a callback for the ``finally`` part of the try/except/finally.
    Again, use functools.partial for arguments.
    ``caught`` and ``always`` default to a function that does nothing.
    """
    try:
        yield
    except WikiError as exc:
        if (exc.code != code
                if isinstance(code, str)
                else exc.code not in code):
            raise
        caught()
    finally:
        always()
