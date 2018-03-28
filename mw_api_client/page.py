"""
This submodule contains the Page and User objects.
"""
from __future__ import print_function
# pylint: disable=too-many-lines
try:
    from urllib.parse import urlencode
except ImportError:
    from urllib import urlencode
import re
from functools import wraps
import time
from .excs import WikiError, EditConflict
from . import GETINFO

__all__ = [
    'Page',
    'User',
    'Revision',
]

class _CachedAttribute(object): # pylint: disable=too-few-public-methods
    '''Computes attribute value and caches it in the instance.
    From the Python Cookbook (Denis Otkidach)
    This decorator allows you to create a property which can be computed once
    and accessed many times. Sort of like memoization.
    '''
    def __init__(self, method, name=None):
        """Initialize the cached attribute."""
        # record the unbound-method and the name
        self.method = method
        self.name = name or method.__name__
        self.__doc__ = method.__doc__
    def __get__(self, inst, cls):
        """Get the cached attribute."""
        # self: <__main__.cache object at 0xb781340c>
        # inst: <__main__.Foo object at 0xb781348c>
        # cls: <class '__main__.Foo'>
        if inst is None:
            # instance attribute accessed on class, return self
            # You get here if you write `Foo.bar`
            return self
        # compute, cache and return the instance's attribute value
        result = self.method(inst)
        # setattr redefines the instance's attribute so this doesn't get called again
        setattr(inst, self.name, result)
        return result

def _mkgen(func):
    """A decorator that creates a generator.

    The order of things to yield is thus:
    1. Static API parameters to use
    2. Class to construct when yielding
    3. Path through returned API data
    4. Dynamic API parameters to use
    5. Positions of positional parameters
    The ``extraself`` parameter specifies whether the page should also
    pass itself to the ``toyield`` constructor.
    """
    gen = func()
    params = gen.__next__()
    toyield = gen.__next__()
    path = gen.__next__()
    dynamparams = gen.__next__()
    positional = gen.__next__()
    extraself = gen.__next__()
    @wraps(func)
    def newfunc(self, *pargs, **kwargs):
        """New function to replace old generator"""
        last_cont = {}
        for key, (val, default) in dynamparams.items():
            if val.startswith('self.'):
                params[key] = getattr(self, val.lstrip('self.'), default)
                if params[key] == Ellipsis: #Ellipsis signals requirement
                    raise AttributeError(repr(val)
                                         + 'is required but does not '
                                         + 'exist!')
            try:
                params[key] = kwargs.get(val, pargs[positional.index(val)])
            except IndexError:
                params[key] = kwargs.get(val, default)
            if val in kwargs:
                del kwargs[val]
        params.update(kwargs)
        for key in params:
            if key.endswith('limit'):
                limitkey = key
                break

        while 1:
            params.update(last_cont)
            data = self.request(**params)
            rootdata = data

            for part in path:
                data = data[part]
            for thing in data:
                if '*' in thing:
                    thing['content'] = thing['*']
                    del thing['*']
                if extraself:
                    yield toyield(self.wiki,
                                  self,
                                  getinfo=kwargs.get('getinfo', None),
                                  **thing)
                else:
                    yield toyield(self.wiki,
                                  getinfo=kwargs.get('getinfo', None),
                                  **thing)
            if params[limitkey] == 'max' \
                   or len(data) < params[limitkey]:
                if 'continue' in rootdata:
                    last_cont = rootdata['continue']
                    last_cont[limitkey] = self.wiki._wraplimit(params)
                else:
                    break
            else:
                break
    return newfunc

