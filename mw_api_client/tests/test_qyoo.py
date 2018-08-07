"""Test various aspects of the Wiki."""
from sys import version_info
from unittest import TestCase
import mw_api_client as mw

if version_info[0] > 2:
    basestring = str # pylint: disable=invalid-name

WP = mw.Wiki('https://en.wikipedia.org/w/api.php', 'Test suite')
class TestWiki(TestCase):
    """Test the Wiki class."""
    def test_qyoo(self):
        """Assert that creating a Queue initializes it properly."""
        queue = mw.Queue(WP, (WP.page('Project:Sandbox'),
                              WP.page('Draft:Sandbox')))
        for i, thing in enumerate(queue._things):
            self.assertEqual(('Project:Sandbox', 'Draft:Sandbox')[i],
                             thing.title)
    def test_qyoo_fromtitles(self):
        """Assert fromtitles classmethod of Queue works properly."""
        queue = mw.Queue.fromtitles(WP, ('Project:Sandbox', 'Draft:Sandbox'))
        for i, thing in enumerate(queue._things):
            self.assertEqual(('Project:Sandbox', 'Draft:Sandbox')[i],
                             thing.title)
    def test_qyoo_frompages(self):
        """Assert frompages checks type."""
        try:
            queue = mw.Queue.frompages(WP, (WP.page('Project:Sandbox'),
                                        'not a Page'))
            self.assertTrue(False)
        except TypeError:
            self.assertTrue(True)
    def test_contributors(self):
        """Assert Queue.contributors returns Pages with Users."""
        queue = mw.Queue.fromtitles(WP, ('Project:Sandbox', 'Draft:Sandbox'))
        for page in queue.contributors(2):
            self.assertTrue(isinstance(page, Page))
            for user in page.contributors:
                self.assertTrue(isinstance(user, User))
    def test_revisions(self):
        """Assert Queue.revisions returns Pages with Revisions."""
        queue = mw.Queue.fromtitles(WP, ('Project:Sandbox', 'Draft:Sandbox'))
        for page in queue.revisions(2):
            self.assertTrue(isinstance(page, Page))
            for rev in page.revisions:
                self.assertTrue(isinstance(rev, Revision))
