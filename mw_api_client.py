"""
A really simple MediaWiki API client.

Can:

  * read pages
  * edit pages
  * list pages in category
  * list page backlinks ("what links here")
  * list page transclusions

Requires the `requests` library.

http://www.mediawiki.org/


Example Usage
=============
    import mw_api_client as mwapi

Get a page::

    wiki = mwapi.Wiki("https://en.wikipedia.org/", "wiki/", "w/api.php")

    wiki.login("kenny2wiki", password)

    sandbox = wiki.page("User:Kenny2wiki/sandbox")

Edit page:

    # Get the page
    contents = sandbox.contents

    # Change
    contents += "\n This is a test!"
    summary = "Made a test edit"

    # Submit
    sandbox.edit(contents, summary)

List pages in category::

    for page in wiki.category_members("Redirects"):
        print page.title

Remove all uses of a template::

    target_pages = wiki.page("Template:Stub").transclusions()

    # Sort by title because it's prettier that way
    target_pages.sort(key=lambda x: x.title)

    # Main namespace only
    target_pages = [p for p in target_pages if p.ns == 0]

    for page in target_pages:
        page.replace("{{stub}}", "")


Made by Kenny2github, based off of ~blob8108's Scratch Wiki API client.

MIT Licensed.
"""
from __future__ import print_function
try:
    from urllib.parse import urlencode
except ImportError:
    from urllib import urlencode
import requests

SESH = requests.session()

class WikiError(Exception):
    """An arbitrary wiki error."""
    def __init__(self, error):
        Exception.__init__(self)
        self.info = None
        self.__dict__.update(error)

    def __str__(self):
        return self.info

class PermissionDenied(WikiError):
    """Permission is denied for that action."""
    pass


ERRORS = {
    'permissiondenied': PermissionDenied,
}

