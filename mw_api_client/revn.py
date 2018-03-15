from __future__ import print_function
from .page import Page

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
