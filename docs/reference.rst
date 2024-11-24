mw_api Package Reference
===============================

.. default-domain:: py

.. currentmodule:: mw_api

.. |noinit| replace:: Not meant to be constructed directly.

Wiki class
~~~~~~~~~~

.. autoclass:: Wiki
	:class-doc-from: class

Exceptions
~~~~~~~~~~

.. autoexception:: APIError

.. autoexception:: APIWarning
	:inherited-members: Exception

Page classes
~~~~~~~~~~~~

.. autoclass:: Page
	:inherited-members:

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
