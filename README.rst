A really simple MediaWiki API client.

Can:

* read pages
* edit pages
* list pages in category
* list page backlinks ("what links here")
* list page transclusions

Requires the ``requests`` library.

http://www.mediawiki.org/


Example Usage
=============

Get a page::

    wiki = Wiki()

    wiki.login("kenny2wiki", password)

    sandbox = wiki.page("User:Kenny2wiki/Sandbox")

Edit page::

    # Get the page
    contents = sandbox.read()

    # Change
    contents += "\n This is a test!"
    summary = "Made a test edit"

    # Submit
    sandbox.edit(contents, summary)

List pages in category::

    for page in wiki.category_members("Redirects"):
        print page.title

Remove all uses of a template::

    target_pages = wiki.transclusions("Template:Stub")

    # Sort by title because it's prettier that way
    target_pages.sort(key=lambda x: x.title)
    
    # Main namespace only
    target_pages = [p for p in target_pages if p.query_info()['ns'] == 0]
    
    for page in target_pages:
        page.replace("{{stub}}", "")


Made by Kenny2github, based on ~blob8108's MWAPI client for the Scratch Wiki.

MIT Licensed.
