"""
This submodule contains the Page and User objects.
"""
from __future__ import print_function
# pylint: disable=too-many-lines,method-hidden
import re
import time
from .excs import WikiError, EditConflict
from .misc import GenericData, _CachedAttribute
from . import GETINFO

__all__ = [
    'Page',
    'User',
    'Revision',
]

class Page(object):
    """The class for a page on a wiki.

    Must be initialized with a Wiki instance.

    Pages with the "missing" attribute set evaluate to False.
    """
    #pylint: disable=too-many-arguments
    def __init__(self, wiki, title=None, getinfo=None, **data):
        """Initialize a page with its wiki and initially don't set a title.

        The Wiki class sets the title automatically, since the Page __init__
        updates its __dict__.

        If `getinfo` is True, request page info for the page.
        If `getinfo` is None, use the module default (defined by GETINFO)
        """
        self.wiki = wiki
        self.title = title
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

    def _generate(self, params, toyield, path,
                  getinfo=Ellipsis, extraself=False):
        """Centralizes generation of API data"""
        last_cont = {}
        for key in params:
            if key.endswith('limit'):
                limitkey = key
                break

        while 1:
            params.update(last_cont)
            data = self.wiki.request(**params)
            rootdata = data

            for part in path:
                if part == '__page':
                    data = tuple(data.values())[0]
                else:
                    try:
                        data = data[part]
                    except KeyError:
                        return #no such item, nothing to generate
            for thing in data:
                if '*' in thing:
                    thing['content'] = thing['*']
                    del thing['*']
                args = [self.wiki]
                if extraself:
                    args.append(self)
                if getinfo != Ellipsis:
                    yield toyield(*args, getinfo=getinfo, **thing)
                else:
                    yield toyield(*args, **thing)
            if params[limitkey] == 'max' \
                   or len(data) < params[limitkey]:
                if 'continue' in rootdata:
                    last_cont = rootdata['continue']
                    #pylint: disable=protected-access
                    last_cont[limitkey] = self.wiki._wraplimit(params)
                else:
                    break
            else:
                break

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
        page_data = tuple(data["query"]["pages"].values())[0]
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
            'rvslots': 'main'
        })
        missingq = False
        try:
            data = tuple(data['query']['pages'].values())[0]['revisions'][0]
        except KeyError:
            self.info()
            if hasattr(self, 'missing'):
                missingq = True
            else:
                raise
        if missingq:
            raise WikiError.notfound('The page does not exist.')
        self._lasttimestamp = time.mktime(time.strptime(data['timestamp'],
                                                        '%Y-%m-%dT%H:%M:%SZ'))
        self.content = data['slots']['main']['*']
        return self.content

    @_CachedAttribute
    def content(self):
        """This property replaces itself when contents are fetched.
        To update this property, use ``read``. Always prefer the ``read``
        method over using the property.
        """
        return self.read()

    def edit(self, content, summary, erroronconflict=True, **evil):
        """Edit the page with the content content."""

        token = self.wiki.meta.csrftoken

        try:
            rev = tuple(self.revisions(limit=1))[0]
            newtimestamp = time.mktime(time.strptime(rev.timestamp,
                                                     '%Y-%m-%dT%H:%M:%SZ'))
            if newtimestamp > self._lasttimestamp and erroronconflict:
                raise EditConflict('The last fetch was before \
the most recent revision.')
        except (IndexError, KeyError):
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

        result = {'result': None}

        try:
            result['result'] = self.wiki.post_request(**params)
        except WikiError.badtoken:
            del self.wiki.meta.csrftoken
            token = self.wiki.meta.csrftoken
            params['token'] = token
            result['result'] = self.wiki.post_request(**params)

        return result['result']

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
            'move': 'sysop'
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
        user = tuple(self.revisions(limit=1))[0].user
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
        data = tuple(data['query']['pages'].values())[0]
        self.__dict__.update(data)
        return data['categoryinfo']

    def revisions(self, limit="max", **evil):
        """Generate Revisions for this page.

        See https://www.mediawiki.org/wiki/API:Revisions for explanations
        of the various parameters.
        """
        params = {
            'action': 'query',
            'prop': 'revisions',
            'rvprop': 'ids|flags|timestamp|user|userid|size|sha1|contentmodel|'
                      + 'comment|parsedcomment|tags',
            'rvslots': 'main',
            'titles': self.title,
            'rvlimit': limit
        }
        params.update(evil)
        return self._generate(
            params,
            Revision,
            ('query', 'pages', '__page', 'revisions'),
            extraself=True
        )

    def deletedrevs(self, limit="max", **evil):
        """Generate deleted Revisions for this page.

        See https://www.mediawiki.org/wiki/API:Deletedrevs for explanations
        of the various paraemeters.
        """
        params = {
            'action': 'query',
            'list': 'deletedrevs',
            'drprop': 'revid|parentid|user|userid|comment|parsedcomment|minor|'
                      + 'len|sha1|tags',
            'titles': self.title,
            'drlimit': limit,
        }
        params.update(evil)
        return self._generate(
            params,
            Revision,
            ('query', 'deletedrevs'),
            extraself=True
        )

    def backlinks(self, limit="max", getinfo=None, **evil):
        """Generate Pages that link to this page."""
        params = {
            'action': "query",
            'list': "backlinks",
            'bltitle': self.title,
            'bllimit': limit,
        }
        params.update(evil)
        return self._generate(
            params,
            Page,
            ('query', 'backlinks'),
            getinfo
        )

    linkshere = backlinks #literally what is the difference?

    def redirects(self, limit='max', namespace=None, getinfo=None, **evil):
        """Generate redirects to this Page."""
        self.info() #needed to get pageid
        params = {
            'action': 'query',
            'prop': 'redirects',
            'titles': self.title,
            'rdlimit': limit,
            'rdnamespace': namespace,
        }
        params.update(evil)
        return self._generate(
            params,
            Page,
            ('query', 'pages', '__page', 'redirects'),
            getinfo
        )

    def interwikilinks(self, limit='max', fullurl=False, **evil):
        """Generate all interwiki links used by this page. If fullurl
        is specified, GenericData yielded will have an extra "url" attribute.
        """
        params = {
            'action': 'query',
            'titles': self.title,
            'prop': 'iwlinks',
            'iwlimit': limit,
            'iwprop': 'url' if fullurl else None,
        }
        params.update(evil)
        return self._generate(
            params,
            GenericData,
            ('query', 'pages', '__page', 'iwlinks'),
        )

    iwlinks = interwikilinks

    def languagelinks(self, limit='max', fullurl=True, **evil):
        """Generate all inter-language links used on this page.
        The yield format is (prefix, title, url).
        """
        params = {
            'action': 'query',
            'prop': 'languagelinks',
            'llprop': 'langname|autonym'
                      + ('|url' if fullurl else ''),
            'titles': self.title,
            'lllimit': limit,
        }
        params.update(evil)
        return self._generate(
            params,
            GenericData,
            ('query', 'pages', '__page', 'langlinks'),
        )

    langlinks = languagelinks

    def links(self, limit='max', namespace=None, getinfo=None, **evil):
        """Generate Pages that this Page links to."""
        params = {
            'action': 'query',
            'prop': 'links',
            'titles': self.title,
            'plnamespace': namespace,
            'pllimit': limit,
        }
        params.update(evil)
        return self._generate(
            params,
            Page,
            ('query', 'pages', '__page', 'links'),
            getinfo
        )

    def extlinks(self, limit='max', protocol=None, query=None, **evil):
        """Generate all external links this Page uses. Yield format is
        simply the URL.
        """
        params = {
            'action': 'query',
            'prop': 'extlinks',
            'elexpandurl': True,
            'titles': self.title,
            'ellimit': limit,
            'elprotocol': protocol,
            'elquery': query,
        }
        params.update(evil)
        return self._generate(
            params,
            GenericData,
            ('query', 'pages', '__page', 'extlinks'),
        )

    def transclusions(self, limit="max", namespace=None, getinfo=None, **evil):
        """Generate Pages that transclude this page."""
        params = {
            'action': "query",
            'list': "embeddedin",
            'eilimit': limit,
            'eititle': self.title,
            'einamespace': namespace,
        }
        params.update(evil)
        return self._generate(
            params,
            Page,
            ('query', 'embeddedin'),
            getinfo
        )

    embeddedin = transcludedin = transclusions #WHAT is the DIFFERENCE?

    def templates(self, limit='max', namespace=None, getinfo=None, **evil):
        """Generate Pages that this Page transcludes."""
        params = {
            'action': 'query',
            'prop': 'templates',
            'titles': self.title,
            'tlnamespace': namespace,
            'tllimit': limit,
        }
        params.update(evil)
        return self._generate(
            params,
            Page,
            ('query', 'pages', '__page', 'templates'),
            getinfo
        )

    def categorymembers(self, limit="max", namespace=None, getinfo=None, **evil):
        """Generate Pages in this category."""
        params = {
            'action': 'query',
            'list': 'categorymembers',
            'cmprop': 'ids|title|sortkey|sortkeyprefix|type|timestamp',
            'cmtitle': self.title,
            'cmlimit': limit,
            'cmnamespace': namespace,
        }
        params.update(evil)
        return self._generate(
            params,
            Page,
            ('query', 'categorymembers'),
            getinfo
        )

    def imageusage(self, limit="max", namespace=None, getinfo=None, **evil):
        """Generate Pages that link to this image."""
        params = {
            'action': 'query',
            'list': 'imageusage',
            'iutitle': self.title,
            'iunamespace': namespace,
            'iulimit': limit
        }
        params.update(evil)
        return self._generate(
            params,
            Page,
            ('query', 'imageusage'),
            getinfo
        )

    def fileusage(self, limit='max', namespace=None, getinfo=None, **evil):
        """Generate Pages that link to this File. TODO: figure out what
        the difference between this and imageusage is.
        """
        if not self.title.startswith('File:'):
            raise ValueError('Page is not a file')

        params = {
            'action': 'query',
            'titles': self.title,
            'prop': 'fileusage',
            'fuprop': 'pageid|title|redirect',
            'funamespace': namespace,
            'fulimit': limit,
        }
        params.update(evil)
        return self._generate(
            params,
            Page,
            ('query', 'pages', '__page', 'fileusage'),
            getinfo
        )

    def images(self, limit='max', getinfo=None, **evil):
        """Generate Pages based on what images this Page uses."""
        params = {
            'action': 'query',
            'titles': self.title,
            'prop': 'images',
            'imlimit': limit
        }
        params.update(evil)
        return self._generate(
            params,
            Page,
            ('query', 'pages', '__page', 'images'),
            getinfo
        )

    def duplicatefiles(self, limit='max', getinfo=None, **evil):
        """Generate duplicates of this file."""
        if not self.title.startswith("File:"):
            raise ValueError('Page is not a file')

        params = {
            'action': 'query',
            'prop': 'duplicatefiles',
            'titles': self.title,
            'dflimit': limit
        }
        params.update(evil)
        return self._generate(
            params,
            Page,
            ('query', 'pages', '__page', 'duplicatefiles'),
            getinfo
        )

    def pagepropnames(self):
        """Generate property names for this page."""
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
        return tuple(self.wiki.request(**params)['query']['pages']
                     .values())[0]['pageprops']

    def categories(self, limit='max', getinfo=None, **evil):
        """Get a generator of all categories used on this page."""
        params = {
            'action': 'query',
            'titles': self.title,
            'prop': 'categories',
            'clprop': 'sortkey|timestamp|hidden',
            'cllimit': limit
        }
        params.update(evil)
        return self._generate(
            params,
            Page,
            ('query', 'pages', '__page', 'categories'),
            getinfo
        )

    def contributors(self, limit='max', getinfo=None, **evil):
        """Get a generator of contributors to this page."""
        params = {
            'action': 'query',
            'titles': self.title,
            'prop': 'contributors',
            'pclimit': limit
        }
        params.update(evil)
        return self._generate(
            params,
            User,
            ('query', 'pages', '__page', 'contributors'),
            getinfo
        )