class Page(object):
    """The class for a page on a wiki.

    Must be initialized with a Wiki instance.

    Pages with the "missing" attribute set evaluate to False.
    """
    def __init__(self, wiki, getinfo=None, **data):
        """Initialize a page with its wiki and initially don't set a title.

        The Wiki class sets the title automatically, since the Page __init__
        updates its __dict__.

        If `getinfo` is True, request page info for the page.
        If `getinfo` is None, use the module default (defined by GETINFO)
        """
        self.wiki = wiki
        self.title = None
        self.__dict__.update(data)
        if getinfo is None:
            getinfo = GETINFO
        if getinfo:
            self.__dict__.update(self.info())

    def __bool__(self):
        """Return the boolean state of a page. This will simply be whether
        the page exists - i.e., doesn't have the "missing" attribute.
        """
        return not hasattr(self, 'missing')

    def __repr__(self):
        """Represent a page instance."""
        return "<Page {name}>".format(name=self.title)

    def __eq__(self, other):
        """Check if two pages are the same."""
        return self.title == other.title

    def __hash__(self):
        """Page.__hash__() <==> hash(Page)"""
        return hash(self.title)

    __str__ = __repr__

    def info(self):
        """Query information about the page."""
        arguments = {
            'action': "query",
            'titles': self.title,
            'prop': 'info',
            'inprop': 'protection|talkid|watched|watchers|visitingwatchers|'
                      + 'notificationtimestamp|subjectid|url|readable|preload|'
                      + 'displaytitle'
        }
        data = self.wiki.request(**arguments)
        page_data = list(data["query"]["pages"].values())[0]
        if 'title' in page_data:
            del page_data['title'] #don't override the title
        self.__dict__.update(page_data)
        return page_data

    _lasttimestamp = float('inf')

    def read(self):
        """Retrieve the page's content."""
        data = self.wiki.request(**{
            'action': "query",
            'titles': self.title,
            'prop': "revisions",
            'rvprop': "content|timestamp",
            'rvlimit': "1",
        })
        try:
            data = list(data['query']['pages'].values())[0]['revisions'][0]
        except KeyError:
            self.info()
            if hasattr(self, 'missing'):
                raise WikiError('notfound', 'The page does not exist.')
            raise
        self._lasttimestamp = time.mktime(time.strptime(data['timestamp'],
                                                        '%Y-%m-%dT%H:%M:%SZ'))
        return data['*']

    @_CachedAttribute
    def content(self):
        """This property replaces itself when contents are fetched.
        To update this property, use ``read``. Always prefer the ``read``
        method over using the property.
        """
        return self.read()

    def edit_token(self):
        """Retrieve an edit token for the page.

        This function is deprecated in favor of
        and is an alias for self.wiki.meta.tokens()
        """
        return self.wiki.meta.tokens()

    def edit(self, content, summary, erroronconflict=True, **evil):
        """Edit the page with the content content."""

        token = self.wiki.meta.tokens()

        try:
            rev = tuple(self.revisions(limit=1))[0]
            newtimestamp = time.mktime(time.strptime(rev.timestamp,
                                                     '%Y-%m-%dT%H:%M:%SZ'))
            if newtimestamp > self._lasttimestamp and erroronconflict:
                raise EditConflict('The last fetch was before \
    the most recent revision.')
        except KeyError:
            pass #the page doesn't exist, so we're creating it

        params = {
            'action': "edit",
            'title': self.title,
            'token': token,
            'text': content.encode("utf-8"),
            'summary': summary,
            'bot': 1,
        }
        params.update(evil)

        return self.wiki.post_request(**params)

    def delete(self, reason):
        """Delete this page. Note: this is NOT the same thing
        as `del page`! `del` only unsets names, not objects.
        """
        token = self.wiki.meta.tokens()

        if hasattr(self, 'pageid'):
            return self.wiki.post_request(**{
                'action': 'delete',
                'pageid': self.pageid,
                'token': token,
                'reason': reason,
            })
        return self.wiki.post_request(**{
            'action': 'delete',
            'title': self.title,
            'token': token,
            'reason': reason,
        })

    def undelete(self, reason):
        """Undelete this page, assuming it's already deleted :-)"""
        return self.wiki.post_request(**{
            'action': 'undelete',
            'title': self.title,
            'reason': reason,
            'token': self.wiki.meta.tokens()
        })

    def move(self, newtitle, reason=None,
             subpages=None, suppressredirect=None, **evil):
        """Move this page to a new title."""
        token = self.wiki.meta.tokens()

        params = {
            'action': 'move',
            'token': token,
            'reason': reason,
            'to': newtitle,
            'movesubpages': subpages,
            'noredirect': suppressredirect,
        }
        params.update(evil)

        if hasattr(self, 'pageid'):
            params['fromid'] = self.pageid
        else:
            params['from'] = self.title
        self.title = newtitle #duh
        return self.wiki.post_request(**params)

    def protect(self, protections=None, expiry=None, reason=None, cascade=None):
        """Protect this page from editing.

        Format for `protections`:
        A dict, containing action: level pairs, i.e. to restrict editing
        to autoconfirmed users and restrict moving to admins, use:
        {
            'edit': 'autoconfirmed',
            'move': 'systop'
        }

        Format for `expiry`:
        A list, containing expiry timestamps corresponding to each action: level pair.
        Following the previous example, to protect editing for a month
        and moving indefinitely:
        [
            'next month',
            'never'
        ]

        Specify `cascade` to make the protection cascading.
        """
        token = self.wiki.meta.tokens()

        if protections:
            levels = '|'.join((k+'='+v for k, v in protections.items()))
        else:
            levels = None
        if expiry:
            expiries = '|'.join(expiry)
        else:
            expiries = None

        if hasattr(self, 'pageid'):
            return self.wiki.post_request(**{
                'action': 'protect',
                'pageid': self.pageid,
                'token': token,
                'protections': levels,
                'expiry': expiries,
                'reason': reason,
                'cascade': cascade
            })
        return self.wiki.post_request(**{
            'action': 'protect',
            'title': self.title,
            'token': token,
            'protections': levels,
            'expiry': expiries,
            'reason': reason,
            'cascade': cascade
        })

    def replace(self, old_text, new_text='', summary=None):
        """Replace each occurence of old_text in the page's source with
        new_text.

        Raises ValueError if both old_text and new_text are empty.
        """

        if old_text and new_text:
            edit_summary = "Automated edit: Replace {} with {}".format(old_text, new_text)
        elif old_text:
            edit_summary = "Automated edit: Remove {}".format(old_text)
        else:
            raise ValueError("old_text and new_text cannot both be empty.")

        if summary is not None:
            edit_summary = summary

        content = self.read()
        content = content.replace(old_text, new_text)
        self.edit(content, edit_summary)

    def substitute(self, pattern, repl, flags=0, summary=None):
        """Use a regex to substitute each occurence of pattern in the page's
        source with repl.

        Can raise normal re errors.
        """

        if not repl:
            edit_summary = "Automated edit: Removed text"
        else:
            edit_summary = "Automated edit: Replaced text"

        if summary is not None:
            edit_summary = summary

        content = self.read()
        content = re.sub(pattern, repl, content, flags=flags)
        self.edit(content, edit_summary)

    def purge(self):
        """Purge the cache of this page, forcing a re-parse of the contents."""
        return self.wiki.post_request(**{
            'action': 'purge',
            'titles': None if hasattr(self, 'pageid') else self.title,
            'pageids': self.pageid if hasattr(self, 'pageid') else None,
        })

    def rollback(self):
        """Roll back all edits by the last user."""
        user = list(self.revisions(limit=1))[0].user
        params = {
            'action': 'rollback',
            'title': None if hasattr(self, 'pageid') else self.title,
            'pageid': self.pageid if hasattr(self, 'pageid') else None,
            'user': user,
            'token': self.wiki.meta.tokens(kind='rollback'),
            'markbot': True
        }
        return self.wiki.post_request(**params)

    def categoryinfo(self):
        """Get info about this category. Raises an error if this page
        is not a category.
        """
        self.info()
        if self.ns != 14:
            raise ValueError('Page {} is not a category.'.format(self.title))
        params = {
            'action': 'query',
            'prop': 'categoryinfo',
            'titles': self.title,
        }
        data = self.wiki.request(**params)
        data = list(data['query']['pages'].values())[0]
        self.__dict__.update(data)
        return data['categoryinfo']

    @_mkgen
    def revisions(limit="max", **evil):
        """Get a generator of Revisions for this page.

        See https://www.mediawiki.org/wiki/API:Revisions for explanations
        of the various parameters.
        """
        params = {
            'action': 'query',
            'prop': 'revisions',
            'rvprop': 'ids|flags|timestamp|user|userid|size|sha1|contentmodel|'
                      + 'comment|parsedcomment|tags',
        }
        yield params
        yield Revision
        yield ('query', 'pages')
        dynamparams = {
            'titles': ('self.title', Ellipsis), #Ellipsis signals requirement
            'rvlimit': ('limit': limit),
        }
        yield dynamparams
        yield ('limit',)
        yield True

    @_mkgen
    def deletedrevs(limit="max", **evil):
        """Get a generator of deleted Revisions for this page.

        See https://www.mediawiki.org/wiki/API:Deletedrevs for explanations
        of the various paraemeters.
        """
        params = {
            'action': 'query',
            'list': 'deletedrevs',
            'titles': self.title,
            'drprop': 'revid|parentid|user|userid|comment|parsedcomment|minor|'
                      + 'len|sha1|tags',
            'drlimit': limit
        }
        yield params
        yield Revision
        yield ('query', 'deletedrevs')
        dynamparams = {
            'titles': ('self.title', Ellipsis),
            'drlimit': ('limit', limit),
        }
        yield ('limit',)
        yield True

    @property
    def url(self):
        """Return an approximation of the canonical URL for the page."""
        return self.wiki.site_url + urlencode({"x": self.title})[2:].replace("%2F", "/")

    def backlinks(self, limit="max", getinfo=None, **evil):
        """Return a generator of Pages that link to this page."""
        last_cont = {}
        params = {
            'action': "query",
            'list': "backlinks",
            'bllimit': limit,
            'bltitle': self.title
        }
        params.update(evil)

        while 1:
            params.update(last_cont)
            data = self.wiki.request(**params)

            for page_data in data["query"]["backlinks"]:
                if ['*'] in page_data:
                    page_data['content'] = page_data['*']
                    del page_data['*']
                yield Page(self.wiki, getinfo=getinfo, **page_data)

            if limit == 'max' \
                   or len(data['query']['backlinks']) \
                   < params['bllimit']:
                if "continue" in data:
                    last_cont = data["continue"]
                    last_cont['bllimit'] = self.wiki._wraplimit(params)
                else:
                    break
            else:
                break

    linkshere = backlinks #literally what is the difference?

    def redirects(self, limit='max', namespace=None, getinfo=None, **evil):
        """Generate redirects to this Page."""
        last_cont = {}
        params = {
            'action': 'query',
            'titles': self.title,
            'prop': 'redirects',
            'rdlimit': limit,
            'rdnamespace': namespace
        }
        params.update(evil)

        while 1:
            params.update(last_cont)
            data = self.wiki.request(**params)

            for page in list(data['query']['pages'].values())[0]['redirects']:
                if '*' in page:
                    page['content'] = page['*']
                    del page['*']
                yield Page(self.wiki, getinfo=getinfo, **page)

            if limit == 'max' \
                   or len(list(data['query']['pages'].values())[0]['redirects']) \
                   < params['rdlimit']:
                if 'continue' in data:
                    last_cont = data['continue']
                    last_cont['rdlimit'] = self.wiki._wraplimit(params)
                else:
                    break
            else:
                break

    def interwikilinks(self, limit='max', fullurl=False, **evil):
        """Generate all interwiki links used by this page. If fullurl
        is specified, format is (prefix, title, url); otherwise it's
        (prefix, title).
        """
        last_cont = {}
        params = {
            'action': 'query',
            'titles': self.title,
            'prop': 'iwlinks',
            'iwlimit': limit
        }
        if fullurl:
            params['iwprop'] = 'url'
        params.update(evil)

        while 1:
            params.update(last_cont)
            data = self.wiki.request(**params)

            for link in list(data['query']['pages'].values())[0]['iwlinks']:
                if fullurl:
                    yield (link['prefix'], link['*'], link['url'])
                else:
                    yield (link['prefix'], link['*'])

            if limit == 'max' \
                   or len(list(data['query']['pages'].values())[0]['iwlinks']) \
                   < params['iwlimit']:
                if 'continue' in data:
                    last_cont = data['continue']
                    last_cont['iwlimit'] = self.wiki._wraplimit(params)
                else:
                    break
            else:
                break

    iwlinks = interwikilinks

    def languagelinks(self, limit='max', fullurl=False, **evil):
        """Generate all inter-language links used on this page.
        The yield format is (prefix, title, url) if fullurl is specified,
        otherwise it's (prefix, title).
        """
        last_cont = {}
        params = {
            'action': 'query',
            'titles': self.title,
            'prop': 'languagelinks',
            'lllimit': limit
        }
        if fullurl:
            params['llprop'] = 'url'
        params.update(evil)

        while 1:
            params.update(last_cont)
            data = self.wiki.request(**params)

            for link in list(data['query']['pages'].values())[0]['langlinks']:
                if fullurl:
                    yield (link['lang'], link['*'], link['url'])
                else:
                    yield (link['lang'], link['*'])

            if limit == 'max' \
                   or len(list(data['query']['pages'].values())[0]['langlinks']) \
                   < params['lllimit']:
                if 'continue' in data:
                    last_cont = data['continue']
                    last_cont['lllimit'] = self.wiki._wraplimit(params)
                else:
                    break
            else:
                break

    langlinks = languagelinks

    def links(self, limit='max', namespace=None, getinfo=None, **evil):
        """Generate Pages that this Page links to."""
        last_cont = {}
        params = {
            'action': 'query',
            'titles': self.title,
            'prop': 'links',
            'plnamespace': namespace,
            'pllimit': limit
        }
        params.update(evil)

        while 1:
            params.update(last_cont)
            data = self.wiki.request(**params)

            for page in list(data['query']['pages'].values())[0]['links']:
                if '*' in page:
                    page['content'] = page['*']
                    del page['*']
                yield Page(self.wiki, getinfo=getinfo, **page)

            if limit == 'max' \
               or len(list(data['query']['pages'].values())[0]['links']) \
               < params['pllimit']:
                if 'continue' in data:
                    last_cont = data['continue']
                    last_cont['pllimit'] = self.wiki._wraplimit(params)
                else:
                    break
            else:
                break

    def extlinks(self, limit='max', protocol=None, query=None, **evil):
        """Generate all external links this Page uses. Yield format is
        simply the URL.
        """
        last_cont = {}
        params = {
            'action': 'query',
            'titles': self.title,
            'prop': 'extlinks',
            'ellimit': limit,
            'elprotocol': protocol,
            'elquery': query,
            'elexpandurl': True
        }
        params.update(evil)

        while 1:
            params.update(last_cont)
            data = self.wiki.request(**params)

            for link in list(data['query']['pages'].values())[0]['extlinks']:
                yield link['*']

            if limit == 'max' \
                   or len(list(data['query']['pages'].values())[0]['extlinks']) \
                   < params['ellimit']:
                if 'continue' in data:
                    last_cont = data['continue']
                    last_cont['ellimit'] = self.wiki._wraplimit(params)
                else:
                    break
            else:
                break

    def transclusions(self, limit="max", namespace=None, getinfo=None, **evil):
        """Return a generator of Pages that transclude this page."""
        last_cont = {}
        params = {
            'action': "query",
            'list': "embeddedin",
            'eilimit': limit,
            'eititle': self.title,
            'einamespace': namespace,
        }
        params.update(evil)

        while 1:
            params.update(last_cont)
            data = self.wiki.request(**params)

            for page_data in data["query"]["embeddedin"]:
                if '*' in page_data:
                    page_data['content'] = page_data['*']
                    del page_data['*']
                yield Page(self.wiki, getinfo=getinfo, **page_data)

            if limit == 'max' \
                   or len(data['query']['embeddedin']) \
                   < params['eilimit']:
                if "continue" in data:
                    last_cont = data["continue"]
                    last_cont['eilimit'] = self.wiki._wraplimit(params)
                else:
                    break
            else:
                break

    embeddedin = transcludedin = transclusions #WHAT is the DIFFERENCE?

    def templates(self, limit='max', namespace=None, getinfo=None, **evil):
        """Generate Pages that this Page transcludes."""
        last_cont = {}
        params = {
            'action': 'query',
            'titles': self.title,
            'prop': 'templates',
            'tlnamespace': namespace,
            'tllimit': limit,
        }
        params.update(evil)

        while 1:
            params.update(last_cont)
            data = self.wiki.request(**params)

            for page in list(data['query']['pages'].values())[0]['templates']:
                if '*' in page:
                    page['content'] = page['*']
                    del page['*']
                yield Page(self.wiki, getinfo=getinfo, **page)

            if limit == 'max' \
                   or len(list(data['query']['pages'].values())[0]['templates']) \
                   < params['tllimit']:
                if 'continue' in data:
                    last_cont = data['continue']
                    last_cont['tllimit'] = self.wiki._wraplimit(params)
                else:
                    break
            else:
                break

    def categorymembers(self, limit="max", getinfo=None, **evil):
        """Return a generator of Pages in this category."""
        if not self.title.startswith("Category:"):
            raise ValueError('Page is not a category.')

        last_cont = {}
        params = {
            'action': 'query',
            'list': 'categorymembers',
            'cmtitle': self.title,
            'cmlimit': limit,
        }
        params.update(evil)

        while 1:
            params.update(last_cont)
            data = self.wiki.request(**params)

            for page in data["query"]["categorymembers"]:
                if '*' in page:
                    page['content'] = page['*']
                    del page['*']
                yield Page(self.wiki, getinfo=getinfo, **page)

            if limit == 'max' \
                   or len(data['query']['categorymembers']) \
                   < params['cmlimit']:
                if "continue" in data:
                    last_cont = data["continue"]
                    last_cont['cmlimit'] = self.wiki._wraplimit(params)
                else:
                    break
            else:
                break

    def imageusage(self, limit="max", namespace=None, getinfo=None, **evil):
        """Return a generator of Pages that link to this image."""
        if not self.title.startswith("File:"):
            raise ValueError('Page is not a file')

        last_cont = {}
        params = {
            'action': 'query',
            'list': 'imageusage',
            'iutitle': self.title,
            'iunamespace': namespace,
            'iulimit': limit
        }
        params.update(evil)

        while 1:
            params.update(last_cont)
            data = self.wiki.request(**params)

            for page in data['query']['imageusage']:
                if '*' in page:
                    page['content'] = page['*']
                    del page['*']
                yield Page(self.wiki, getinfo=getinfo, **page)

            if limit == 'max' \
                   or len(data['query']['imageusage']) \
                   < params['iulimit']:
                if 'continue' in data:
                    last_cont = data['continue']
                    last_cont['iulimit'] = self.wiki._wraplimit(params)
                else:
                    break
            else:
                break

    def fileusage(self, limit='max', namespace=None, getinfo=None, **evil):
        """Generate Pages that link to this File. TODO: figure out what
        the difference between this and imageusage is.
        """
        if not self.title.startswith('File:'):
            raise ValueError('Page is not a file')

        last_cont = {}
        params = {
            'action': 'query',
            'titles': self.title,
            'prop': 'fileusage',
            'fuprop': 'pageid|title|redirect',
            'funamespace': namespace,
            'fulimit': limit,
        }
        params.update(evil)

        while 1:
            params.update(last_cont)
            data = self.wiki.request(**params)

            for page in list(data['query']['pages'].values())[0]['fileusage']:
                if '*' in page:
                    page['content'] = page['*']
                    del page['*']
                yield Page(self.wiki, getinfo=getinfo, **page)

            if limit == 'max' \
                   or len(list(data['query']['pages'].values())[0]['fileusage']) \
                   < params['fulimit']:
                if 'continue' in data:
                    last_cont = data['continue']
                    last_cont['fulimit'] = self.wiki._wraplimit(params)
                else:
                    break
            else:
                break

    def images(self, limit='max', getinfo=None, **evil):
        """Generate Pages based on what images this Page uses."""
        last_cont = {}
        params = {
            'action': 'query',
            'titles': self.title,
            'prop': 'images',
            'imlimit': limit
        }
        params.update(evil)

        while 1:
            params.update(last_cont)
            data = self.wiki.request(**params)

            for page in list(data['query']['pages'].values())[0]['images']:
                if '*' in page:
                    page['content'] = page['*']
                    del page['*']
                yield Page(self.wiki, getinfo=getinfo, **page)

            if limit == 'max' \
                   or len(list(data['query']['pages'].values())[0]['images']) \
                   < params['imlimit']:
                if 'continue' in data:
                    last_cont = data['continue']
                    last_cont['imlimit'] = self.wiki._wraplimit(params)
                else:
                    break
            else:
                break

    def duplicatefiles(self, limit='max', getinfo=None, **evil):
        """Generate duplicates of this file."""
        if not self.title.startswith("File:"):
            raise ValueError('Page is not a file')

        last_cont = {}
        params = {
            'action': 'query',
            'prop': 'duplicatefiles',
            'titles': self.title,
            'dflimit': limit
        }
        params.update(evil)

        while 1:
            params.update(last_cont)
            data = self.wiki.request(**params)

            for page in list(data['query']['pages'].values())[0]['duplicatefiles']:
                if '*' in page:
                    page['content'] = page['*']
                    del page['*']
                yield Page(self.wiki, getinfo=getinfo, title=page['name'])

            if limit == 'max' \
                   or len(list(data['query']['pages'].values())[0]['duplicatefiles']) \
                   < params['dflimit']:
                if 'continue' in data:
                    last_cont = data['continue']
                    last_cont['dflimit'] = self.wiki._wraplimit(params)
                else:
                    break
            else:
                break

    def pagepropnames(self):
        """Retrieve a generator of property names for this page."""
        params = {
            'action': 'query',
            'list': 'pagepropnames',
            'titles': self.title,
            'ppnlimit': 'max',
        }
        data = self.wiki.request(**params)

        for prop in data['query']['pagepropnames']:
            yield prop['propname']

    def pageprops(self):
        """Return a dictionary of page properties for this page."""
        params = {
            'action': 'query',
            'titles': self.title,
            'prop': 'pageprops',
        }
        return list(self.wiki.request(**params)['query']['pages']
                    .values())[0]['pageprops']

    def categories(self, limit='max', getinfo=None, **evil):
        """Get a generator of all categories used on this page."""
        last_cont = {}
        params = {
            'action': 'query',
            'titles': self.title,
            'prop': 'categories',
            'clprop': 'sortkey|timestamp|hidden',
            'cllimit': limit
        }
        params.update(evil)

        while 1:
            params.update(last_cont)
            data = self.wiki.request(**params)

            for page in list(data['query']['pages'].values())[0]['categories']:
                if '*' in page:
                    page['content'] = page['*']
                    del page['*']
                yield Page(self.wiki, getinfo=getinfo, **page)

            if limit == 'max' \
                   or len(list(data['query']['pages'].values())[0]['categories']) \
                   < params['cllimit']:
                if 'continue' in data:
                    last_cont = data['continue']
                    last_cont['cllimit'] = self.wiki._wraplimit(params)
                else:
                    break
            else:
                break

    def contributors(self, limit='max', getinfo=None, **evil):
        """Get a generator of contributors to this page."""
        last_cont = {}
        params = {
            'action': 'query',
            'titles': self.title,
            'prop': 'contributors',
            'pclimit': limit
        }
        params.update(evil)

        while 1:
            params.update(last_cont)
            data = self.wiki.request(**params)

            for usr in list(data['query']['pages'].values())[0]['contributors']:
                yield User(self.wiki, getinfo=getinfo, **usr)

            if limit == 'max' \
                   or len(list(data['query']['pages'].values())[0]['contributors']) \
                   < params['pclimit']:
                if 'continue' in data:
                    last_cont = data['continue']
                    last_cont['pclimit'] = self.wiki._wraplimit(params)
                else:
                    break
            else:
                break

