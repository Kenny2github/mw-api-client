"""This submodule contains the small classes."""

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

    def allmessages(self, *args, **kwargs):
        """Though the API module is in meta, this is implemented in Wiki
        due to importing ambiguities.
        """
        return self.wiki.allmessages(*args, **kwargs)

class GenericData(object): #pylint: disable=too-few-public-methods
    """A hunk of random API data
    that is not widely used enough to deserve its own class.
    """
    def __init__(self, _, **data):
        """Initialize the data by copying kwargs to __dict__"""
        self.__dict__.update(data)

    def __repr__(self):
        """Represent some GenericData."""
        result = '<GenericData: '
        result += repr(self.__dict__)
        result += '>'
        return result

    __str__ = __repr__

    def __getitem__(self, key):
        """Get an attribute like a dict item."""
        return self.__dict__.__getitem__(key)

    def __setitem__(self, key, val):
        """Set an attribute like a dict item."""
        return self.__dict__.__setitem__(key, val)

    def __delitem__(self, key):
        """Del an attribute like a dict item."""
        return self.__dict__.__delitem__(key)
