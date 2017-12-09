"""
A really simple MediaWiki API client.

Can use most MediaWiki API modules.

Requires the ``requests`` library.

http://www.mediawiki.org/


Example Usage
=============
    import mw_api_client as mw

Get a page:

    wp = mw.Wiki("https://en.wikipedia.org/w/api.php", "MyCoolBot/0.0.0")

    wp.login("kenny2wiki", password)

    sandbox = wp.page("User:Kenny2wiki/sandbox")

Edit page:

    # Get the page
    contents = sandbox.read()

    # Change
    contents += "\n This is a test!"
    summary = "Made a test edit"

    # Submit
    sandbox.edit(contents, summary)

List pages in category:

    for page in wp.category("Redirects").categorymembers():
        print page.title

Remove all uses of a template:

    stub = wp.template("Stub")

    # Pages that transclude stub, main namespace only
    target_pages = list(stub.transclusions(namespace=0))

    # Sort by title because it's prettier that way
    target_pages.sort(key=lambda p: p.title)

    for page in target_pages:
        page.replace("{{stub}}", "")

Patrol all recent changes in the Help namespace:

    rcs = wp.recentchanges(namespace=12)

    for rc in rcs:
        rc.patrol()


Made by Kenny2github, based off of ~blob8108's Scratch Wiki API client.

MIT Licensed.
"""
from __future__ import print_function
try:
    from urllib.parse import urlencode
except ImportError:
    from urllib import urlencode
import re
import time
import requests

GETINFO = False #for convenience

__all__ = [
    'GETINFO',
    'WikiError',
    'EditConflict',
    'NotFound',
    'Wiki',
    'Page',
    'User',
    'Revision',
    'RecentChange',
    'Meta',
    'Tag'
]

class WikiError(Exception):
    """An arbitrary wiki error."""
    pass

class EditConflict(WikiError):
    """The last fetch of the page's content
    was before the most recent revision.
    """
    pass