class Wiki(object):
    """The base class for a wiki. Contains most API modules as methods."""
    USER_AGENT = "PythonBot Kenny2github~~~~ ~blob8108"

    def __init__(self, url, site_url, api_url):
        """Initialize a wiki with its URLs.

        Additionally create a Meta instance.
        """
        self.wiki_url = url
        self.site_url = self.wiki_url + site_url
        self.api_url = self.wiki_url + api_url
        self.meta = Meta(self)

    def __repr__(self):
        """Represent a Wiki object."""
        return "<Wiki at {addr}>".format(addr=self.wiki_url)

    __str__ = __repr__

    def request(self, _headers=None, _post=False, **params):
        """Inner request method.

        Remains public since it might be used per se.
        """
        params["format"] = "json"

        headers = {
            "User-Agent": self.USER_AGENT,
        }
        headers.update(_headers if _headers is not None else {})

        if _post:
            response = SESH.post(self.api_url, data=params, headers=headers)
        else:
            response = SESH.get(self.api_url, params=params, headers=headers)

        assert response.ok

        if 'error' in response.json():
            error = response.json()['error']
            error_code = error['code']
            if error_code in ERRORS:
                error_cls = ERRORS[error_code]
            else:
                raise WikiError(error)
            raise error_cls(error)

        return response.json()

    def post_request(self, **params):
        """Alias for Wiki.request(_post=True)"""
        return self.request(_post=True, **params)

    def login(self, username, password):
        """Login with a username and password; store cookies."""
        lgtoken = self.meta.tokens('login')
        params = {
            'action': 'login',
            'lgname': username,
            'lgpassword': password,
            'lgtoken': lgtoken
        }
        data = self.post_request(**params)['login']
        return data

    def page(self, title):
        """Return a Page instance based off of the title of the page."""
        if isinstance(title, Page):
            return title
        return Page(self, title=title)

    def allcategories(self, limit="max", prefix=None):
        """Retrieve a generator of all categories represented as Pages."""
        last_cont = {}
        params = {
            'action': 'query',
            'list': 'allcategories',
            'aclimit': limit,
            'acprefix': prefix,
            'acprop': 'size|hidden',
        }
        while 1:
            params.update(last_cont)
            data = self.request(**params)

            for page_data in data['query']['allcategories']:
                yield Page(self, **page_data)

            if 'continue' in data:
                last_cont = data['continue']
            else:
                break

    def alldeletedrevisions(self, limit="max", prefix=None):
        """Retrieve a generator of all deleted Revisions."""
        last_cont = {}
        params = {
            'action': 'query',
            'list': 'alldeletedrevisions',
            'adrlimit': limit,
            'adrprefix': prefix,
            'adrprop': 'ids|flags|timestamp|user|userid|size|sha1|'
                       + 'contentmodel|comment|parsedcomment|content|'
                       + 'tags'
        }
        while 1:
            params.update(last_cont)
            data = self.request(**params)

            for rev_data in data['query']['alldeletedrevisions']:
                yield Revision(self, **rev_data)

            if 'continue' in data:
                last_cont = data['continue']
            else:
                break

    def allfileusages(self, limit="max", prefix=None, unique=False):
        """Retrieve a generator of Pages corresponding to all file usages."""
        last_cont = {}
        params = {
            'action': 'query',
            'list': 'allfileusages',
            'aflimit': limit,
            'afprefix': prefix
        }
        if unique:
            params['afunique'] = 'true'
        else:
            params['afprop'] = 'ids|titles'

        while 1:
            params.update(last_cont)
            data = self.request(**params)

            for page_data in data['query']['allfileusages']:
                yield Page(self, **page_data)

            if 'continue' in data:
                last_cont = data['continue']
            else:
                break

    def allimages(self, limit="max", prefix=None, mime=None):
        """Retrieve a generator of all images represented as Pages."""
        last_cont = {}
        params = {
            'action': 'query',
            'list': 'allimages',
            'ailimit': limit,
            'aiprefix': prefix,
            'aimime': mime,
            'aiprop': 'timestamp|user|userid|comment|parsedcomment|'
                      + 'canonicaltitle|url|size|sha1|mime|mediatype|'
                      + 'metadata|commonmetadata|extmetadata|bitdepth'
        }

        while 1:
            params.update(last_cont)
            data = self.request(**params)

            for page_data in data['query']['allimages']:
                yield Page(self, **page_data)

            if 'continue' in data:
                last_cont = data['continue']
            else:
                break

    def alllinks(self, limit="max", namespace='0', prefix=None, unique=False):
        """Retrieve a generator of all links."""
        last_cont = {}
        params = {
            'action': 'query',
            'list': 'alllinks',
            'allimit': limit,
            'alprefix': prefix,
            'alnamespace': namespace
        }
        if unique:
            params['alunique'] = 'true'
        else:
            params['alprop'] = 'ids|title'

        while 1:
            params.update(last_cont)
            data = self.request(**params)

            for page_data in data['query']['alllinks']:
                yield Page(self, **page_data)

            if 'continue' in data:
                last_cont = data['continue']
            else:
                break

    def allpages(self, limit="max", namespace="0", prefix=None):
        """Retrieve a generator of all Pages.

        NOTE: This may take a long time on very large wikis!
        """
        last_cont = {}
        params = {
            'action': 'query',
            'list': 'allpages',
            'aplimit': limit,
            'apprefix': prefix,
            'apnamespace': namespace,
        }

        while 1:
            params.update(last_cont)
            data = self.request(**params)

            for page_data in data['query']['allpages']:
                yield Page(self, **page_data)

            if 'continue' in data:
                last_cont = data['continue']
            else:
                break

    def allredirects(self, limit="max", prefix=None, unique=False):
        """Retrieve a generator of all Pages that are redirects."""
        last_cont = {}
        params = {
            'action': 'query',
            'list': 'allredirects',
            'arprefix': prefix,
            'arlimit': limit,
        }
        if unique:
            params['arunique'] = 'true'
        else:
            params['arprop'] = 'ids|title|fragment|interwiki'

        while 1:
            params.update(last_cont)
            data = self.request(**params)

            for page_data in data['query']['allredirects']:
                yield Page(self, **page_data)

            if 'continue' in data:
                last_cont = data['continue']
            else:
                break

    def allrevisions(self, limit="max", **kwargs):
        """Retrieve a generator of all revisions."""
        last_cont = {}
        params = {
            'action': 'query',
            'list': 'allrevisions',
            'arvprop': 'ids|flags|timestamp|user|userid|size|sha1|contentmodel|'
                       + 'comment|parsedcomment|tags',
            'arvlimit': limit
        }
        params.update(kwargs)

        while 1:
            params.update(last_cont)
            data = self.request(**params)

            for page in data['query']['allrevisions']:
                for rev_data in page['revisions']:
                    yield Revision(self, Page(self, title=page['title']), **rev_data)

            if 'continue' in data:
                last_cont = data['continue']
            else:
                break

