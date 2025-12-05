mw_api Package Reference
===============================

.. default-domain:: py

.. currentmodule:: mw_api

.. |noinit| replace:: Not meant to be constructed directly.

.. |limit| replace:: :attr:`~genr.Generator.limit`

.. |see-limit| replace:: See :attr:`genr.Generator.limit`.

.. |key-attr| replace:: is the only data guaranteed to be available on a given instance, which is why it is an attribute and not a :class:`property`. All of the properties raise :exc:`KeyError` if the respective data is not available. Methods in the library that return or generate instances of this class will document what properties they populate, if any.

.. |population| replace:: The respective data can be fetched and/or brought up to date by calling

Wiki class
~~~~~~~~~~

.. autoclass:: Wiki
	:class-doc-from: class
	:no-show-inheritance:

Exceptions
~~~~~~~~~~

.. autoexception:: APIError
	:no-show-inheritance:

.. autoexception:: APIWarning
	:inherited-members: Exception

Page classes
~~~~~~~~~~~~

.. autoclass:: Page
	:inherited-members:
	:no-show-inheritance:

.. autoclass:: TalkPage
	:inherited-members: Page

.. autoclass:: File
	:inherited-members: Page

.. autoclass:: Template
	:inherited-members: Page

.. autoclass:: Category
	:inherited-members: Page

User classes
~~~~~~~~~~~~

.. autoclass:: User
	:no-show-inheritance:

.. autoclass:: CurrentUser

Multi-stream fetches
~~~~~~~~~~~~~~~~~~~~

.. autoclass:: mw_api.genr.Generator
	:special-members:

.. autoclass:: mw_api.genr.GeneratedGenerator
	:special-members:
	:inherited-members: Generic

.. autoclass:: mw_api.genr.PageGenerator
	:inherited-members: Generator

.. autoclass:: mw_api.genr.CategoryGenerator
	:inherited-members: _PageProps

.. autoclass:: mw_api.genr.FileGenerator
	:inherited-members: _PageProps

.. autoclass:: mw_api.genr.TemplateGenerator
	:inherited-members: _PageProps

.. autoclass:: mw_api.genr.UserGenerator
	:inherited-members: Generator

.. autoclass:: mw_api.page.Pages
	:inherited-members:

Miscellaneous classes
~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: mw_api.misc.Namespace()
	:no-show-inheritance:
