"""
A really simple MediaWiki API client.

Can use all MediaWiki API modules as of 23/11/2017

Requires the ``requests`` library.

http://www.mediawiki.org/


Example Usage
=============
    import mw_api_client as mwapi

Get a page:

    wiki = mwapi.Wiki("https://en.wikipedia.org/w/api.php")

    wiki.login("kenny2wiki", password)

    sandbox = wiki.page("User:Kenny2wiki/sandbox")

Edit page:

    # Get the page
    contents = sandbox.read()

    # Change
    contents += "\n This is a test!"
    summary = "Made a test edit"

    # Submit
    sandbox.edit(contents, summary)

List pages in category:

    for page in wiki.page("Category:Redirects").categorymembers():
        print page.title

Remove all uses of a template:

    target_pages = list(wiki.page("Template:Stub").transclusions())

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
import re
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

class MustBePosted(WikiError):
    """You must POST some of the parameters in the request."""
    pass


ERRORS = {
    'permissiondenied': PermissionDenied,
    'mustbeposted': MustBePosted,
    'mustpostparams': MustBePosted,
}

class Wiki(object):
    """The base class for a wiki. Contains most API modules as methods."""

    def __init__(self, api_url, user_agent=None):
        """Initialize a wiki with its URLs.

        Additionally create a Meta instance.

        If user_agent is specified, all requests will use that user agent.
        Otherwise, a generic user agent is used.
        """
        self.api_url = api_url
        if user_agent is not None:
            self.USER_AGENT = user_agent
        else:
            self.USER_AGENT = "Python MediaWiki API Client, by Kenny2github, \
based off of blob8108's original."
        self.meta = Meta(self)
        data = self.meta.siteinfo()
        self.wiki_url = data['server']
        self.site_url = data['server'] + data['articlepath'].replace('$1', '')

    def __repr__(self):
        """Represent a Wiki object."""
        return "<Wiki at {addr}>".format(addr=self.wiki_url)

    __str__ = __repr__

    @staticmethod
    def _wraplimit(limit, wrap=500):
        if isinstance(limit, str):
            if limit == 'max':
                return limit
            else:
                limit = int(limit) - wrap
                if limit < 1:
                    limit = 1
                return limit
        elif isinstance(limit, int):
            limit -= wrap
            if limit < 1:
                return limit
        else:
            raise TypeError('"limit" must be str or int, not ' + type(limit).__name__)

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

        print(response.text)
        data = response.json()

        if 'error' in data:
            error = data['error']
            error_code = error['code']
            error_cls = ERRORS.get(error_code, WikiError)
            raise error_cls(error)

        return data

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

    def allcategories(self, limit="max", prefix=None, getinfo=True):
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
                yield Page(self, getinfo=getinfo **page_data)

            if 'continue' in data:
                last_cont = data['continue']
                last_cont['aclimit'] = self._wraplimit(params['aclimit'])
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
                last_cont['adrlimit'] = self._wraplimit(params['adrlimit'])
            else:
                break

    def allfileusages(self, limit="max", prefix=None,
                      unique=False, getinfo=True):
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
                yield Page(self, getinfo=getinfo, **page_data)

            if 'continue' in data:
                last_cont = data['continue']
                last_cont['aflimit'] = self._wraplimit(params['aflimit'])
            else:
                break

    def allimages(self, limit="max", prefix=None, mime=None, getinfo=True):
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
                yield Page(self, getinfo=getinfo, **page_data)

            if 'continue' in data:
                last_cont = data['continue']
                last_cont['ailimit'] = self._wraplimit(params['ailimit'])
            else:
                break

    def alllinks(self, limit="max", namespace='0',
                 prefix=None, getinfo=True):
        """Retrieve a generator of all links."""
        last_cont = {}
        params = {
            'action': 'query',
            'list': 'alllinks',
            'allimit': limit,
            'alprefix': prefix,
            'alnamespace': namespace,
            'alprop': 'ids|title',
        }

        while 1:
            params.update(last_cont)
            data = self.request(**params)

            for page_data in data['query']['alllinks']:
                yield Page(self, getinfo=getinfo, **page_data)

            if 'continue' in data:
                last_cont = data['continue']
                last_cont['allimit'] = self._wraplimit(params['allimit'])
            else:
                break

    def allpages(self, limit="max", namespace="0", prefix=None, getinfo=True):
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
                yield Page(self, getinfo=getinfo, **page_data)

            if 'continue' in data:
                last_cont = data['continue']
                last_cont['aplimit'] = self._wraplimit(params['aplimit'])
            else:
                break

    def allredirects(self, limit="max", prefix=None,
                     unique=False, getinfo=True):
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
                yield Page(self, getinfo=getinfo, **page_data)

            if 'continue' in data:
                last_cont = data['continue']
                last_cont['arlimit'] = self._wraplimit(params['arlimit'])
            else:
                break

    def allrevisions(self, limit="max", getinfo=True, **kwargs):
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
                    yield Revision(self, Page(self, getinfo=getinfo, **page),
                                   **rev_data)

            if 'continue' in data:
                last_cont = data['continue']
                last_cont['arvlimit'] = self._wraplimit(params['arvlimit'])
            else:
                break

    def alltransclusions(self, limit="max", prefix=None,
                         unique=False, getinfo=True):
        """Retrieve a generator of all transclusions."""
        last_cont = {}
        params = {
            'action': 'query',
            'list': 'alltransclusions',
            'atprefix': prefix,
            'atlimit': limit,
        }
        if unique:
            params['atunique'] = 'true'
        else:
            params['atprop'] = 'title|ids'

        while 1:
            params.update(last_cont)
            data = self.request(**params)

            for page_data in data['query']['alltransclusions']:
                yield Page(self, getinfo=getinfo, **page_data)

            if 'continue' in data:
                last_cont = data['continue']
                last_cont['atlimit'] = self._wraplimit(params['atlimit'])
            else:
                break

    def allusers(self, limit="max", prefix=None, **kwargs):
        """Retrieve a generator of all users, each item being a dict."""
        last_cont = {}
        params = {
            'action': 'query',
            'list': 'allusers',
            'auprefix': prefix,
            'aulimit': limit,
            'auprop': 'blockinfo|groups|implicitgroups|rights|editcount'
                      + '|registration'
        }
        params.update(kwargs)

        while 1:
            params.update(last_cont)
            data = self.request(**params)

            for user_data in data['query']['allusers']:
                yield user_data

            if 'continue' in data:
                last_cont = data['continue']
                last_cont['aulimit'] = self._wraplimit(params['aulimit'])
            else:
                break

    def blocks(self, limit="max", blockip=None, users=None):
        """Retrieve a generator of currently active blocks, each item being
        a dict.
        """
        if blockip is not None and users is not None:
            raise ValueError("Cannot specify IP and username together!")

        last_cont = {}
        params = {
            'action': 'query',
            'list': 'blocks',
            'bkip': blockip,
            'bkusers': users,
            'bklimit': limit,
            'bkprop': 'id|user|userid|by|byid|timestamp|expiry|reason|range|'
                      + 'flags'
        }

        while 1:
            params.update(last_cont)
            data = self.request(**params)

            for block_data in data['query']['blocks']:
                yield block_data

            if 'continue' in data:
                last_cont = data['continue']
                last_cont['bklimit'] = self._wraplimit(params['bklimit'])
            else:
                break

    def deletedrevs(self, limit="max", user=None, namespace=None, getinfo=True):
        """Retrieve a generator of all deleted Revisions.

        This can be deleted user contributions (specify "user") or
        deleted revisions in a certain namespace (specify "namespace")
        or both.
        """
        last_cont = {}
        params = {
            'action': 'query',
            'list': 'deletedrevs',
            'druser': user,
            'drnamespace': namespace,
            'drprop': 'revid|parentid|'
                      + '' if user is not None else 'user|userid'
                      + 'comment|parsedcomment|minor|len|sha1|tags',
            'drlimit': limit
        }

        while 1:
            params.update(last_cont)
            data = self.request(**params)

            for page in data['query']['deletedrevs']:
                for rev_data in page['revisions']:
                    yield Revision(self,
                                   Page(self, getinfo=getinfo, **page),
                                   **rev_data)

            if 'continue' in data:
                last_cont = data['continue']
                last_cont['drlimit'] = self._wraplimit(params['drlimit'])
            else:
                break

    def exturlusage(self, limit="max", url=None, protocol=None,
                    getinfo=True, **kwargs):
        """Retrieve a generator of Pages that link to a particular URL or
        protocol, or simply external links in general.

        These pages will have an extra attribute, `url`, that shows what
        URL they link to externally.
        """
        last_cont = {}
        params = {
            'action': 'query',
            'list': 'exturlusage',
            'euquery': url,
            'euprotocol': protocol,
            'eulimit': limit
        }
        params.update(kwargs)

        while 1:
            params.update(last_cont)
            data = self.request(**params)

            for page in data['query']['exturlusage']:
                yield Page(self, getinfo=getinfo, **page)

            if 'continue' in data:
                last_cont = data['continue']
                last_cont['eulimit'] = self._wraplimit(params['eulimit'])
            else:
                break

    def filearchive(self, limit="max", prefix=None, getinfo=True):
        """Retrieve a generator of deleted files, represented as Pages."""
        last_cont = {}
        params = {
            'action': 'query',
            'list': 'filearchive',
            'faprop': 'sha1|timestamp|user|size|description|parseddescription|'
                      + 'mime|mediatype|metadata|bitdepth|archivename',
            'falimit': limit,
            'faprefix': prefix
        }

        while 1:
            params.update(last_cont)
            data = self.request(**params)

            for page in data['query']['filearchive']:
                yield Page(self, getinfo=getinfo, **page)

            if 'continue' in data:
                last_cont = data['continue']
                last_cont['falimit'] = self._wraplimit(params['falimit'])
            else:
                break

    def interwikibacklinks(self, iwprefix, iwtitle=None,
                           limit="max", getinfo=True):
        """Retrieve a generator of Pages that link to a particular
        interwiki prefix (and title, if specified)
        """
        last_cont = {}
        params = {
            'action': 'query',
            'list': 'iwbacklinks',
            'iwblprefix': iwprefix,
            'iwbltitle': iwtitle,
            'iwbllimit': limit,
            'iwblprop': 'iwprefix|iwtitle'
        }

        while 1:
            params.update(last_cont)
            data = self.request(**params)

            for page in data['query']['iwbacklinks']:
                yield Page(self, getinfo=getinfo, **page)

            if 'continue' in data:
                last_cont = data['continue']
                last_cont['iwblimit'] = self._wraplimit(params['iwblimit'])
            else:
                break

    def languagebacklinks(self, langprefix, langtitle=None,
                          limit="max", getinfo=True):
        """Retrieve a generator of Pages that link to a particular language
        code (and title, if specified)
        """
        last_cont = {}
        params = {
            'action': 'query',
            'list': 'langbacklinks',
            'lbllang': langprefix,
            'lbltitle': langtitle,
            'lbllimit': limit,
            'lblprop': 'lllang|lltitle'
        }

        while 1:
            params.update(last_cont)
            data = self.request(**params)

            for page in data['query']['langbacklinks']:
                yield Page(self, getinfo=getinfo, **page)

            if 'continue' in data:
                last_cont = data['continue']
                last_cont['lbllimit'] = self._wraplimit(params['lbllimit'])
            else:
                break

    def logevents(self, limit="max", title=None, user=None):
        """Retrieve a generator of log events, each event being a dict.

        For more information on results, see:
        https://www.mediawiki.org/wiki/API:Logevents
        """
        last_cont = {}
        params = {
            'action': 'query',
            'list': 'logevents',
            'leprop': 'ids|title|type|user|userid|timestamp|comment|'
                      + 'parsedcomment|details|tags',
            'leuser': user,
            'letitle': title,
            'lelimit': limit
        }

        while 1:
            params.update(last_cont)
            data = self.request(**params)

            for log_data in data['query']['logevents']:
                yield log_data

            if 'continue' in data:
                last_cont = data['continue']
                last_cont['lelimit'] = self._wraplimit(params['leimit'])
            else:
                break

    def pagepropnames(self):
        """Retrieve a generator of all possible page properties."""
        params = {
            'action': 'query',
            'list': 'pagepropnames',
            'ppnlimit': 'max',
        }
        data = self.request(**params)

        for prop in data['query']['pagepropnames']:
            yield prop['propname']

    def pageswithprop(self, prop, limit="max", getinfo=True):
        """Retrieve a generator of Pages with a particular property."""
        last_cont = {}
        params = {
            'action': 'query',
            'list': 'pageswithprop',
            'pwppropname': prop,
            'pwpprop': 'ids|title|value',
            'pwplimit': limit,
        }

        while 1:
            params.update(last_cont)
            data = self.request(**params)

            for page in data['query']['pageswithprop']:
                yield Page(self, getinfo=getinfo, **page)

            if 'continue' in data:
                last_cont = data['continue']
                last_cont['pwplimit'] = self._wraplimit(params['pwplimit'])
            else:
                break

    def protectedtitles(self, limit="max", level=None,
                        namespace=None, getinfo=True):
        """Retrieve a generator of Pages protected from creation.

        This means that all of the Pages returned will have the "missing"
        attribute set.
        """
        last_cont = {}
        params = {
            'action': 'query',
            'list': 'protectedtitles',
            'ptnamespace': namespace,
            'ptlevel': level,
            'ptprop': 'timestamp|user|userid|comment|'
                      + 'parsedcomment|expiry|level',
            'ptlimit': limit
        }

        while 1:
            params.update(last_cont)
            data = self.request(**params)

            for page in data['query']['protectedtitles']:
                yield Page(self, getinfo=getinfo, **page)

            if 'continue' in data:
                last_cont = data['continue']
                last_cont['ptlimit'] = self._wraplimit(params['ptlimit'])
            else:
                break

    def random(self, limit="max", namespace=None, getinfo=True):
        """Retrieve a generator of random Pages."""
        last_cont = {}
        params = {
            'action': 'query',
            'list': 'random',
            'rnnamespace': namespace,
            'rnlimit': limit
        }

        while 1:
            params.update(last_cont)
            data = self.request(**params)

            for page in data['query']['random']:
                yield Page(self, getinfo=getinfo, **page)

            if 'continue' in data:
                last_cont = data['continue']
                last_cont['rnlimit'] = self._wraplimit(params['rnlimit'], 20)
            else:
                break

class Page(object):
    """The class for a page on a wiki.

    Must be initialized with a Wiki instance.

    Pages with the "missing" attribute set evaluate to False.
    """
    def __init__(self, wiki, getinfo=True, **data):
        """Initialize a page with its wiki and initially don't set a title.

        The Wiki class sets the title automatically, since the Page __init__
        updates its __dict__.

        If `getinfo` is True, request page info for the page.
        """
        self.wiki = wiki
        self.title = None
        self.__dict__.update(data)
        if getinfo:
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

    def read(self):
        """Retrieve the page's content."""
        data = self.wiki.request(**{
            'action': "query",
            'titles': self.title,
            'prop': "revisions",
            'rvprop': "content",
            'rvlimit': "1",
        })
        if length is not None:
            return list(data['query']['pages'].values())[0]["revisions"][0]["*"][:length]
        return list(data['query']['pages'].values())[0]['revisions'][0]['*']

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

    def deletedrevs(self, limit="max", **kwargs):
        """Get a generator of deleted Revisions for this page.

        See https://www.mediawiki.org/wiki/API:Deletedrevs for explanations
        of the various paraemeters.
        """
        last_cont = {}
        params = {
            'action': 'query',
            'list': 'deletedrevs',
            'titles': self.title,
            'drprop': 'revid|parentid|user|userid|comment|parsedcomment|minor|'
                      + 'len|sha1|tags',
            'drlimit': limit
        }
        params.update(kwargs)

        while 1:
            params.update(last_cont)
            data = self.wiki.request(**params)

            for rev_data in list(data['query']['deletedrevs'].values())[0]['revisions']:
                yield Revision(self.wiki, self, **rev_data)

            if 'continue' in data:
                last_cont = data['continue']
            else:
                break

    @property
    def url(self):
        """Return an approximation of the canonical URL for the page."""
        return self.wiki.site_url + urlencode({"x": self.title})[2:].replace("%2F", "/")

    def backlinks(self, limit="max", getinfo=True):
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
                yield Page(self.wiki, getinfo=getinfo, **page_data)

            if "continue" in data:
                last_cont = data["continue"]
            else:
                break

    def transclusions(self, limit="max", getinfo=True):
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
                yield Page(self.wiki, getinfo=getinfo, **page_data)

            if "continue" in data:
                last_cont = data["continue"]
            else:
                break

    def categorymembers(self, limit="max", getinfo=True):
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
                yield Page(self.wiki, getinfo=getinfo, **page)

            if "continue" in data:
                last_cont = data["continue"]
            else:
                break

    def imageusage(self, limit="max", namespace=None, getinfo=True):
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

        while 1:
            params.update(last_cont)
            data = self.wiki.request(**params)

            for page in data['query']['imageusage']:
                yield Page(self.wiki, getinfo=getinfo, **page)

            if 'continue' in data:
                last_cont = data['continue']
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

    def allmessages(self, messages='*', args=None, prefix=None,
                    getinfo=True, **kwargs):
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
                yield Page(self.wiki, getinfo=getinfo, **page_data)

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
