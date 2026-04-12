from importlib.metadata import version as _get_version
from .wiki import Wiki
from .excs import APIError, APIWarning
from .page import Page, TalkPage, File, Template, Category, Revision
from .user import User, CurrentUser
from .misc import Namespace, RecentChange, LogEntry, ImageInfo, Tag

__all__ = [
    'Wiki',
    'APIError',
    'APIWarning',
    'Page',
    'TalkPage',
    'File',
    'Template',
    'Category',
    'Revision',
    'User',
    'CurrentUser',
    'Namespace',
    'RecentChange',
    'LogEntry',
    'ImageInfo',
    'Tag',
]

__version__ = _get_version('mw-api-client')