class CurrentUser(object):
    """The currently logged in user on a wiki."""
    def __init__(self, wiki):
        """Initialize the instance with its wiki."""
        self.wiki = wiki
        self.__dict__.update(self.wiki.meta.userinfo())
        self.user = User(self.wiki, name=self.name, getinfo=True)

    def __repr__(self):
        """Represent the current user."""
        return '<CurrentUser {un}>'.format(un=self.name)

    __str__ = __repr__

    def clearhasmsg(self):
        """Clear the "new message" notification."""
        self.wiki.request(_format='none',
                          **{'action': 'clearhasmsg'})

    def emailuser(self, target, body, subject=None, ccme=None):
        """Email another user."""
        token = self.wiki.meta.tokens()
        return self.wiki.post_request(**{
            'action': 'emailuser',
            'target': target.name if isinstance(target, User) else target,
            'subject': subject,
            'text': body,
            'ccme': ccme,
            'token': token
        })['emailuser']['result']

class User(object):
    """A user on a wiki."""
    def __init__(self, wiki, name=None,
                 getinfo=None, **userinfo):
        """Initialize the instance with its wiki and update its info."""
        self.wiki = wiki
        self.name = name
        self.__dict__.update(userinfo)
        if getinfo is None:
            getinfo = GETINFO
        if getinfo:
            data = next(self.wiki.users(self.name, justdata=True))
            self.__dict__.update(data)

    def __repr__(self):
        """Represent a User."""
        return '<User {un}>'.format(un=self.name)

    __str__ = __repr__

    def __eq__(self, other):
        """Check if two users are the same."""
        return self.name == other.name

    def __hash__(self):
        """User.__hash__() <==> hash(User)"""
        return hash(self.name)

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
                    #pylint: disable=protected-access
                    last_cont['uclimit'] = self.wiki._wraplimit(params)
                else:
                    break
            else:
                break

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
        data = self.wiki.post_request(**params)
        if capture:
            return data['resetpassword']['passwords'][self.name]
        return data['resetpassword']['status']

class Revision(object):
    """The class for a revision of a page.

    Must be initialized with a Wiki and Page instance.
    """
    def __init__(self, wiki, page, revid=None, **data):
        """Initialize a revision with its wiki and page.

        Initially does not set a revision ID, since the Page/Wiki classes
        pass that in data, which updates the __dict__.
        """
        self.wiki = wiki
        self.page = wiki.page(page) #use what Wiki does
        self.revid = revid
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
            'rvslots': 'main',
        }
        data = self.wiki.request(**params)

        return tuple(data['query']['pages'].values())[0]['revisions'][0]['slots']['main']['*']

    @_CachedAttribute
    def content(self):
        """The content of this revision.
        This should normally be set when a request instantiating a Revision
        includes the content.
        """
        if hasattr(self, 'slots'):
            return self.slots['main']['*']
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

        return tuple(data['query']['pages'].values())[0]['revisions'][0]['diff']

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
        return self.wiki.post_request(**params)['revisiondelete']['status']
