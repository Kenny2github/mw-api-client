from __future__ import annotations
from typing import (
    TYPE_CHECKING, Any, AsyncIterator, Generic, Literal, Never, ParamSpec,
    TypeVar, TypeVarTuple, Union, overload
)

from .misc import Limit, Namespace

if TYPE_CHECKING:
    from . import page, user, misc

AnnoT = TypeVar('AnnoT')
P = ParamSpec('P')
R = TypeVar('R')

class _PageProps:

    @overload
    def links(
        self: page.Page, limit: Literal[1], *,
        namespaces: list[Namespace] | None = None,
        pages: list[page.Page] | None = None,
        descending: bool = False,
    ) -> OnePageGenerator: ...
    @overload
    def links(
        self: page.Page, limit: Limit = None, *,
        namespaces: list[Namespace] | None = None,
        pages: list[page.Page] | None = None,
        descending: bool = False,
    ) -> PageGenerator: ...
    @overload
    def links(
        self: page.Pages, limit: Literal[1], *,
        namespaces: list[Namespace] | None = None,
        pages: list[page.Page] | None = None,
        descending: bool = False,
    ) -> OnePageGenerator: ...
    @overload
    def links(
        self: page.Pages, limit: Limit = None, *,
        namespaces: list[Namespace] | None = None,
        pages: list[page.Page] | None = None,
        descending: bool = False,
    ) -> PageGenerator: ...
    @overload
    def links(
        self: OnePageGenerator, limit: Limit = None, *,
        namespaces: list[Namespace] | None = None,
        pages: list[page.Page] | None = None,
        descending: bool = False,
    ) -> GeneratedGenerator[page.Page, page.Page]: ...
    @overload
    def links(
        self: PageGenerator, limit: None = None, *,
        namespaces: list[Namespace] | None = None,
        pages: list[page.Page] | None = None,
        descending: bool = False,
    ) -> GeneratedGenerator[page.Page, page.Page]: ...
    def links(
        self, limit: Limit = None, *,
        namespaces: list[Namespace] | None = None,
        pages: list[page.Page] | None = None,
        descending: bool = False,
    ) -> Any: # page.Page+ -> page.Page
        """Fetch the pages that these pages links to.

        Parameters:
            limit: |see-limit|
            namespaces: Only generate links in these namespaces.
            pages: Only generate links *to* these pages. Useful for checking
                whether those links are present.
            descending: If :data:`True`, generate in descending order (instead
                of the default ascending order).

        Yields:
            If iterated with ``async for``, each page which this page links to.
        """
        raise NotImplementedError

    @overload
    def categories(
        self: page.Page, limit: Literal[1], *,
        show_hidden: bool | None = None,
        categories: list[page.Category] | None = None,
        descending: bool = False,
    ) -> OneCategoryGenerator: ...
    @overload
    def categories(
        self: page.Page, limit: Limit = None, *,
        show_hidden: bool | None = None,
        categories: list[page.Category] | None = None,
        descending: bool = False,
    ) -> CategoryGenerator: ...
    @overload
    def categories(
        self: page.Pages, limit: Literal[1], *,
        show_hidden: bool | None = None,
        categories: list[page.Category] | None = None,
        descending: bool = False,
    ) -> OneCategoryGenerator: ...
    @overload
    def categories(
        self: page.Pages, limit: Limit = None, *,
        show_hidden: bool | None = None,
        categories: list[page.Category] | None = None,
        descending: bool = False,
    ) -> CategoryGenerator: ...
    @overload
    def categories(
        self: OnePageGenerator, limit: Limit = None, *,
        show_hidden: bool | None = None,
        categories: list[page.Category] | None = None,
        descending: bool = False,
    ) -> GeneratedGenerator[page.Page, page.Category]: ...
    @overload
    def categories(
        self: PageGenerator, limit: None = None, *,
        show_hidden: bool | None = None,
        categories: list[page.Category] | None = None,
        descending: bool = False,
    ) -> GeneratedGenerator[page.Page, page.Category]: ...
    def categories(
        self, limit: Limit = None, *,
        show_hidden: bool | None = None,
        categories: list[page.Category] | None = None,
        descending: bool = False,
    ) -> Any: # page.Page+ -> page.Category
        """Fetch the categories that these pages belongs to.

        Parameters:
            limit: |see-limit|
            show_hidden: If :data:`True`, *only* generate hidden categories. If
                :data:`False`, *don't* generate hidden categories. If
                :data:`None`, generate all categories.
            categories: Only generate these categories. Useful for checking
                whether the page belongs to those categories.
            descending: If :data:`True`, generate in descending order (instead
                of the default ascending order).

        Yields:
            If iterated with ``async for``, each category which this page
            belongs to.
        """
        raise NotImplementedError

    @overload
    def templates(
        self: page.Page, limit: Literal[1], *,
        namespaces: list[Namespace] | None = None,
        templates: list[page.Template] | None = None,
        descending: bool = False,
    ) -> OneTemplateGenerator: ...
    @overload
    def templates(
        self: page.Page, limit: Limit = None, *,
        namespaces: list[Namespace] | None = None,
        templates: list[page.Template] | None = None,
        descending: bool = False,
    ) -> TemplateGenerator: ...
    @overload
    def templates(
        self: page.Pages, limit: Literal[1], *,
        namespaces: list[Namespace] | None = None,
        templates: list[page.Template] | None = None,
        descending: bool = False,
    ) -> OneTemplateGenerator: ...
    @overload
    def templates(
        self: page.Pages, limit: Limit = None, *,
        namespaces: list[Namespace] | None = None,
        templates: list[page.Template] | None = None,
        descending: bool = False,
    ) -> TemplateGenerator: ...
    @overload
    def templates(
        self: OnePageGenerator, limit: Limit = None, *,
        namespaces: list[Namespace] | None = None,
        templates: list[page.Template] | None = None,
        descending: bool = False,
    ) -> GeneratedGenerator[page.Page, page.Template]: ...
    @overload
    def templates(
        self: PageGenerator, limit: None = None, *,
        namespaces: list[Namespace] | None = None,
        templates: list[page.Template] | None = None,
        descending: bool = False,
    ) -> GeneratedGenerator[page.Page, page.Template]: ...
    def templates(
        self, limit: Limit = None, *,
        namespaces: list[Namespace] | None = None,
        templates: list[page.Template] | None = None,
        descending: bool = False,
    ) -> Any: # page.Page+ -> page.Template
        """Fetch the pages that these pages transclude.

        Parameters:
            limit: |see-limit|
            namespaces: Only generate templates in these namespaces.
            pages: Only generate these templates. Useful for checking whether those
                templates are present.
            descending: If :data:`True`, generate in descending order (instead
                of the default ascending order).

        Yields:
            If iterated with ``async for``, each page which these pages transclude.
        """
        raise NotImplementedError

    @overload
    def links_here(
        self: page.Page, limit: Literal[1], *,
        namespaces: list[Namespace] | None = None,
        show_redirects: bool | None = None,
    ) -> OnePageGenerator: ...
    @overload
    def links_here(
        self: page.Page, limit: Limit = None, *,
        namespaces: list[Namespace] | None = None,
        show_redirects: bool | None = None,
    ) -> PageGenerator: ...
    @overload
    def links_here(
        self: page.Pages, limit: Literal[1], *,
        namespaces: list[Namespace] | None = None,
        show_redirects: bool | None = None,
    ) -> OnePageGenerator: ...
    @overload
    def links_here(
        self: page.Pages, limit: Limit = None, *,
        namespaces: list[Namespace] | None = None,
        show_redirects: bool | None = None,
    ) -> PageGenerator: ...
    @overload
    def links_here(
        self: OnePageGenerator, limit: Limit = None, *,
        namespaces: list[Namespace] | None = None,
        show_redirects: bool | None = None,
    ) -> GeneratedGenerator[page.Page, page.Page]: ...
    @overload
    def links_here(
        self: PageGenerator, limit: None = None, *,
        namespaces: list[Namespace] | None = None,
        show_redirects: bool | None = None,
    ) -> GeneratedGenerator[page.Page, page.Page]: ...
    def links_here(
        self, limit: Limit = None, *,
        namespaces: list[Namespace] | None = None,
        show_redirects: bool | None = None,
    ) -> Any: # page.Page+ -> page.Page
        """Fetch the pages that link to these pages.

        Parameters:
            limit: |see-limit|
            namespaces: Only generate links from pages in these namespaces.
            show_redirects: If :data:`True`, *only* generate redirects. If
                :data:`False`, *don't* generate redirects. If :data:`None`,
                generate all links.

        Yields:
            If iterated with ``async for``, each page that links to these pages.
        """
        raise NotImplementedError

    @overload
    def contributors(
        self: page.Page, limit: Literal[1], *,
        only_groups: list[str] | None = None,
        not_groups: list[str] | None = None,
        only_rights: list[str] | None = None,
        not_rights: list[str] | None = None,
    ) -> OneUserGenerator: ...
    @overload
    def contributors(
        self: page.Page, limit: Limit = None, *,
        only_groups: list[str] | None = None,
        not_groups: list[str] | None = None,
        only_rights: list[str] | None = None,
        not_rights: list[str] | None = None,
    ) -> UserGenerator: ...
    @overload
    def contributors(
        self: page.Pages, limit: Literal[1], *,
        only_groups: list[str] | None = None,
        not_groups: list[str] | None = None,
        only_rights: list[str] | None = None,
        not_rights: list[str] | None = None,
    ) -> OneUserGenerator: ...
    @overload
    def contributors(
        self: page.Pages, limit: Limit = None, *,
        only_groups: list[str] | None = None,
        not_groups: list[str] | None = None,
        only_rights: list[str] | None = None,
        not_rights: list[str] | None = None,
    ) -> UserGenerator: ...
    @overload
    def contributors(
        self: OnePageGenerator, limit: Limit = None, *,
        only_groups: list[str] | None = None,
        not_groups: list[str] | None = None,
        only_rights: list[str] | None = None,
        not_rights: list[str] | None = None,
    ) -> GeneratedGenerator[page.Page, user.User]: ...
    @overload
    def contributors(
        self: PageGenerator, limit: None = None, *,
        only_groups: list[str] | None = None,
        not_groups: list[str] | None = None,
        only_rights: list[str] | None = None,
        not_rights: list[str] | None = None,
    ) -> GeneratedGenerator[page.Page, user.User]: ...
    def contributors(
        self, limit: Limit = None, *,
        only_groups: list[str] | None = None,
        not_groups: list[str] | None = None,
        only_rights: list[str] | None = None,
        not_rights: list[str] | None = None,
    ) -> Any: # page.Page+ -> user.User
        """Fetch the users who contributed to these pages."""
        raise NotImplementedError

