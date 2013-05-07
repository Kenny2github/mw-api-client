A really simple MediaWiki API client for the Scratch Wiki.

Can:

  * read pages
  * edit pages
  * list pages in category
  * list page backlinks ("what links here")
  * list page transclusions

Requires the `requests` library.

http://wiki.scratch.mit.edu/


Example Usage
=============

Get a page::

    wiki = ScratchWiki()

    wiki.login("blob8108", password)

    sandbox = wiki.page("User:Blob8108/Sandbox")

Edit page:

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

    target_pages = wiki.transclusions("Template:unreleased")

    # Sort by title because it's prettier that way
    target_pages.sort(key=lambda x: x.title)
    
    # Main namespace only
    target_pages = [p for p in target_pages if p.query_info()['ns'] == 0]
    
    for page in target_pages:
        page.replace("{{unreleased}}", "")


Made by ~blob8108.

MIT Licensed.
