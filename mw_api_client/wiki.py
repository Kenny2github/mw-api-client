from __future__ import print_function
import time
import requests
from .page import *
from .user import *
from .excs import *
from .misc import *
from . import GETINFO

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
        self._session = requests.session()
        data = self.meta.siteinfo()
        self.wiki_url = data['server']
        self.site_url = data['server'] + data['articlepath'].replace('$1', '')
        self.currentuser = None

    def __repr__(self):
        """Represent a Wiki object."""
        return "<Wiki at {addr}>".format(addr=self.wiki_url)

    def __eq__(self, other):
        """Check if two Wikis are equal."""
        return self.wiki_url == other.wiki_url

    def __hash__(self):
        """Wiki.__hash__() <==> hash(Wiki)"""
        return hash(self.wiki_url)

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

        try:
            if _post:
                response = self._session.post(self.api_url, data=params,
                                              headers=headers, files=files)
            else:
                response = self._session.get(self.api_url, params=params,
                                             headers=headers, files=files)
        except requests.exceptions.ConnectionError:
            #try again as it may have been a one-time thing
            if _post:
                response = self._session.post(self.api_url, data=params,
                                              headers=headers, files=files)
            else:
                response = self._session.get(self.api_url, data=params,
                                             headers=headers, files=files)

        response.raise_for_status()

        #print(response.text)
        data = response.json()

        if 'error' in data:
            error = data['error']
            raise WikiError(error['info'], code=error['code'])

        if 'warnings' in data:
            warnings = data['warnings']
            for module, value in warnings.items():
                print('warning from', module, 'module:', value['*'])

        return data

    def checktoken(self, kind, token):
        """Check the validity of a token. Returns True if valid,
        False if invalid.
        """
        params = {
            'action': 'checktoken',
            'type': kind,
            'token': token,
        }
        if self.request(**params)['checktoken']['result'] == 'invalid':
            return False
        return True

    def upload(self, fileobj_or_url, filename,
               comment=None, ignorewarnings=None, **evil):
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
            'token': token,
            'ignorewarnings': ignorewarnings
        }
        params.update(evil)
        if isinstance(fileobj_or_url, str):
            params['url'] = fileobj_or_url
            return self.post_request(**params)
        files = {'file': fileobj_or_url}
        return self.post_request(files=files, **params)

    def import_(self, source, summary=None, iwpage=None,
                namespace=None, rootpage=None):
        """Import a page into the wiki.
        `source` can either be a file object or an interwiki prefix.
        """
        token = self.meta.tokens()
        params = {
            'action': 'import',
            'summary': summary,
            'interwikipage': iwpage,
            'namespace': namespace,
            'rootpage': rootpage,
            'token': token
        }
        if isinstance(source, str):
            params['interwikisource'] = source
            return self.post_request(**params)
        files = {'xml': source}
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

    def logout(self): #simple enough lol
        """Log out the current user."""
        self.currentuser = None
        return self.post_request(**{'action': 'logout'})

    def page(self, title, **evil):
        """Return a Page instance based off of the title of the page."""
        if isinstance(title, Page):
            return title
        return Page(self, title=title, **evil)

    def category(self, title, **evil):
        """Return a Page instance based off of the title of the page
        with `Category:` prepended.
        """
        if isinstance(title, Page):
            return title
        return Page(self, title='Category:' + title, **evil)

    def template(self, title, **evil):
        """Return a Page instance based off of the title of the page
        with `Template:` prepended.
        """
        if isinstance(title, Page):
            return title
        return Page(self, title='Template:' + title, **evil)

    def createaccount(self, name, reason, password=None,
                      email=None, mailpassword=False):
        """Create an account."""
        token = self.meta.tokens(kind='createaccount')
        params = {
            'action': 'createaccount',
            'username': name,
            'token': token,
            'email': email,
            'reason': reason
        }
        if mailpassword:
            if not email:
                raise ValueError('`email` must be specified with mailpassword.')
            params['mailpassword'] = True
        else:
            params['password'] = password
        return self.post_request(**params)

    def compare(self, original, new, pst=None, **evil):
        """Compare two Pages, revision (ID)s, or texts."""
        params = {
            'action': 'compare',
            'frompst': pst,
            'topst': pst,
            'prop': 'diff',
        }
        if isinstance(original, Page):
            if hasattr(original, 'pageid'): #prefer pageid over title
                params['fromid'] = original.pageid
            else:
                params['fromtitle'] = original.title
        elif isinstance(original, int):
            params['fromrev'] = original
        elif isinstance(original, str):
            params['fromtext'] = original
        else:
            raise TypeError('Inappropriate argument type for `original`.')
        if isinstance(new, Page):
            if hasattr(new, 'pageid'):
                params['toid'] = new.pageid
            else:
                params['totitle'] = new.title
        elif isinstance(new, int):
            params['torev'] = new
        elif isinstance(new, str):
            params['totext'] = new
        else:
            raise TypeError('Inappropriate argument type for `new`.')
        params.update(evil)
        data = self.request(**params)
        return data['compare']['*']

    def expandtemplates(self, text, title=None, revid=None,
                        comments=False, **evil):
        """Expand all templates in the wikitext."""
        params = {
            'action': 'expandtemplates',
            'text': text,
            'title': title,
            'revid': revid,
            'prop': 'wikitext'
        }
        if comments:
            params['includecomments'] = comments
        params.update(evil)

        data = self.request(**params)
        return data['expandtemplates']['wikitext']

    def parse(self, source, title=None, **evil):
        """Parse wikitext. `source` can be a string, Page,
        or integer revision ID."""
        params = {
            'action': 'parse',
            'redirects': True,
            'prop': 'text',
            'disablelimitreport': True,
        }
        if isinstance(source, str):
            params['text'] = source
            params['title'] = title
        elif isinstance(source, Page):
            if hasattr(source, 'pageid'):
                params['pageid'] = source.pageid
            else:
                params['page'] = source.title
        elif isinstance(source, int):
            params['oldid'] = source
        params.update(evil)

        data = self.request(**params)
        return data['parse']['text']['*']

    def managetags(self, operation, tag, reason=None, ignorewarnings=None):
        """Manage tags."""
        params = {
            'action': 'managetags',
            'operation': operation,
            'tag': tag,
            'reason': reason,
            'ignorewarnings': ignorewarnings,
            'token': self.meta.tokens()
        }
        return self.post_request(**params)

    def mergehistory(self, source, target, maxtime=None, reason=None):
        """Merge histories of two Pages."""
        params = {
            'action': 'mergehistory',
            'reason': reason,
            'token': self.meta.tokens()
        }
        if isinstance(source, Page):
            if hasattr(source, 'pageid'):
                params['fromid'] = source.pageid
            else:
                params['from'] = source.title
        elif isinstance(source, str):
            params['from'] = source
        elif isinstance(source, int):
            params['fromid'] = source
        else:
            raise TypeError('Inappropriate argument type for `source`.')
        if isinstance(target, Page):
            if hasattr(target, 'pageid'):
                params['toid'] = target.pageid
            else:
                params['to'] = target.title
        elif isinstance(target, str):
            params['to'] = target
        elif isinstance(target, int):
            params['toid'] = target
        else:
            raise TypeError('Inappropriate argument type for `source`.')
        if isinstance(maxtime, time.struct_time):
            params['timestamp'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', maxtime)
        elif isinstance(maxtime, str):
            params['timestamp'] = maxtime
        return self.post_request(**params)

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

    def alldeletedrevisions(self, limit="max", prefix=None, getinfo=None, **evil):
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

            for page in data['query']['alldeletedrevisions']:
                for rev in page['revisions']:
                    yield Revision(self,
                                   Page(self,
                                        getinfo=getinfo,
                                        **page),
                                   **rev)

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

    def allrevisions(self, limit="max", getinfo=None, **evil):
        """Retrieve a generator of all revisions."""
        last_cont = {}
        params = {
            'action': 'query',
            'list': 'allrevisions',
            'arvprop': 'ids|flags|timestamp|user|userid|size|sha1|contentmodel|'
                       + 'comment|parsedcomment|tags',
            'arvlimit': limit
        }
        params.update(evil)

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

    def allusers(self, limit="max", prefix=None, **evil):
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
        params.update(evil)

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
                    getinfo=None, **evil):
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
        params.update(evil)

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

    iwbacklinks = interwikibacklinks

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

    langbacklinks = languagebacklinks

    def logevents(self, limit="max", title=None, user=None, **evil):
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
        params.update(evil)

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

    def recentchanges(self, limit=50, mostrecent=None, **evil):
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
        params.update(evil)

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