class _PageLists:
    pass

class _CategoryProps(_PageProps):
    pass

class _CategoryLists(_PageLists):

    @overload
    def pages(
        self: page.Category, limit: Literal[1], *,
        namespaces: list[Namespace] | None = None,
        descending: bool = False,
        type: set[Literal['page', 'subcat', 'file']] | None = None,
        sort: Literal['sortkey', 'timestamp'] = 'sortkey',
    ) -> OnePageGenerator: ...
    @overload
    def pages(
        self: page.Category, limit: Limit = None, *,
        namespaces: list[Namespace] | None = None,
        descending: bool = False,
        type: set[Literal['page', 'subcat', 'file']] | None = None,
        sort: Literal['sortkey', 'timestamp'] = 'sortkey',
    ) -> PageGenerator: ...
    def pages(
        self, limit: Limit = None, *,
        namespaces: list[Namespace] | None = None,
        descending: bool = False,
        type: set[Literal['page', 'subcat', 'file']] | None = None,
        sort: Literal['sortkey', 'timestamp'] = 'sortkey',
    ) -> Any: # page.Category! -> page.Page
        """Fetch the pages in this category.

        Parameters:
            limit: |see-limit|
            namespaces: Only generate category members in these namespaces.
            descending: If :data:`True`, generate in descending order (instead
                of the default ascending order).

        Yields:
            If iterated with ``async for``, each page in this category.
        """
        raise NotImplementedError

