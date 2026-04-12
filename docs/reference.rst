mw_api Package Reference
===============================

.. default-domain:: py

.. currentmodule:: mw_api

.. |noinit| replace:: Not meant to be constructed directly.

.. |limit| replace:: :attr:`~mw_api.genr.Generator.limit`

.. |see-limit| replace:: See :attr:`mw_api.genr.Generator.limit`.

.. |key-attr| replace:: is the only data guaranteed to be available on a given instance, which is why it is an attribute and not a :class:`property`. All of the properties raise :exc:`KeyError` if the respective data is not available. Methods in the library that return or generate instances of this class will document what properties they populate, if any.

.. |population| replace:: The respective data can be fetched and/or brought up to date by calling

Wiki class
~~~~~~~~~~

.. autoclass:: Wiki()
	:class-doc-from: class
	:no-show-inheritance:

Exceptions
~~~~~~~~~~

.. autoexception:: APIError()
	:no-show-inheritance:

.. autoexception:: APIWarning()
	:inherited-members: UserWarning

Page classes
~~~~~~~~~~~~

.. autoclass:: Page()
	:inherited-members:
	:no-show-inheritance:

.. autoclass:: TalkPage()
	:inherited-members: Page

.. autoclass:: File()
	:inherited-members: Page

.. autoclass:: Template()
	:inherited-members: Page

.. autoclass:: Category()
	:inherited-members: Page

.. autoclass:: Revision()
	:inherited-members:
	:no-show-inheritance:

User classes
~~~~~~~~~~~~

.. autoclass:: User()
	:no-show-inheritance:

.. autoclass:: CurrentUser()

Multi-stream fetches
~~~~~~~~~~~~~~~~~~~~

.. autoclass:: mw_api.genr.Generator()
	:special-members: __or__, __aiter__

.. autoclass:: mw_api.genr.GeneratedGenerator()
	:special-members: __or__, __aiter__
	:inherited-members: Generic

.. autoclass:: mw_api.genr.PageGenerator()
	:inherited-members: Generator

.. autoclass:: mw_api.genr.CategoryGenerator()
	:inherited-members: _PageProps

.. autoclass:: mw_api.genr.FileGenerator()
	:inherited-members: _PageProps

.. autoclass:: mw_api.genr.TemplateGenerator()
	:inherited-members: _PageProps

.. autoclass:: mw_api.genr.RevisionGenerator()
	:inherited-members: _PageProps

.. autoclass:: mw_api.genr.UserGenerator()
	:inherited-members: Generator

.. autoclass:: mw_api.genr.RecentChangeGenerator()
	:inherited-members: Generator

.. autoclass:: mw_api.genr.LogEntryGenerator()
	:inherited-members: Generator

.. autoclass:: mw_api.genr.ImageInfoGenerator()
	:inherited-members: Generator

.. autoclass:: mw_api.page.Pages()
	:inherited-members:
	:special-members: __aiter__, __or__
	:no-show-inheritance:

Miscellaneous classes
~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: Namespace()
	:no-show-inheritance:

.. autoclass:: RecentChange()
	:no-show-inheritance:

.. autoclass:: LogEntry()
	:no-show-inheritance:

.. autoclass:: ImageInfo()
	:no-show-inheritance:

.. autoclass:: Tag()
	:no-show-inheritance:
