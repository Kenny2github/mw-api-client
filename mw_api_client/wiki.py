"""
See the Wiki docstrings.
"""
from __future__ import print_function
#pylint: disable=too-many-lines
import time
from warnings import warn as _warn
import requests
from .page import Page, User, Revision
from .excs import WikiError, WikiWarning
from .misc import Tag, RecentChange, Meta, GenericData

class Wiki(object): #pylint: disable=too-many-public-methods
    #pylint: disable=too-many-arguments
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
            self.user_agent = "mw_api_client/3.0.0, python-requests/>=2.18.4"
        self.meta = Meta(self)
        self._session = requests.session()
        data = self.meta.siteinfo()
        self.wiki_url = data['server']
        self.currentuser = None

    def __repr__(self):
        """Represent a Wiki object."""
        return "<Wiki at {addr}>".format(addr=self.wiki_url)

    def __eq__(self, other):
        """Check if two Wikis are equal."""
        return self.wiki_url == other.wiki_url

    def __hash__(self):
        """Wiki.__hash__() <==> hash(Wiki)"""
        return hash(self.api_url)

    __str__ = __repr__

    def _generate(self, params, toyield, path, getinfo=Ellipsis):
        """Centralize generation of API data."""
        last_cont = {}
        limitkey = 'limit'
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
                if getinfo != Ellipsis:
                    yield toyield(self, getinfo=getinfo, **thing)
                else:
                    yield toyield(self, **thing)

            if params[limitkey] == 'max' \
                   or len(data) < params[limitkey]:
                if 'continue' in rootdata:
                    last_cont = rootdata['continue']
                    last_cont[limitkey] = self._wraplimit(params)
                else:
                    break
            else:
                break

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
        print(params)

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
            response.raise_for_status()
        except (requests.exceptions.ConnectionError,
                requests.exceptions.HTTPError):
            #try again as it may have been a one-time thing
            if _post:
                response = self._session.post(self.api_url, data=params,
                                              headers=headers, files=files)
            else:
                response = self._session.get(self.api_url, data=params,
                                             headers=headers, files=files)
            response.raise_for_status()

        print(response.text)
        data = response.json()

        if 'error' in data:
            error = data['error']
            raise WikiError(error['code'],
                            error['code'] + ': ' + error['info'])

        if 'warnings' in data:
            warnings = data['warnings']
            for module, value in warnings.items():
                _warn('warning from {} module: {}'.format(
                    module,
                    value['*']
                ), WikiWarning)

        return data

    def checktoken(self, token, kind='csrf'):
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
                namespace=None, rootpage=None, **evil):
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
        params.update(evil)
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

    def clientlogin(self, username, password):
        """Log in as a client.

        NOTE: This does not yet implement the full clientlogin API;
        use Wiki.request as required for your specific wiki.
        """
        lgtoken = self.meta.tokens('login')
        params = {
            'action': 'clientlogin',
            'username': username,
            'password': password,
            'logintoken': lgtoken,
            'loginreturnurl': self.api_url
        }
        data = self.post_request(**params)['clientlogin']
        self.currentuser = User(self, name=username,
                                currentuser=True, getinfo=True)
        return data

    def logout(self): #simple enough lol
        """Log out the current user."""
        self.currentuser = None
        return self.post_request(action='logout')

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

    def user(self, name, **evil):
        """Return a User instance based off of the username."""
        if isinstance(name, User):
            return name
        return User(self, name=name, **evil)

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
        """Generate all categories represented as Pages."""
        # NOTE: this function does not use _generate because it
        # has a special API data format - the * value is the title,
        # not the content.
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
        """Generate all deleted Revisions."""
        # NOTE: this function does not use _generate because it uses nested loops
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
                if '*' in page:
                    page['content'] = page['*']
                    del page['*']
                for rev in page['revisions']:
                    if '*' in rev:
                        rev['content'] = rev['*']
                        del rev['*']
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

    def allfileusages(self, limit="max", prefix=None, getinfo=None, **evil):
        """Generate Pages corresponding to all file usages."""
        params = {
            'action': 'query',
            'list': 'allfileusages',
            'afprop': 'ids|titles',
            'aflimit': limit,
            'afprefix': prefix,
        }
        params.update(evil)
        return self._generate(
            params,
            Page,
            ('query', 'allfileusages'),
            getinfo
        )

    def allimages(self, limit="max", prefix=None, getinfo=None, **evil):
        """Generate all images represented as Pages."""
        params = {
            'action': 'query',
            'list': 'allimages',
            'aiprop': 'timestamp|user|userid|comment|parsedcomment|'
                      + 'canonicaltitle|url|size|sha1|mime|mediatype|'
                      + 'metadata|commonmetadata|extmetadata|bitdepth',
            'ailimit': limit,
            'aiprefix': prefix,
        }
        params.update(evil)
        return self._generate(
            params,
            Page,
            ('query', 'allimages'),
            getinfo
        )

    def alllinks(self, limit="max", namespace=0,
                 prefix=None, getinfo=None, **evil):
        """Generate all links."""
        params = {
            'action': 'query',
            'list': 'alllinks',
            'alprop': 'ids|title',
            'allimit': limit,
            'alprefix': prefix,
            'alnamespace': namespace,
        }
        params.update(evil)
        return self._generate(
            params,
            Page,
            ('query', 'alllinks'),
            getinfo
        )

    def allmessages(self, limit='max', messages='*', args=None,
                    prefix=None, getinfo=None, **evil):
        """Generate all interface messages.

        The "messages" parameter specifies what messages to retrieve
        (default all).

        The "args" parameter specifies a list of arguments to substitute
        into the messages.

        The "prefix" parameter specifies a common prefix for the messages'
        titles.

        See https://www.mediawiki.org/wiki/API:Allmessages for details about
        other parameters.
        """
        params = {
            'action': 'query',
            'meta': 'allmessages',
            'ammessages': ('|'.join(messages)
                           if isinstance(messages, list)
                           else messages),
            'amargs': ('|'.join(args)
                       if isinstance(args, list)
                       else args),
            'amprefix': prefix,
            'amlimit': limit,
        }
        params.update(evil)
        return self._generate(
            params,
            Page,
            ('query', 'allmessages'),
            getinfo
        )

    def allpages(self, limit=100, namespace=0,
                 prefix=None, getinfo=None, **evil):
        """Generate all Pages.

        Default limit is 100 rather than "max" as "max" can take a long time,
        especially if "getinfo" is True.
        """
        params = {
            'action': 'query',
            'list': 'allpages',
            'aplimit': limit,
            'apprefix': prefix,
            'apnamespace': namespace,
        }
        params.update(evil)
        return self._generate(
            params,
            Page,
            ('query', 'allpages'),
            getinfo
        )

    def allredirects(self, limit="max", prefix=None, getinfo=None, **evil):
        """Generate all Pages that are redirects."""
        params = {
            'action': 'query',
            'list': 'allredirects',
            'arprop': 'ids|title|fragment|interwiki',
            'arprefix': prefix,
            'arlimit': limit,
        }
        params.update(evil)
        return self._generate(
            params,
            Page,
            ('query', 'allredirects'),
            getinfo
        )

    def allrevisions(self, limit="max", getinfo=None, **evil):
        """Generate all revisions."""
        # NOTE: this function does not use _generate because
        # it uses nested loops.
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
                if '*' in page:
                    page['content'] = page['*']
                    del page['*']
                for rev_data in page['revisions']:
                    if '*' in rev_data:
                        rev_data['content'] = rev_data['*']
                        del rev_data['*']
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

    def alltransclusions(self, limit="max", prefix=None, getinfo=None, **evil):
        """Generate all transclusions."""
        params = {
            'action': 'query',
            'list': 'alltransclusions',
            'atprop': 'title|ids',
            'atprefix': prefix,
            'atlimit': limit,
        }
        params.update(evil)
        return self._generate(
            params,
            Page,
            ('query', 'alltransclusions'),
            getinfo
        )

    def allusers(self, limit="max", prefix=None, ingroup=None,
                 notingroup=None, withrights=None, active=None, **evil):
        """Generate all Users.

        ``prefix`` specifies a common prefix for usernames.
        ``ingroup`` specifies a usergroup that generated Users must be in.
        ``notingroup`` specifies a usergroup that generated Users must not
        be in.
        ``withrights`` specifies userrights that generated Users must possess.
        ``active`` specifies that generated Users must be "active"
        (see Special:ActiveUsers for the definition of "active").
        """
        params = {
            'action': 'query',
            'list': 'allusers',
            'auprop': 'blockinfo|groups|implicitgroups|rights|editcount'
                      + '|registration',
            'augroup': ingroup,
            'auexcludegroup': notingroup,
            'aurights': withrights,
            'auactiveusers': active,
            'auprefix': prefix,
            'aulimit': limit,
        }
        params.update(evil)
        return self._generate(
            params,
            User,
            ('query', 'allusers'),
        )

    def blocks(self, limit="max", blockip=None, users=None, **evil):
        """Generate currently active blocks."""
        if blockip is not None and users is not None:
            raise ValueError('Cannot specify ``blockip`` and ``users`` at once.')
        params = {
            'action': 'query',
            'list': 'blocks',
            'bkprop': 'id|user|userid|by|byid|timestamp|expiry|reason|range|'
                      + 'flags',
            'bkip': blockip,
            'bkusers': users,
            'bklimit': limit,
        }
        params.update(evil)
        return self._generate(
            params,
            GenericData,
            ('query', 'blocks'),
        )

    def deletedrevs(self, limit="max", user=None,
                    namespace=None, getinfo=None, **evil):
        """Generate all deleted Revisions.

        This can be deleted user contributions (specify "user") or
        deleted revisions in a certain namespace (specify "namespace")
        or both.
        """
        # NOTE: this function is not decorator-made because
        # it uses nested loops.
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
                if '*' in page:
                    page['content'] = page['*']
                    del page['*']
                for rev_data in page['revisions']:
                    if '*' in rev_data:
                        rev_data['content'] = rev_data['*']
                        del rev_data['*']
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

    def exturlusage(self, limit="max", url=None,
                    protocol=None, getinfo=None, **evil):
        """Generate Pages that link to a particular URL or
        protocol, or simply external links in general.

        These pages will have an extra attribute, `url`, that shows what
        URL they link to externally.
        """
        params = {
            'action': 'query',
            'list': 'exturlusage',
            'euquery': url,
            'euprotocol': protocol,
            'eulimit': limit,
        }
        params.update(evil)
        return self._generate(
            params,
            Page,
            ('query', 'exturlusage'),
            getinfo
        )

    def filearchive(self, limit="max", prefix=None, getinfo=None, **evil):
        """Generate deleted files, represented as Pages."""
        params = {
            'action': 'query',
            'list': 'filearchive',
            'faprop': 'sha1|timestamp|user|size|description|parseddescription|'
                      + 'mime|mediatype|metadata|bitdepth|archivename',
            'falimit': limit,
            'faprefix': prefix
        }
        params.update(evil)
        return self._generate(
            params,
            Page,
            ('query', 'filearchive'),
            getinfo
        )

    def interwikibacklinks(self, iwprefix, iwtitle=None,
                           limit="max", getinfo=None, **evil):
        """Generate Pages that link to a particular
        interwiki prefix (and title, if specified)
        """
        params = {
            'action': 'query',
            'list': 'iwbacklinks',
            'iwblprop': 'iwprefix|iwtitle',
            'iwblprefix': iwprefix,
            'iwbltitle': iwtitle,
            'iwbllimit': limit,
        }
        params.update(evil)
        return self._generate(
            params,
            Page,
            ('query', 'iwbacklinks'),
            getinfo
        )

    iwbacklinks = interwikibacklinks

    def languagebacklinks(self, langprefix, langtitle=None,
                          limit="max", getinfo=None, **evil):
        """Generate Pages that link to a particular language
        code (and title, if specified)
        """
        params = {
            'action': 'query',
            'list': 'langbacklinks',
            'lbllang': langprefix,
            'lbltitle': langtitle,
            'lbllimit': limit,
            'lblprop': 'lllang|lltitle'
        }
        params.update(evil)
        return self._generate(
            params,
            Page,
            ('query', 'langbacklinks'),
            getinfo
        )

    langbacklinks = languagebacklinks

    def logevents(self, limit="max", title=None, user=None, **evil):
        """Generate log events.

        For more information on results, see:
        https://www.mediawiki.org/wiki/API:Logevents
        """
        params = {
            'action': 'query',
            'list': 'logevents',
            'leprop': 'ids|title|type|user|userid|timestamp|comment|'
                      + 'parsedcomment|details|tags',
            'leuser': user.name if isinstance(user, User) else user,
            'letitle': title.title if isinstance(title, Page) else title,
            'lelimit': limit,
        }
        params.update(evil)
        return self._generate(
            params,
            GenericData,
            ('query', 'logevents'),
        )

    def pagepropnames(self, limit='max', **evil):
        """Generate all possible page properties."""
        params = {
            'action': 'query',
            'list': 'pagepropnames',
            'ppnlimit': limit,
        }
        params.update(evil)
        return self._generate(
            params,
            GenericData,
            ('query', 'pagepropnames'),
        )

    def pageswithprop(self, prop, limit="max", getinfo=None, **evil):
        """Generate Pages with a particular property."""
        params = {
            'action': 'query',
            'list': 'pageswithprop',
            'pwpprop': 'ids|title|value',
            'pwppropname': prop,
            'pwplimit': limit,
        }
        params.update(evil)
        return self._generate(
            params,
            Page,
            ('query', 'pageswithprop'),
            getinfo
        )

    def protectedtitles(self, limit="max", level=None,
                        namespace=None, getinfo=None, **evil):
        """Generate Pages protected from creation.

        This means that all of the Pages returned will have the "missing"
        attribute set.
        """
        params = {
            'action': 'query',
            'list': 'protectedtitles',
            'ptprop': 'timestamp|user|userid|comment|'
                      + 'parsedcomment|expiry|level',
            'ptnamespace': namespace,
            'ptlevel': level,
            'ptlimit': limit,
        }
        params.update(evil)
        return self._generate(
            params,
            Page,
            ('query', 'protectedtitles'),
            getinfo
        )

    def random(self, limit="max", namespace=None, getinfo=None, **evil):
        """Generate random Pages."""
        params = {
            'action': 'query',
            'list': 'random',
            'rnnamespace': namespace,
            'rnlimit': limit,
        }
        params.update(evil)
        return self._generate(
            params,
            Page,
            ('query', 'random'),
            getinfo
        )

    def recentchanges(self, limit=50, mostrecent=None, **evil):
        """Retrieve recent changes on the wiki, a la Special:RecentChanges"""
        params = {
            'action': 'query',
            'list': 'recentchanges',
            'rcprop': 'user|userid|comment|parsedcomment|timestamp|title|ids|\
sha1|sizes|redirect|loginfo|tags|flags',
            'rctoponly': mostrecent,
            'rclimit': limit,
        }
        params.update(evil)
        return self._generate(
            params,
            RecentChange,
            ('query', 'recentchanges'),
        )

    def search(self, term, limit=500, namespace=None, getinfo=None, **evil):
        """Search page titles for `term`.

        Specify `namespace` to only search in that/those namespace(s).
        """
        params = {
            'action': 'query',
            'list': 'search',
            'srwhat': 'title|text|nearmatch',
            'srprop': 'size|wordcount|timestamp|score|snippet|titlesnippet|\
redirecttitle|redirectsnippet|sectiontitle|sectionsnippet',
            'srsearch': term,
            'srnamespace': namespace,
            'srlimit': limit,
        }
        params.update(evil)
        return self._generate(
            params,
            Page,
            ('query', 'search'),
            getinfo
        )

    def tags(self, limit='max', **evil):
        """Retrieve a generator of Tags on this wiki, a la Special:Tags."""
        params = {
            'action': 'query',
            'list': 'tags',
            'tglimit': limit,
            'tgprop': 'name|displayname|description|hitcount'
        }
        params.update(evil)
        return self._generate(
            params,
            Tag,
            ('query', 'tags'),
        )

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
        if justdata:
            yield self.request(**params)['query']['users'][0]
        else:
            for user_data in self.request(**params)['query']['users']:
                yield User(self, **user_data)
