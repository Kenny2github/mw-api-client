"""
mw_api_client.qyoo - handling multiple requests in one.

Example use:

.. code-block:: python

    >>> queue = mw.Queue.fromtitles(mywiki, ('Main Page', 'Home'))
    >>> pages = queue.categories()
    >>> pages
    [<Page Main Page>, <Page Home>]
    >>> pages[0].categories
    [<Page Category:Main Pages>]
    >>> pages[1].categories
    [<Page Category:Redirects>]

Use for efficiency in batch processing.
"""
from .page import Page, Revision

class Queue(object):
    """A Queue makes batch processing of similarly-structured information
    about wiki data easier by fetching all data in one request.
    """

    def __init__(self, wiki, things=[], converter=None):
        """Set up the Queue, optionally initialized with an iterable.

        ``converter`` is an optional function to call on every item in
        ``things``; Queue(mywiki, [bunch, of, things], func) is equivalent
        to Queue(mywiki, list(map([bunch, of, things], func))).
        """
        self._converter = (lambda i: i) if converter is None else converter
        self._things = list(map(self._converter, things))
        self.wiki = wiki

    @classmethod
    def fromtitles(cls, wiki, things=[]):
        """Set up the Queue, optionally initialized with an iterable,
        all of whose arguments will be converted to a Page if possible.
        """
        return cls(wiki, things, wiki.page)

    @classmethod
    def frompages(cls, wiki, things=[]):
        """Set up the Queue, typechecking each item in it as a Page."""
        def check_is_page(thing):
            if not isinstance(thing, Page):
                raise TypeError('Item is not Page: ' + repr(thing))
            return thing
        return cls(wiki, things, check_is_page)

    @classmethod
    def fromrevisions(cls, wiki, things=[]):
        """Set up the Queue, typechecking each item in it as a Page."""
        def check_is_rev(thing):
            if not isinstance(thing, Revision):
                raise TypeError('Item is not Revision: ' + repr(thing))
            return thing
        return cls(wiki, things, check_is_rev)

    def __iadd__(self, thing):
        """Add something to this Queue (optionally using += syntax)."""
        self._things += self._converter(thing)

    add = __iadd__

    def __add__(self, other):
        """Concatenate two Queues."""
        if not isinstance(other, type(self)):
            raise TypeError("Cannot concatenate 'Queue' and '"
                            + type(other).__name__
                            + "'")
        self += other._things
        return self

    def __iter__(self):
        """Iterate over Queue items."""
        return iter(self._things)

    def __repr__(self):
        return '<Queue of: ' + repr(self._things) + '>'

    __str__ = __repr__

    def _convert(self, iterable, key, cls1, cls2):
        """Convert a list of dictionaries to a list of ``cls1``s, whose ``key``
        attribute is a list of ``cls2``s.
        """
        print(iterable)
        result = []
        if isinstance(iterable, dict):
            iterable = iterable.values() #ugh when will format JSONv2 come out
        for i in iterable:
            tmp = []
            if '*' in i:
                i['content'] = i['*']
                del i['*']
            convertedi = cls1(self.wiki, **i)
            for j in i[key]:
                if '*' in j:
                    j['content'] = j['*']
                    del j['*']
                if cls2 == Revision:
                    tmp.append(cls2(self.wiki, convertedi, **j))
                else:
                    tmp.append(cls2(self.wiki, **j))
            setattr(convertedi, key, tmp)
            result.append(convertedi)
        return result

    def _mklist(self, params, key, cls1, cls2):
        """Centralize generation of API data."""
        last_cont = {}
        limitkey = 'limit'
        for k in params:
            if k.endswith('limit'):
                limitkey = k
                break
        result = []

        while 1:
            params.update(last_cont)
            data = self.wiki.request(**params)
            result.extend(self._convert(data['query']['pages'],
                                        key,
                                        cls1,
                                        cls2))
            if params[limitkey] == 'max' \
                   or len(data['query']['pages']) < params[limitkey]:
                if 'continue' in data:
                    last_cont = data['continue']
                    last_cont[limitkey] = self.wiki._wraplimit(params)
                else:
                    break
            else:
                break
        return result

    #time for more API methods :D
    def categories(self, limit='max', hidden=0):
        """Return a list of Pages with lists of categories represented as
        more Pages. The Queue must contain only Pages.

        The ``hidden`` parameter specifies whether returned categories must be
        hidden (1), must not be hidden (-1), or can be either (0, default).
        """
        #typecheck
        for thing in self:
            if not isinstance(thing, Page):
                raise TypeError('Item is not Page: ' + repr(thing))
        titles = ''
        for page in self:
            titles += page.title + '|'
        titles = titles.strip('|')
        print(titles)

        last_cont = {}
        params = {
            'action': 'query',
            'titles': titles,
            'prop': 'categories',
            'clprop': 'sortkey|timestamp|hidden',
            'clshow': ('hidden'
                       if hidden == 1
                       else ('!hidden'
                             if hidden == -1
                             else None)),
            'cllimit': int(limit) if limit != 'max' else limit
        }
        return self._mklist(params, 'categories', Page, Page)
