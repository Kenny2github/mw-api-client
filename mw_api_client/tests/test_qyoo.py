"""Test various aspects of the Wiki."""
from sys import version_info
from unittest import TestCase
import mw_api_client as mw

if version_info[0] > 2:
    basestring = str # pylint: disable=invalid-name

# pylint: disable=protected-access
WP = mw.Wiki('https://en.wikipedia.org/w/api.php', 'Test suite')
class TestQyoo(TestCase):
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
            mw.Queue.frompages(WP, (WP.page('Project:Sandbox'),
                                    'not a Page'))
            self.assertTrue(1 != 1)
        except TypeError:
            self.assertTrue(1 == 1)
    def test_categories(self):
        """Assert Queue.categories returns Pages with Pages."""
        queue = mw.Queue.fromtitles(WP, ('Project:Sandbox', 'Draft:Sandbox'))
        for page in queue.categories(2):
            self.assertTrue(isinstance(page, mw.Page))
            for cat in page.categories:
                self.assertTrue(isinstance(cat, mw.Page))
    def test_contributors(self):
        """Assert Queue.contributors returns Pages with Users."""
        queue = mw.Queue.fromtitles(WP, ('Project:Sandbox', 'Draft:Sandbox'))
        for page in queue.contributors(2):
            self.assertTrue(isinstance(page, mw.Page))
            for user in page.contributors:
                self.assertTrue(isinstance(user, mw.User))
    def test_revisions(self):
        """Assert Queue.revisions returns Pages with Revisions."""
        queue = mw.Queue.fromtitles(WP, ('Project:Sandbox', 'Draft:Sandbox'))
        for page in queue.revisions():
            self.assertTrue(isinstance(page, mw.Page))
            for rev in page.revisions:
                self.assertTrue(isinstance(rev, mw.Revision))