class User(object):
    """A user on a wiki."""
    def __init__(self, wiki, currentuser=False, getinfo=None, **userinfo):
        """Initialize the instance with its wiki and update its info."""
        self.wiki = wiki
        self.name = None
        self.currentuser = currentuser
        self.__dict__.update(userinfo)
        if getinfo is None:
            getinfo = GETINFO
        if getinfo:
            data = self.wiki.users(self.name, justdata=True)
            self.__dict__.update(tuple(data)[0])
            if currentuser:
                self.__dict__.update(self.wiki.meta.userinfo())

    def __repr__(self):
        """Represent a User."""
        if self.currentuser:
            return '<Current User {un}>'.format(un=self.name)
        return '<User {un}>'.format(un=self.name)

    __str__ = __repr__

    def __eq__(self, other):
        """Check if two users are the same."""
        return self.name == other.name

    def __hash__(self):
        """User.__hash__() <==> hash(User)"""
        return hash(self.name)

    def __bool__(self):
        """Returns the value of self.currentuser."""
        return bool(self.currentuser)

    def block(self, reason, expiry=None, **evil):
        """Block this user.

        See https://www.mediawiki.org/wiki/API:Block for details about kwargs.
        """
        token = self.wiki.meta.tokens()

        params = {
            'action': 'block',
            'user': self.name,
            'token': token,
            'reason': reason,
            'expiry': expiry
        }
        params.update(evil)

        return self.wiki.post_request(**params)

    def rights(self, add, remove, reason=None, **evil):
        """Change user rights for this user.

        `add` and `rem` can both be either a pipe-separated string
        of group names, or an iterable of group names.
        """
        token = self.wiki.meta.tokens(kind='userrights')

        params = {
            'action': 'userrights',
            'reason': reason,
            'token': token
        }
        if hasattr(self, 'userid'):
            params['userid'] = self.userid
        else:
            params['user'] = self.name
        if isinstance(add, str):
            params['add'] = add
        else:
            params['add'] = '|'.join(add)
        if isinstance(remove, str):
            params['remove'] = remove
        else:
            params['remove'] = '|'.join(remove)
        params.update(evil)

        return self.wiki.post_request(**params)

    def contribs(self, limit='max', namespace=None, **evil):
        """Get contributions from this user."""
        last_cont = {}
        params = {
            'action': 'query',
            'list': 'usercontribs',
            'uclimit': limit,
            'ucnamespace': namespace,
            'ucuserids': self.userid if hasattr(self, 'userid') else None,
            'ucuser': self.name if not hasattr(self, 'userid') else None,
            'ucprop': 'ids|title|timestamp|comment|parsedcomment|size|sizediff|\
flags|tags',
        }
        params.update(evil)

        while 1:
            params.update(last_cont)
            data = self.wiki.request(**params)

            for rev in data['query']['usercontribs']:
                if '*' in rev:
                    rev['content'] = rev['*']
                    del rev['*']
                yield Revision(self.wiki, self.wiki.page(rev['title']), **rev)

            if limit == 'max' \
                   or len(data['query']['usercontribs']) \
                   < params['uclimit']:
                if 'continue' in data:
                    last_cont = data['continue']
                    last_cont['uclimit'] = self.wiki._wraplimit(params)
                else:
                    break
            else:
                break

    def clearhasmsg(self):
        """Clear the "new message" notification. Must be current user."""
        assert self.currentuser
        self.wiki.request(_format='none',
                          **{'action': 'clearhasmsg'})

    def emailuser(self, target, body, subject=None, ccme=None):
        """Email another user. Must be current user."""
        assert self.currentuser
        token = self.wiki.meta.tokens()
        return self.wiki.post_request(**{
            'action': 'emailuser',
            'target': target.name if isinstance(target, User) else target,
            'subject': subject,
            'text': body,
            'ccme': ccme,
            'token': token
        })['emailuser']['result']

    def resetpassword(self, capture=False):
        """Reset this User's password. If `capture` is truthy, return the
        temporary password that was sent instead of the reset status (requires
        the `passwordreset` right).
        """
        token = self.wiki.meta.tokens()
        params = {
            'action': 'resetpassword',
            'user': self.name,
            'token': token
        }
        if capture:
            params['capture'] = True
        data = self.post_request(**params)
        if capture:
            return data['resetpassword']['passwords'][self.name]
        return data['resetpassword']['status']

