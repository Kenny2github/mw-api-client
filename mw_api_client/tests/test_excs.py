"""Test exception handling"""
from unittest import TestCase
import mw_api_client as mw

WP = mw.Wiki('https://en.wikipedia.org/w/api.php')
class TestExcs(TestCase):
    """TestCase class to test exception handling."""
    def test_error(self):
        """Test general WikiError catching."""
        errored = False
        try:
            WP.page('Main Page').edit('unit test', 'unit test')
        except mw.WikiError:
            errored = True
        self.assertTrue(errored)
    def test_conflict(self):
        """Test catching an edit conflict."""
        sandbox1 = WP.page('Project:Sandbox')
        sandbox2 = WP.page('Project:Sandbox')
        content1 = sandbox1.read()
        try:
            sandbox2.edit(sandbox2.read() + 'testing conflict',
                          'testing edit conflict')
        except mw.WikiError.blocked:
            self.skipTest('This IP is blocked from editing')
            return
        errored = False
        try:
            sandbox1.edit(content1 + 'testing conflicted edit',
                          'testing edit conflict')
        except mw.EditConflict:
            errored = True
        self.assertTrue(errored)
    def test_catch(self):
        """Test try/except to catch specific errors."""
        mainpage = WP.page('Main Page')
        errored = False
        try:
            mainpage.edit('test illegal edit', 'test illegal edit')
        except mw.WikiError.protectedpage:
            errored = True
        except mw.WikiError.blocked:
            self.skipTest('This IP is blocked from editing')
            return
        self.assertTrue(errored)