class _FileProps(_PageProps):
    pass

class _FileLists(_PageLists):
    pass

class _TemplateProps(_PageProps):

    @overload
    def transclusions(
        self: page.Template, limit: Literal[1], *,
        namespaces: list[Namespace] | None = None,
        descending: bool = False,
        show_redirects: bool | None = None,
    ) -> OnePageGenerator: ...
    @overload
    def transclusions(
        self: page.Template, limit: Limit = None, *,
        namespaces: list[Namespace] | None = None,
        descending: bool = False,
        show_redirects: bool | None = None,
    ) -> PageGenerator: ...
    @overload
    def transclusions(
        self: page.Templates, limit: Literal[1], *,
        namespaces: list[Namespace] | None = None,
        descending: bool = False,
        show_redirects: bool | None = None,
    ) -> OnePageGenerator: ...
    @overload
    def transclusions(
        self: page.Templates, limit: Limit = None, *,
        namespaces: list[Namespace] | None = None,
        descending: bool = False,
        show_redirects: bool | None = None,
    ) -> PageGenerator: ...
    @overload
    def transclusions(
        self: OneTemplateGenerator, limit: Limit = None, *,
        namespaces: list[Namespace] | None = None,
        descending: bool = False,
        show_redirects: bool | None = None,
    ) -> GeneratedGenerator[page.Template, page.Page]: ...
    @overload
    def transclusions(
        self: TemplateGenerator, limit: None = None, *,
        namespaces: list[Namespace] | None = None,
        descending: bool = False,
        show_redirects: bool | None = None,
    ) -> GeneratedGenerator[page.Template, page.Page]: ...
    def transclusions(
        self, limit: Limit = None, *,
        namespaces: list[Namespace] | None = None,
        descending: bool = False,
        show_redirects: bool | None = None,
    ) -> Any: # page.Template+ -> page.Page
        """Fetch the pages that transclude these pages.

        Parameters:
            limit: |see-limit|
            namespaces: Only generate transclusions from pages in these
                namespaces.
            show_redirects: If :data:`True`, *only* generate redirects. If
                :data:`False`, *don't* generate redirects. If :data:`None`,
                generate all transclusions.

        Yields:
            If iterated with ``async for``, each page that transcludes these
            pages.
        """
        raise NotImplementedError