class NotFound(WikiError):
    """The page does not have any content."""
    pass

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
            self.user_agent = user_agent
        else:
            self.user_agent = "mw_api_client/2.0.0, python-requests/>=2.18.4"
        self.meta = Meta(self)
        self.session = requests.session()
        data = self.meta.siteinfo()
        self.wiki_url = data['server']
        self.site_url = data['server'] + data['articlepath'].replace('$1', '')
        self.currentuser = None

    def __repr__(self):
        """Represent a Wiki object."""
        return "<Wiki at {addr}>".format(addr=self.wiki_url)

    __str__ = __repr__

    def _wraplimit(self, kwds):
        module = kwds['action'] + '+' + kwds.get('list', kwds.get('prop', kwds.get('meta')))
        params = {
            'action': 'paraminfo',
            'modules': module,
        }
        data = self.request(**params)
        data = data['paraminfo']['modules'][0]
        for param in data['parameters']:
            if param['name'] == 'limit':
                if 'apihighlimits' in getattr(self.currentuser, 'rights', ()):
                    wrap = param['highmax']
                else:
                    wrap = param['max']
                break
        limit = kwds[data['prefix'] + 'limit']
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
                limit = 1
            return limit
        else:
            raise TypeError('"limit" must be str or int, not '
                            + type(limit).__name__)

    def request(self, _headers=None, _post=False, files=None, **params):
        """Inner request method.

        Remains public since it might be used per se.
        """
        params["format"] = "json"

        headers = {
            "User-Agent": self.user_agent,
        }
        headers.update(_headers if _headers is not None else {})

        if _post:
            response = self.session.post(self.api_url, data=params,
                                         headers=headers, files=files)
        else:
            response = self.session.get(self.api_url, params=params,
                                        headers=headers, files=files)

        response.raise_for_status()

        #print(response.text)
        data = response.json()

        if 'error' in data:
            error = data['error']
            raise WikiError(error['code'] + ': ' + error['info'])

        return data

    def upload(self, fileobj_or_url, filename,
               comment=None, bigfile=False, **evil):
        """Upload a file.

        `fileobj_or_url` must be a file(-like) object open in BYTES mode or
        a canonical URL to a file to upload.
        `filename` is the target filename (including extension).
        `comment` is the upload comment, and is also the initial
        content for the file description page.
        If the file is particularly big, set `bigfile` to True to use
        MediaWiki's multi-request file upload format.
        """
        token = self.meta.tokens()
        params = {
            'action': 'upload',
            'filename': filename,
            'comment': comment,
            'token': token
        }
        params.update(evil)
        if isinstance(fileobj_or_url, str):
            params['url'] = fileobj_or_url
            return self.post_request(**params)
        else:
            params['filesize'] = fileobj_or_url.seek(0, 2)
            fileobj_or_url.seek(0)
            if bigfile:
                raise NotImplementedError('Sorry, this has \
not been implemented yet.')
            else:
                files = {'file': fileobj_or_url}
                return self.post_request(files=files, **params)

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
        self.currentuser = User(self, name=username,
                                currentuser=True, getinfo=True)
        return data

    def page(self, title, **kwargs):
        """Return a Page instance based off of the title of the page."""
        if isinstance(title, Page):
            return title
        return Page(self, title=title, **kwargs)

    def category(self, title, **kwargs):
        """Return a Page instance based off of the title of the page
        with `Category:` prepended.
        """
        if isinstance(title, Page):
            return title
        return Page(self, title='Category:' + title, **kwargs)

    def template(self, title, **kwargs):
        """Return a Page instance based off of the title of the page
        with `Template:` prepended.
        """
        if isinstance(title, Page):
            return title
        return Page(self, title='Template:' + title, **kwargs)

    def allcategories(self, limit="max", prefix=None, getinfo=None, **evil):
        """Retrieve a generator of all categories represented as Pages."""
        last_cont = {}
        params = {
            'action': 'query',
            'list': 'allcategories',
            'aclimit': limit,
            'acprefix': prefix,
            'acprop': 'size|hidden',
        }
        params.update(evil)
        while 1:
            params.update(last_cont)
            data = self.request(**params)

            for page_data in data['query']['allcategories']:
                page_data['title'] = page_data['*']
                del page_data['*']
                yield Page(self, getinfo=getinfo, **page_data)

            if limit == 'max' \
                   or len(data['query']['allcategories']) \
                   < params['aclimit']:
                if 'continue' in data:
                    last_cont = data['continue']
                    last_cont['aclimit'] = self._wraplimit(params)
                else:
                    break
            else:
                break

    def alldeletedrevisions(self, limit="max", prefix=None, **evil):
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
        params.update(evil)
        while 1:
            params.update(last_cont)
            data = self.request(**params)

            for rev_data in data['query']['alldeletedrevisions']:
                yield Revision(self, **rev_data)

            if limit == 'max' \
                   or len(data['query']['alldeletedrevisions']) \
                   < params['adrlimit']:
                if 'continue' in data:
                    last_cont = data['continue']
                    last_cont['adrlimit'] = self._wraplimit(params)
                else:
                    break
            else:
                break

    def allfileusages(self, limit="max", prefix=None,
                      unique=False, getinfo=None, **evil):
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
        params.update(evil)

        while 1:
            params.update(last_cont)
            data = self.request(**params)

            for page_data in data['query']['allfileusages']:
                yield Page(self, getinfo=getinfo, **page_data)

            if limit == 'max' \
                   or len(data['query']['allfileusages']) \
                   < params['aflimit']:
                if 'continue' in data:
                    last_cont = data['continue']
                    last_cont['aflimit'] = self._wraplimit(params)
                else:
                    break
            else:
                break

    def allimages(self, limit="max", prefix=None,
                  getinfo=None, **evil):
        """Retrieve a generator of all images represented as Pages."""
        last_cont = {}
        params = {
            'action': 'query',
            'list': 'allimages',
            'ailimit': limit,
            'aiprefix': prefix,
            'aiprop': 'timestamp|user|userid|comment|parsedcomment|'
                      + 'canonicaltitle|url|size|sha1|mime|mediatype|'
                      + 'metadata|commonmetadata|extmetadata|bitdepth'
        }
        params.update(evil)

        while 1:
            params.update(last_cont)
            data = self.request(**params)

            for page_data in data['query']['allimages']:
                yield Page(self, getinfo=getinfo, **page_data)

            if limit == 'max' \
                   or len(data['query']['allimages']) \
                   < params['ailimit']:
                if 'continue' in data:
                    last_cont = data['continue']
                    last_cont['ailimit'] = self._wraplimit(params)
                else:
                    break
            else:
                break

    def alllinks(self, limit="max", namespace='0',
                 prefix=None, getinfo=None, **evil):
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
        params.update(evil)

        while 1:
            params.update(last_cont)
            data = self.request(**params)

            for page_data in data['query']['alllinks']:
                yield Page(self, getinfo=getinfo, **page_data)

            if limit == 'max' \
                   or len(data['query']['alllinks']) \
                   < params['allimit']:
                if 'continue' in data:
                    last_cont = data['continue']
                    last_cont['allimit'] = self._wraplimit(params)
                else:
                    break
            else:
                break

    def allpages(self, limit="max", namespace=0,
                 prefix=None, getinfo=None, **evil):
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
        params.update(evil)

        while 1:
            params.update(last_cont)
            data = self.request(**params)

            for page_data in data['query']['allpages']:
                yield Page(self, getinfo=getinfo, **page_data)

            if limit == 'max' \
                   or len(data['query']['allpages']) \
                   < params['aplimit']:
                if 'continue' in data:
                    last_cont = data['continue']
                    last_cont['aplimit'] = self._wraplimit(params)
                else:
                    break
            else:
                break

    def allredirects(self, limit="max", prefix=None,
                     unique=False, getinfo=None, **evil):
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
        params.update(evil)

        while 1:
            params.update(last_cont)
            data = self.request(**params)

            for page_data in data['query']['allredirects']:
                yield Page(self, getinfo=getinfo, **page_data)

            if limit == 'max' \
                   or len(data['query']['allredirects']) \
                   < params['arlimit']:
                if 'continue' in data:
                    last_cont = data['continue']
                    last_cont['arlimit'] = self._wraplimit(params)
                else:
                    break
            else:
                break

    def allrevisions(self, limit="max", getinfo=None, **kwargs):
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

            if limit == 'max' \
                   or len(data['query']['allrevisions']) \
                   < params['arvlimit']:
                if 'continue' in data:
                    last_cont = data['continue']
                    last_cont['arvlimit'] = self._wraplimit(params)
                else:
                    break
            else:
                break

    def alltransclusions(self, limit="max", prefix=None,
                         unique=False, getinfo=None, **evil):
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
        params.update(evil)

        while 1:
            params.update(last_cont)
            data = self.request(**params)

            for page_data in data['query']['alltransclusions']:
                yield Page(self, getinfo=getinfo, **page_data)

            if limit == 'max' \
                   or len(data['query']['alltransclusions']) \
                   < params['atlimit']:
                if 'continue' in data:
                    last_cont = data['continue']
                    last_cont['atlimit'] = self._wraplimit(params)
                else:
                    break
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

            if limit == 'max' \
                   or len(data['query']['allusers']) \
                   < params['aulimit']:
                if 'continue' in data:
                    last_cont = data['continue']
                    last_cont['aulimit'] = self._wraplimit(params)
                else:
                    break
            else:
                break

    def blocks(self, limit="max", blockip=None, users=None, **evil):
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
        params.update(evil)

        while 1:
            params.update(last_cont)
            data = self.request(**params)

            for block_data in data['query']['blocks']:
                yield block_data

            if limit == 'max' \
                   or len(data['query']['blocks']) \
                   < params['bklimit']:
                if 'continue' in data:
                    last_cont = data['continue']
                    last_cont['bklimit'] = self._wraplimit(params)
                else:
                    break
            else:
                break

    def deletedrevs(self, limit="max", user=None,
                    namespace=None, getinfo=None, **evil):
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
        params.update(evil)

        while 1:
            params.update(last_cont)
            data = self.request(**params)

            for page in data['query']['deletedrevs']:
                for rev_data in page['revisions']:
                    yield Revision(self,
                                   Page(self, getinfo=getinfo, **page),
                                   **rev_data)

            if limit == 'max' \
                   or len(data['query']['deletedrevs']) \
                   < params['drlimit']:
                if 'continue' in data:
                    last_cont = data['continue']
                    last_cont['drlimit'] = self._wraplimit(params)
                else:
                    break
            else:
                break

    def exturlusage(self, limit="max", url=None, protocol=None,
                    getinfo=None, **kwargs):
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

            if limit == 'max' \
                   or len(data['query']['exturlusage']) \
                   < params['eulimit']:
                if 'continue' in data:
                    last_cont = data['continue']
                    last_cont['eulimit'] = self._wraplimit(params)
                else:
                    break
            else:
                break

    def filearchive(self, limit="max", prefix=None, getinfo=None, **evil):
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
        params.update(evil)

        while 1:
            params.update(last_cont)
            data = self.request(**params)

            for page in data['query']['filearchive']:
                yield Page(self, getinfo=getinfo, **page)

            if limit == 'max' \
                   or len(data['query']['filearchive']) \
                   < params['falimit']:
                if 'continue' in data:
                    last_cont = data['continue']
                    last_cont['falimit'] = self._wraplimit(params)
                else:
                    break
            else:
                break

    def interwikibacklinks(self, iwprefix, iwtitle=None,
                           limit="max", getinfo=None, **evil):
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
        params.update(evil)

        while 1:
            params.update(last_cont)
            data = self.request(**params)

            for page in data['query']['iwbacklinks']:
                yield Page(self, getinfo=getinfo, **page)

            if limit == 'max' \
                   or len(data['query']['iwbacklinks']) \
                   < params['iwblimit']:
                if 'continue' in data:
                    last_cont = data['continue']
                    last_cont['iwblimit'] = self._wraplimit(params)
                else:
                    break
            else:
                break

    def languagebacklinks(self, langprefix, langtitle=None,
                          limit="max", getinfo=None, **evil):
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
        params.update(evil)

        while 1:
            params.update(last_cont)
            data = self.request(**params)

            for page in data['query']['langbacklinks']:
                yield Page(self, getinfo=getinfo, **page)

            if limit == 'max' \
                   or len(data['query']['langbacklinks']) \
                   < params['lbllimit']:
                if 'continue' in data:
                    last_cont = data['continue']
                    last_cont['lbllimit'] = self._wraplimit(params)
                else:
                    break
            else:
                break

    def logevents(self, limit="max", title=None, user=None, **kwargs):
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
        params.update(kwargs)

        while 1:
            params.update(last_cont)
            data = self.request(**params)

            for log_data in data['query']['logevents']:
                yield log_data

            if limit == 'max' \
                   or len(data['query']['logevents']) \
                   < params['lelimit']:
                if 'continue' in data:
                    last_cont = data['continue']
                    last_cont['lelimit'] = self._wraplimit(params)
                else:
                    break
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

    def pageswithprop(self, prop, limit="max", getinfo=None, **evil):
        """Retrieve a generator of Pages with a particular property."""
        last_cont = {}
        params = {
            'action': 'query',
            'list': 'pageswithprop',
            'pwppropname': prop,
            'pwpprop': 'ids|title|value',
            'pwplimit': limit,
        }
        params.update(evil)

        while 1:
            params.update(last_cont)
            data = self.request(**params)

            for page in data['query']['pageswithprop']:
                yield Page(self, getinfo=getinfo, **page)

            if limit == 'max' \
                   or len(data['query']['pageswithprop']) \
                   < params['pwplimit']:
                if 'continue' in data:
                    last_cont = data['continue']
                    last_cont['pwplimit'] = self._wraplimit(params)
                else:
                    break
            else:
                break

    def protectedtitles(self, limit="max", level=None,
                        namespace=None, getinfo=None, **evil):
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
        params.update(evil)

        while 1:
            params.update(last_cont)
            data = self.request(**params)

            for page in data['query']['protectedtitles']:
                yield Page(self, getinfo=getinfo, **page)

            if limit == 'max' \
                   or len(data['query']['protectedtitles']) \
                   < params['ptlimit']:
                if 'continue' in data:
                    last_cont = data['continue']
                    last_cont['ptlimit'] = self._wraplimit(params)
                else:
                    break
            else:
                break

    def random(self, limit="max", namespace=None, getinfo=None, **evil):
        """Retrieve a generator of random Pages."""
        last_cont = {}
        params = {
            'action': 'query',
            'list': 'random',
            'rnnamespace': namespace,
            'rnlimit': limit
        }
        params.update(evil)

        while 1:
            params.update(last_cont)
            data = self.request(**params)

            for page in data['query']['random']:
                yield Page(self, getinfo=getinfo, **page)

            if limit == 'max' \
                   or len(data['query']['random']) \
                   < params['rnlimit']:
                if 'continue' in data:
                    last_cont = data['continue']
                    last_cont['rnlimit'] = self._wraplimit(params)
                else:
                    break
            else:
                break

    def recentchanges(self, limit=500, mostrecent=None, **kwargs):
        """Retrieve recent changes on the wiki, a la Special:RecentChanges"""
        last_cont = {}
        params = {
            'action': 'query',
            'list': 'recentchanges',
            'rcprop': 'user|userid|comment|parsedcomment|timestamp|title|ids|\
sha1|sizes|redirect|loginfo|tags|flags' + ('|patrolled' if 'patrol' in getattr(
    self.currentuser, 'rights', []) else ''),
            'rctoponly': mostrecent,
            'rclimit': limit
        }
        params.update(kwargs)

        while 1:
            params.update(last_cont)
            data = self.request(**params)

            for change in data['query']['recentchanges']:
                yield RecentChange(self, **change)

            if limit == 'max' \
                   or len(data['query']['recentchanges']) \
                   < params['rclimit']:
                if 'continue' in data:
                    last_cont = data['continue']
                    last_cont['rclimit'] = self._wraplimit(params)
                else:
                    break
            else:
                break

    def search(self, term, limit=500, namespace=None, getinfo=None, **evil):
        """Search page titles (or content, if `what` is 'text') for `term`.

        Specify `namespace` to only search in that/those namespace(s).
        """
        last_cont = {}
        params = {
            'action': 'query',
            'list': 'search',
            'srsearch': term,
            'srnamespace': namespace,
            'srwhat': 'title|text|nearmatch',
            'srprop': 'size|wordcount|timestamp|score|snippet|titlesnippet|\
redirecttitle|redirectsnippet|sectiontitle|sectionsnippet',
            'srlimit': limit
        }
        params.update(evil)

        while 1:
            params.update(last_cont)
            data = self.request(**params)

            for result in data['query']['search']:
                yield Page(self, getinfo=getinfo, **result)

            if limit == 'max' \
                   or len(data['query']['search']) \
                   < params['srlimit']:
                if 'continue' in data:
                    last_cont = data['continue']
                    last_cont['rclimit'] = self._wraplimit(params)
                else:
                    break
            else:
                break

    def tags(self, limit='max', **evil):
        """Retrieve a generator of Tags on this wiki, a la Special:Tags."""
        last_cont = {}
        params = {
            'action': 'query',
            'list': 'tags',
            'tglimit': limit,
            'tgprop': 'name|displayname|description|hitcount'
        }
        params.update(evil)

        while 1:
            params.update(last_cont)
            data = self.request(**params)

            for tagprop in data['query']['tags']:
                yield Tag(self, **tagprop)

            if limit == 'max' \
                   or len(data['query']['tags']) \
                   < params['tglimit']:
                if 'continue' in data:
                    last_cont = data['continue']
                    last_cont['tglimit'] = self._wraplimit(params)
                else:
                    break
            else:
                break

    def users(self, names=None, justdata=False, **evil):
        """Retrieve details of the specified users, and generate a list
        of Users.
        """
        params = {
            'action': 'query',
            'list': 'users',
            'ususers': names,
            'usprop': 'blockinfo|groups|implicitgroups|rights|'
                      + 'editcount|registration|emailable|gender',
        }
        params.update(evil)

        data = self.request(**params)
        if justdata:
            for userinfo in data['query']['users']:
                yield userinfo
            return
        for userinfo in data['query']['users']:
            yield User(self, currentuser=False, getinfo=False, **userinfo)


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
                raise NotFound('The page does not exist.')
            raise
        self._lasttimestamp = time.mktime(time.strptime(data['timestamp'],
                                                        '%Y-%m-%dT%H:%M:%SZ'))
        return data['*']

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

            for revd in list(data['query']['pages'].values())[0]['revisions']:
                yield Revision(self.wiki, self, **revd)

            if limit == 'max' \
                   or len(list(data['query']['pages'].values())[0]['revisions'])\
                   < params['rvlimit']:
                if 'continue' in data:
                    last_cont = data['continue']
                    last_cont['rvlimit'] = self.wiki._wraplimit(params)
                else:
                    break
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

            if limit == 'max' \
                   or len(data['query']['deletedrevs']) \
                   < params['drlimit']:
                if 'continue' in data:
                    last_cont = data['continue']
                    last_cont['drlimit'] = self.wiki._wraplimit(params)
                else:
                    break
            else:
                break

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
                yield Page(self.wiki, getinfo=getinfo, **page)

            if limit == 'max' \
                   or len(data['query']['imageusage']) \
                   < params['iulimit']:
                if 'continue' in data:
                    last_cont = data['continue']
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