class Revision(object):
    """The class for a revision of a page.

    Must be initialized with a Wiki and Page instance.
    """
    def __init__(self, wiki, page, **data):
        """Initialize a revision with its wiki and page.

        Initially does not set a revision ID, since the Page/Wiki classes
        pass that in data, which updates the __dict__.
        """
        self.wiki = wiki
        if not isinstance(page, Page):
            self.page = Page(self.wiki, title=page)
        else:
            self.page = page
        self.revid = None
        self.__dict__.update(data)

    def __repr__(self):
        """Represent a revision of a page."""
        return "<Revision {revid} of page {name}>".format(revid=self.revid, name=self.page.title)

    __str__ = __repr__

    def __eq__(self, other):
        """Check if two revisions are the same."""
        return self.revid == other.revid

    def __hash__(self):
        """Revision.__hash__() <==> hash(Revision)"""
        return hash(self.revid)

    def read(self):
        """Retrieve the content of this revision."""
        params = {
            'action': 'query',
            'prop': 'revisions',
            'revids': self.revid,
            'rvprop': 'content',
            'rvlimit': '1',
        }
        data = self.wiki.request(**params)

        return list(data['query']['pages'].values())[0]['revisions'][0]['*']

    @_CachedAttribute
    def content(self):
        """The content of this revision.
        This should normally be set when a request instantiating a Revision
        includes the content.
        """
        return self.read()

    @staticmethod
    def edit(*_, **__):
        """Dummy function to disable writing to content."""
        raise NotImplementedError('Cannot edit a revision of a page.')

    def diff(self, revid="prev", difftext=None):
        """Retrieve an HTML diff to another revision (by default previous).

        It is not possible to diff to a revision ID and text at once - if
        difftext is specified, it is assumed over revid.
        """

        params = {
            'action': 'query',
            'prop': 'revisions',
            'revids': self.revid,
        }
        if difftext is not None:
            params['rvdifftotext'] = difftext
        else:
            params['rvdiffto'] = revid

        data = self.wiki.request(**params)

        return list(data['query']['pages'].values())[0]['revisions'][0]['diff']

    def patrol(self):
        """Patrol this revision."""
        token = self.wiki.meta.tokens(kind='patrol')
        return self.wiki.post_request(**{
            'action': 'patrol',
            'revid': self.revid,
            'token': token
        })

    def purge(self):
        """Purge the cache of this revision, forcing a re-parse of the text."""
        return self.wiki.post_request(**{
            'action': 'purge',
            'revids': self.revid,
        })

    def delete(self, contentshown=None, commentshown=None, usershown=None):
        """Delete this revision.
        Set `contentshown`, `commentshown`, and `usershown` to True to
        unhide the content, comment, and user of this revision respectively.
        Set them to False to hide them.
        Set them to None to leave them unchanged."""
        params = {
            'action': 'revisiondelete',
            'type': 'revision',
            'target': self.page.title,
            'ids': self.revid,
            'token': self.wiki.meta.tokens()
        }
        show, hide = [], []
        if contentshown is True:
            show.append('content')
        elif contentshown is False:
            hide.append('content')
        if commentshown is True:
            show.append('comment')
        elif commentshown is False:
            hide.append('comment')
        if usershown is True:
            show.append('user')
        elif usershown is False:
            hide.append('user')
        params['show'] = '|'.join(show)
        params['hide'] = '|'.join(hide)
        return self.post_request(**params)['revisiondelete']['status']