class _TemplateLists(_PageLists):
    pass

class _UserProps:
    pass

class _UserLists:
    pass

Generatable = Union['page.Page', 'user.User', 'misc.RecentChange']
GenT = TypeVar('GenT', covariant=True, bound=Generatable)
GenGenT = TypeVar('GenGenT', covariant=True, bound=Generatable)
GenTs = TypeVarTuple('GenTs')
OtherGenTs = TypeVarTuple('OtherGenTs')

class Generator(Generic[GenT, *GenTs]):
    """Smart generator. |noinit|

    There are four kinds of :class:`Generator`:

    1. First-order mono-generator: a single stream of results based on one or
       more sources that were not themselves generated, e.g.
       :meth:`mw_api.Category.pages()`. These are hinted with (e.g.)
       :class:`PageGenerator`, a subclass of ``Generator[Page]``.
    2. First-order multi-generator: multiple streams of results based on one or
       more sources that were not themselves generated, formed by ``|``-ing
       together multiple first-order mono-generators. These are hinted with
       (e.g.) ``Generator[Page, Category]`` for :meth:`mw_api.Page.links()`
       ``|`` :meth:`mw_api.Page.categories()`.
    3. Second-order mono-generator: a single stream of results based on a
       previous first-order generator, e.g. :meth:`PageGenerator.categories()`.
       These are hinted with (e.g.) ``GeneratedGenerator[Page, Category]``.
    4. Second-order multi-generator: multiple streams of results based on the
       same first-order mono-generator, formed by ``|``-ing together multiple
       second-order mono-generators **from the same first-order source**. These
       are hinted with (e.g.) ``GeneratedGenerator[Page, Category, Page]`` for
       :meth:`PageGenerator.categories()` ``|`` :meth:`PageGenerator.links()`.

    First- and second-order mono-generators can be :meth:`__aiter__()`'d to
    dynamically fetch results until reaching the :attr:`limit`, or
    :meth:`fetchall()`'d to do all the fetching in one go. Multi-generators
    can only be :meth:`fetchall()`'d (as there is no good way to structure an
    iterative approach that doesn't involve prefetching all the data anyway).

    The methods that would be available on each individual result yielded by a
    first-order mono-generator are also available on the generator instance
    itself; these return a second-order mono-generator. In this way, a
    first-order mono-generator acts much like a :class:`~mw_api.page.Pages`
    or its corresponding equivalent, and is an alternative way of specifying
    multiple items as the source for a generator.

    Attributes:
        limit: The maximum number of results to generate. If :data:`None`,
            keep fetching until all available results are generated. If the
            literal ``'max'``, generate the maximum number permissible in one
            API fetch. Otherwise, generate at most this many results (possibly
            requiring multiple fetches if more than the maximum permissible in
            one fetch).

            Second-order generators generally cannot have any limit other than
            :data:`None`, because the API paginates through all of the results
            for the second-order stream for the first first-order result before
            beginning with the next. As such, there is no way to fetch only the
            first N second-order results for each first-order result. The
            exception is if the first-order generator has a limit of exactly 1.
    """

    limit: Limit

    def __or__(self, other: Generator[GenGenT, *OtherGenTs]) -> Generator[GenT, *GenTs, GenGenT, *OtherGenTs]:
        """Combine this generator with another to return multiple different
        results.
        """
        raise NotImplementedError

    @overload
    def __aiter__(self: Generator[GenT]) -> AsyncIterator[GenT]: ...
    @overload
    def __aiter__(self: Generator[GenT, *GenTs]) -> Never: ...
    def __aiter__(self) -> AsyncIterator:
        """Asynchronously iterate through this generator, fetching dynamically.
        Not supported by multi-generators.
        """
        raise NotImplementedError

    async def fetchall(self) -> dict[GenT, dict[str, Any]]:
        """Fetch all results now, making whatever requests necessary.
        This is the only supported way to get your data for multi-generators.
        """
        # this type signature is in lieu of a PEP to re-add Union[*GenTs]
        raise NotImplementedError