class RecentChange(object):
    """A recent change. Used *specifically* for Wiki.recentchanges."""
    def __init__(self, wiki, **change):
        """Initialize a recent change."""
        self.wiki = wiki
        self.rcid = None
        self.__dict__.update(change)

    def __repr__(self):
        """Represent a recent change."""
        return "<Recent change id {rc}>".format(rc=self.rcid)

    def patrol(self):
        """Patrol this recent change."""
        token = self.wiki.meta.tokens(kind='patrol')
        return self.wiki.post_request(**{
            'action': 'patrol',
            'rcid': self.rcid,
            'token': token
        })

    @property
    def info(self):
        """Return a dict of information about this recent change."""
        return self.__dict__.copy()

class Tag(object):
    """A tag. Used for Wiki.tags, but can also be used for tag-specific
    recentchanges.
    """
    def __init__(self, wiki, **taginfo):
        """Initialize a Tag."""
        self.wiki = wiki
        self.name = None
        self.__dict__.update(taginfo)

    def __repr__(self):
        """Represent a Tag."""
        return "<Tag '{nam}'>".format(nam=self.name)

    def recentchanges(self, *args, **kwargs):
        """Get recent changes with this tag."""
        for change in self.wiki.recentchanges(*args, rctag=self.name, **kwargs):
            yield change

    @property
    def info(self):
        """Return a dict of information about this Tag."""
        return self.__dict__.copy()

