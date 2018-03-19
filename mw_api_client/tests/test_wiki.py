from sys import version_info
from unittest import TestCase
import mw_api_client as mw

if version_info[0] > 2:
    basestring = str

WP = mw.Wiki('https://en.wikipedia.org/w/api.php', 'Test suite')
class TestWiki(TestCase):
    def test_page(self):
        self.assertTrue(isinstance(WP.page('Project:Sandbox'), mw.Page))
    def test_recentchanges(self):
        for change in WP.recentchanges(limit=10):
            self.assertTrue(isinstance(change, mw.RecentChange))
    def test_allpages(self):
        for page in WP.allpages(limit=10):
            self.assertTrue(isinstance(page, mw.Page))
            self.assertTrue(isinstance(page.content, basestring))
    def test_token(self):
        token = WP.meta.tokens()
        self.assertTrue(WP.checktoken(token))
    def test_blocks(self):
        for block in WP.blocks(limit=10):
            self.assertTrue(isinstance(block, dict))
    def test_random(self):
        for page in WP.random(limit=10):
            self.assertTrue(isinstance(page, mw.Page))