class Page(object):
    """The class for a page on a wiki.

    Must be initialized with a Wiki instance.

    Pages with the "missing" attribute set evaluate to False.
    """
    def __init__(self, wiki, **data):
        """Initialize a page with its wiki and initially don't set a title.

        The Wiki class sets the title automatically, since the Page __init__
        updates its __dict__.
        """
        self.wiki = wiki
        self.title = None
        self.__dict__.update(data)
        self.__dict__.update(self.info())

    def __bool__(self):
        """Return the boolean state of a page."""
        return not hasattr(self, 'missing')

    def __repr__(self):
        """Represent a page instance."""
        return "<Page {name}>".format(name=self.title)

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
        return page_data

    def read(self, length=None):
        """Retrieve the page's content.

        The "length" parameter is there to make the Page object a file-like
        object.
        """
        data = self.wiki.request(**{
            'action': "query",
            'titles': self.title,
            'prop': "revisions",
            'rvprop': "content",
            'rvlimit': "1",
        })
        if length is not None:
            return data["revisions"][0]["*"][:length]
        return data['revisions'][0]['*']

    def edit_token(self):
        """Retrieve an edit token for the page.

        This function is deprecated in favor of
        and is an alias for self.wiki.meta.tokens()
        """
        return self.wiki.meta.tokens()

    def edit(self, content, summary=None):
        """Edit the page with the content content."""
        token = self.wiki.meta.tokens()

        return self.wiki.post_request(**{
            'action': "edit",
            'title': self.title,
            'token': token,
            'text': content.encode("utf-8"),
            'summary': summary,
            'bot': 1,
            'nocreate': 1,
        })

    #note: this is the only place where it differs from a file object.
    #If something writes to it multiple times, it does not append the
    #second write and onwards - it simply rewrites it. This is because
    #there is no read/write head.
    write = edit

    content = property(read, edit) #make content retrievable using a property

    def replace(self, old_text, new_text=''):
        """Replace each occurence of old_text in the page's source with
        new_text.

        Raises ValueError if both old_text and new_text are empty.
        """

        if old_text and new_text:
            summary = "Replace %s with %s" % (old_text, new_text)
        elif old_text:
            summary = "Remove %s" % old_text
        else:
            raise ValueError("old_text and new_text cannot both be empty.")

        content = self.read()
        content = content.replace(old_text, new_text)
        self.edit(content, summary)

    def revisions(self, limit="max", **kwargs):
        """Get a generator of Revisions for this page.

        See https://www.mediawiki.org/wiki/API:Revisions for explanations
        of the various parameters.
        """
        if 'diffto' in kwargs and 'difftotext' in kwargs:
            raise ValueError('Cannot diff to revision ID and text at once.')

        last_cont = {}
        params = {
            'action': 'query',
            'prop': 'revisions',
            'titles': self.title,
            'rvprop': 'ids|flags|timestamp|user|userid|size|sha1|contentmodel|'
                      + 'comment|parsedcomment|tags',
            'rvlimit': limit
        }
        params.update(kwargs)

        while 1:
            params.update(last_cont)
            data = self.wiki.request(**params)

            for rev_data in list(data['query']['pages'].values())[0]['revisions']:
                yield Revision(self.wiki, self, **rev_data)

            if 'continue' in data:
                last_cont = data['continue']
            else:
                break

    @property
    def url(self):
        """Return an approximation of the canonical URL for the page."""
        return self.wiki.site_url + urlencode({"x": self.title})[2:].replace("%2F", "/")

    def backlinks(self, limit="max"):
        """Return a generator of Pages that link to this page."""
        last_cont = {}
        params = {
            'action': "query",
            'list': "backlinks",
            'bllimit': limit,
            'bltitle': self.title
        }
        while 1:
            params.update(last_cont)
            data = self.wiki.request(**params)

            for page_data in data["query"]["backlinks"]:
                yield Page(self.wiki, **page_data)

            if "continue" in data:
                last_cont = data["continue"]
            else:
                break

    def transclusions(self, limit="max"):
        """Return a generator of Pages that transclude this page."""
        last_cont = {}
        params = {
            'action': "query",
            'list': "embeddedin",
            'eilimit': limit,
            'eititle': self.title,
        }
        while 1:
            params.update(last_cont)
            data = self.wiki.request(**params)

            for page_data in data["query"]["embeddedin"]:
                yield Page(self.wiki, **page_data)

            if "continue" in data:
                last_cont = data["continue"]
            else:
                break

    def category_members(self, limit="max"):
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
        while 1:
            params.update(last_cont)
            data = self.wiki.request(**params)

            for page in data["query"]["categorymembers"]:
                yield Page(self.wiki, **page)

            if "continue" in data:
                last_cont = data["continue"]
            else:
                break

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

    def write(self, *dummy):
        """Dummy function to disable writing to content."""
        raise NotImplementedError('Cannot edit a revision of a page.')

    content = property(read)

    def diff(self, revid="prev", difftext=None):
        """Retrieve an HTML diff to another revision (by default previous).

        Cannot diff to a revision ID and text at once.
        """
        if revid is not None and difftext is not None:
            raise ValueError('Cannot diff to revision ID and text at once.')

        params = {
            'action': 'query',
            'prop': 'revisions',
            'revids': self.revid,
            'rvdiffto': revid,
        }
        data = self.wiki.request(**params)

        return list(data['query']['pages'].values())[0]['revisions'][0]['diff']

