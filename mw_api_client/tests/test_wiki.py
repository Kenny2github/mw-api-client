"""Test various aspects of the Wiki."""
from sys import version_info
from unittest import TestCase
import mw_api_client as mw

if version_info[0] > 2:
    basestring = str # pylint: disable=invalid-name

WP = mw.Wiki('https://en.wikipedia.org/w/api.php', 'Test suite')
class TestWiki(TestCase):
    """Test the Wiki class."""
    def test_page(self):
        """Assert that Wiki.page returns a Page."""
        self.assertTrue(isinstance(WP.page('Project:Sandbox'), mw.Page))
    def test_recentchanges(self):
        """Assert that Wiki.recentchanges yields RecentChanges."""
        for change in WP.recentchanges(limit=10):
            self.assertTrue(isinstance(change, mw.RecentChange))
    def test_allpages(self):
        """Assert that Wiki.allpages yields Pages, and contents are strings."""
        for page in WP.allpages(limit=10):
            self.assertTrue(isinstance(page, mw.Page))
            self.assertTrue(isinstance(page.content, basestring))
    def test_token(self):
        """Assert that a recently fetched token checks out ok."""
        token = WP.meta.tokens()
        self.assertTrue(WP.checktoken(token))
    def test_blocks(self):
        """Assert that Wiki.blocks yields block data."""
        for block in WP.blocks(limit=10):
            self.assertTrue(isinstance(block, mw.GenericData))
    def test_random(self):
        """Assert that Wiki.random yields Pages."""
        for page in WP.random(limit=10):
            self.assertTrue(isinstance(page, mw.Page))
