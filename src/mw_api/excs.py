from __future__ import annotations
from typing import TypeVar

class _MetaGetattr(type):
    """Metaclass to provide __getattr__ on a class."""
    def __getattr__(cls: type[T], name: str) -> type[T]:
        if name.startswith('__'):
            raise AttributeError(name=name, obj=cls)
        d = {'__qualname__': f'{cls.__name__}.{name}'}
        setattr(cls, name, type(name, (cls,), d))
        return getattr(cls, name)

class APIError(Exception, metaclass=_MetaGetattr):
    """An error returned by the wiki's API. Raised by async methods."""

    @property
    def code(self):
        """The exception/warning code."""
        return type(self).__name__

class APIWarning(UserWarning, APIError):
    """A warning returned by the wiki's API. Raised by async methods."""

T = TypeVar('T')