class Meta(object):
    """A separate class for the API "meta" module."""
    def __init__(self, wiki):
        """Initialize the instance with its wiki."""
        self.wiki = wiki

    def tokens(self, kind="csrf"):
        """Get a token for a database-modifying action.

        The parameter "kind" specifies the type.
        """
        params = {
            'action': 'query',
            'meta': 'tokens',
            'type': kind
        }
        data = self.wiki.request(**params)
        if '|' in kind: #if more than one type of token is being requested
            return data['query']['tokens']
        return data['query']['tokens'][kind+'token']

    def userinfo(self, kind=None):
        """Retrieve info about the currently logged-in user.

        The parameter "kind" specifies what kind of information to retrieve.
        """
        params = {
            'action': 'query',
            'meta': 'userinfo',
            'type': kind,
        }
        data = self.wiki.request(**params)
        return data['query']['userinfo']

    def allmessages(self, messages='*', args=None, prefix=None, **kwargs):
        """Retrieve a list of all interface messages.

        The "messages" parameter specifies what messages to retrieve (default all).

        The "args" parameter specifies a list of arguments to substitute
        into the messages.

        See https://www.mediawiki.org/wiki/API:Allmessages for details about
        other parameters.
        """
        last_cont = {}
        params = {
            'action': 'query',
            'meta': 'allmessages',
            'ammessages': '|'.join(messages) if isinstance(messages, list) else messages,
            'amargs': '|'.join(args) if isinstance(args, list) else args,
            'amprefix': prefix,
        }
        params.update(kwargs)

        while 1:
            params.update(last_cont)
            data = self.wiki.request(**params)

            for page_data in data['query']['allmessages']:
                yield Page(self.wiki, **page_data)

            if 'continue' in data:
                last_cont = data['continue']
            else:
                break

    def filerepoinfo(self, prop=None):
        """Retrieve information about the site's file repositories.

        See https://www.mediawiki.org/wiki/API:Filerepoinfo for information
        about results.
        """
        params = {
            'action': 'query',
            'meta': 'filerepoinfo',
            'friprop': prop,
        }
        data = self.wiki.request(**params)
        return data['query']['repos']

    def siteinfo(self, prop=None, filteriw=None, showalldb=None,
                 numberingroup=None):
        """Retrieve information about the site.

        See https://www.mediawiki.org/wiki/API:Siteinfo for information
        about results.
        """
        params = {
            'action': 'query',
            'meta': 'siteinfo',
            'siprop': prop,
            'sifilteriw': None if prop is None else filteriw,
            'sishowalldb': None if prop is None else showalldb,
            'sinumberingroup': None if prop is None else numberingroup,
        }
        data = self.wiki.request(**params)
        return list(data['query'].values())[0]
