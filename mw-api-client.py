"""
A really simple MediaWiki API client.

Can:

  * read pages
  * edit pages
  * list pages in category
  * list page backlinks ("what links here")
  * list page transclusions

Requires the `requests` library.

http://www.mediawiki.org/


Example Usage
=============

Get a page::

    wiki = Wiki("https://en.wikipedia.org/", "wiki/", "w/api.php")

    wiki.login("kenny2wiki", password)

    sandbox = wiki.page("User:Kenny2wiki/Sandbox")

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

    target_pages = wiki.transclusions("Template:Stub")

    # Sort by title because it's prettier that way
    target_pages.sort(key=lambda x: x.title)
    
    # Main namespace only
    target_pages = [p for p in target_pages if p.query_info()['ns'] == 0]
    
    for page in target_pages:
        page.replace("{{stub}}", "")


Made by Kenny2github, based off of ~blob8108's Scratch Wiki MWAPI client.

MIT Licensed.
"""


from urllib import urlencode
import json
import requests



class WikiError(Exception):
    def __init__(self, error):
        self.info = None
        self.__dict__.update(error)
    
    def __str__(self):
        return self.info

class PermissionDenied(WikiError): pass


ERRORS = {
    'permissiondenied': PermissionDenied,
}



class Page(object):
    def __init__(self, wiki, **data):
        self.wiki = wiki
        self.title = None
        self.__dict__.update(data)
    
    def __repr__(self):
        return "<Page(%s)>" % repr(self.title)
    
    def __unicode__(self):
        return self.title
    
    def query_info(self, **kwargs):
        arguments = dict(
            action = "query",
            titles = self.title,
        )
        arguments.update(kwargs)
        data = self.wiki.request(**arguments)
        page_data = data["query"]["pages"].values()[0]
        return page_data
        
    def read(self):
        data = self.query_info(
            prop = "revisions",
            rvprop = "content",
        )
        return data["revisions"][0]["*"]
        
    def edit_token(self):
        data = self.query_info(
            prop = "info",
            intoken = "edit",
        )
        return data["edittoken"]
    
    def edit(self, content, summary):
        token = self.edit_token()
        
        return self.wiki.post_request(
            action = "edit",
            title = self.title,
            token = token,
            text = content.encode("utf-8"),
            summary = summary,
            bot = 1,
            nocreate = 1,
        )

    def replace(self, old_text, new_text):
        """Replace each occurence of old_text in the page's source with
        new_text.

        """

        if old_text and new_text:
            summary = "Replace %s with %s" % (old_text, new_text)
        elif old_text:
            summary = "Remove %s" % old_text
        else:
            raise ValueError, "Invalid arguments"
        
        content = self.read()
        content = content.replace(old_text, new_text)
        self.edit(content, summary)

    @property
    def url(self):
        return self.wiki.SITE_URL + urlencode({"x": self.title})[2:].replace("%2F", "/")


class Wiki(object):
    USER_AGENT = "PythonBot Kenny2github~~~~ ~blob8108"
    
    def __init__(self, url, site_url, api_url):
        self.cookie = None
        self.URL = url
        self.SITE_URL = self.URL + site_url
        self.API_URL = self.URL + api_url
      
    def request(self, _method="GET", _headers={}, _post=False, **params):
        #arguments = dict(filter(lambda (arg, value): value is not None, arguments.items()))
        params["format"] = "json"
        
        headers = {
            "User-Agent": self.USER_AGENT,
        }
        headers.update(_headers)

        if self.cookie:
            headers['Cookie'] = self.cookie

        method = "GET"
        if _post:
            method = "POST"

        if _post:
            r = requests.post(self.API_URL, data=params, headers=headers)
        else:
            r = requests.get(self.API_URL, params=params, headers=headers)

        assert r.ok

        self.cookie = r.headers.get("set-cookie", self.cookie)
    
        if 'error' in r.json():
            error = r.json()['error']
            error_code = error['code']
            if error_code in ERRORS:
                error_cls = ERRORS[error_code]
            else:
                raise WikiError(error)
            raise error_cls(error)
    
        return r.json()
    
    def post_request(self, **params):
        return self.request(_post=True, **params)
    

    ## Wiki API ##
 
    def login(self, username, password):
        # Seems broken -- maybe API login is disabled?
        arguments = dict(
            action = "login",
            lgname = username,
            lgpassword = password,
        )
        data = self.post_request(**arguments)["login"]
        
        if data["result"] == "NeedToken":
            arguments["lgtoken"] = data["token"]
            data = self.post_request(**arguments)["login"]

            if data["result"] == "Success":
                prefix = data["cookieprefix"]
                cookie_vars = {
                    prefix + "UserName": data["lgusername"],
                    prefix + "UserID":  data["lguserid"],
                    prefix + "Token": data["lgtoken"],
                }

                for (name, value) in cookie_vars.items():
                    self.cookie = urlencode({name: value}) + "; " + self.cookie
        return data

    def page(self, title):
        if isinstance(title, Page):
            return title
        return Page(self, title=title)
    
    def category_members(self, title, limit="max"):
        if not title.startswith("Category:"):
            title = "Category:" + title
        
        start_from = None
        while 1:
            data = self.request(
                action = "query",
                list = "categorymembers",
                cmtitle = title,
                cmlimit = limit,
                cmcontinue = start_from,
            )
            for page in data["query"]["categorymembers"]:
                yield Page(self, **page)
            
            if "query-continue" in data:
                start_from = data["query-continue"]["categorymembers"]["cmcontinue"]
            else:
                break

    def backlinks(self, page, limit="max"):
        page = self.page(page)
 
        start_from = None
        while 1:
            data = self.request(
                action = "query",
                list = "backlinks",
                bllimit = limit,
                bltitle = page.title,
                blcontinue = start_from,
            )
            for page_data in data["query"]["backlinks"]:
                yield Page(self, **page_data)
            
            if "query-continue" in data:
                start_from = data["query-continue"]["backlinks"]["blcontinue"]
            else:
                break

    def transclusions(self, template_page, limit="max"):
        page = self.page(template_page)
 
        start_from = None
        while 1:
            data = self.request(
                action = "query",
                list = "embeddedin",
                eilimit = limit,
                eititle = page.title,
                eicontinue = start_from,
            )
            for page_data in data["query"]["embeddedin"]:
                yield Page(self, **page_data)
            
            if "query-continue" in data:
                start_from = data["query-continue"]["embeddedin"]["eicontinue"]
            else:
                break