class GeneratedGenerator(Generator[GenT, *GenTs]):
    """Second-order smart generator. |noinit| See :class:`Generator`."""

    def __or__(self, other: GeneratedGenerator[GenT, *OtherGenTs]
               ) -> GeneratedGenerator[GenT, *GenTs, *OtherGenTs]:
        raise NotImplementedError

    @overload
    def __aiter__(self: GeneratedGenerator[GenT, GenGenT]) -> AsyncIterator[tuple[GenT, GenGenT]]: ...
    @overload
    def __aiter__(self: GeneratedGenerator[GenT, *GenTs]) -> Never: ...
    def __aiter__(self) -> AsyncIterator:
        raise NotImplementedError

class PageGenerator(_PageProps, Generator['page.Page']):
    """First-order mono-generator of :class:`~page.Page` instances. |noinit|"""

class OnePageGenerator(PageGenerator):
    pass

class CategoryGenerator(_CategoryProps, Generator['page.Category']):
    """First-order mono-generator of :class:`~page.Category` instances. |noinit|
    Includes :class:`PageGenerator` methods.
    """

class OneCategoryGenerator(CategoryGenerator):
    pass

class FileGenerator(_FileProps, Generator['page.File']):
    """First-order mono-generator of :class:`~page.File` instances. |noinit|
    Includes :class:`PageGenerator` methods.
    """

class OneFileGenerator(FileGenerator):
    pass

class TemplateGenerator(_TemplateProps, Generator['page.Template']):
    """First-order mono-generator of :class:`~page.Template` instances. |noinit|
    Includes :class:`PageGenerator` methods.
    """

class OneTemplateGenerator(TemplateGenerator):
    pass

class UserGenerator(Generator['user.User']):
    """First-order mono-generator of :class:`~user.User` instances. |noinit|"""

class OneUserGenerator(UserGenerator):
    pass

class RecentChangeGenerator(Generator['misc.RecentChange']):
    """First-order mono-generator of :class:`misc.RecentChange` instances.
    |noinit| Has no methods (the ``recentchanges`` generator can only generate
    page titles or revision IDs).
    """
