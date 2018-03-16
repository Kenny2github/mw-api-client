"""This submodule contains the small classes."""
from __future__ import print_function
from .page import Page

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

    __str__ = __repr__

    def __eq__(self, other):
        """Check if two changes are the same."""
        return self.rcid == other.rcid

    def __hash__(self):
        """RecentChange.__hash__() <==> hash(RecentChange)"""
        return hash(self.rcid)

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

    def tag(self, add=None, remove=None, reason=None):
        """Apply (a) tag(s) to this recent change."""
        if add is None and remove is None:
            raise ValueError('Ya gotta be doing something...')

        params = {
            'action': 'tag',
            'rcid': self.rcid,
            'add': '|'.join(add) if isinstance(add, list) else add,
            'remove': '|'.join(remove) if isinstance(remove, list) else remove,
            'token': self.wiki.meta.tokens(),
            'reason': reason
        }
        return self.wiki.post_request(**params)

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

    __str__ = __repr__

    def __eq__(self, other):
        """Check if two tags are the same."""
        return self.name == other.name

    def __hash__(self):
        """Tag.__hash__() <==> hash(Tag)"""
        return hash(self.name)

    def recentchanges(self, *args, **kwargs):
        """Get recent changes with this tag."""
        for change in self.wiki.recentchanges(*args, rctag=self.name, **kwargs):
            yield change

    @property
    def info(self):
        """Return a dict of information about this Tag."""
        return self.__dict__.copy()

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
                    getinfo=None, **evil):
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
            'amprefix': evil.get('prefix'),
        }
        params.update(evil)

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