class User(object):
    """A user on a wiki."""
    def __init__(self, wiki, currentuser=False, getinfo=None, **userinfo):
        """Initialize the instance with its wiki and update its info."""
        self.wiki = wiki
        self.name = None
        self.currentuser = currentuser
        self.__dict__.update(userinfo)
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

    def block(self, reason, expiry=None, **kwargs):
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
        params.update(kwargs)

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
            'ucprop': 'ids|title|timestamp|comment|parsedcomment|size|sizediff|\
flags|tags' + '|patrolled' if 'patrol' in getattr(self.wiki.currentuser,
                                                  []) else '',
        }
        params.update(evil)

        while 1:
            params.update(last_cont)
            data = self.wiki.request(**params)

            for rev in data['query']['usercontribs']:
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

class Meta(object):
    """A separate class for the API "meta" module."""
    def __init__(self, wiki):
        """Initialize the instance with its wiki."""
        self.wiki = wiki

    def __repr__(self):
        """Represent the Meta instance (there should only ever be one!)."""
        return '<Meta>'

    __str__ = __repr__

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

    def allmessages(self, limit='max', messages='*', args=None,
                    getinfo=None, **kwargs):
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
            'amprefix': kwargs.get('prefix'),
        }
        params.update(kwargs)

        while 1:
            params.update(last_cont)
            data = self.wiki.request(**params)

            for page_data in data['query']['allmessages']:
                yield Page(self.wiki, getinfo=getinfo, **page_data)

            if limit == 'max' \
                   or len(data['query']['allmessages']) \
                   < params['amlimit']:
                if 'continue' in data:
                    last_cont = data['continue']
                    last_cont['amlimit'] = self.wiki._wraplimit(params)
                else:
                    break
            else:
                break

    def filerepoinfo(self, prop=None, **evil):
        """Retrieve information about the site's file repositories.

        See https://www.mediawiki.org/wiki/API:Filerepoinfo for information
        about results.
        """
        params = {
            'action': 'query',
            'meta': 'filerepoinfo',
            'friprop': prop,
        }
        params.update(evil)
        data = self.wiki.request(**params)
        return data['query']['repos']

    def siteinfo(self, prop=None, filteriw=None, showalldb=None,
                 numberingroup=None, **evil):
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
        params.update(evil)
        data = self.wiki.request(**params)
        return list(data['query'].values())[0]
