
A really simple MediaWiki API client.

Can use most MediaWiki API modules.

Requires the ``requests`` library.

http://www.mediawiki.org/

Installation
============

To install the latest stable version::

    pip install -U mw-api-client

To install the latest development (likely unstable) version::

    git clone https://github.com/Kenny2github/mw-api-client.git
    cd mw-api-client
    python setup.py install

Example Usage
=============

.. code-block:: python

    import mw_api_client as mw

Edit page:

.. code-block:: python

    wp = mw.Wiki("https://en.wikipedia.org/w/api.php", "MyCoolBot/0.0.0")

    await wp.login("AbyxDev", password)

    sandbox = wp.page("User:AbyxDev/sandbox")

    # Get the page
    contents = sandbox.read()

    # Change
    contents += "\nThis is a test!"
    summary = "Made a test edit"

    # Submit
    await sandbox.edit(contents, summary)

For a more featureful example, see `demo_bot.py`_.

.. _demo_bot.py: docs/_static/demo_bot.py

Credits
=======

Made by Kenny2github, based off of ~blob8108's Scratch Wiki API client.

MIT Licensed.
