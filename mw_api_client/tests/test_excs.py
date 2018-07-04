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
        sandbox2.edit(sandbox2.read() + 'testing conflict',
                      'testing edit conflict')
        errored = False
        try:
            sandbox1.edit(content1 + 'testing conflicted edit',
                          'testing edit conflict')
        except mw.EditConflict:
            errored = True
        self.assertTrue(errored)
    def test_catch(self):
        """Test using mw.catch to catch specific errors."""
        mainpage = WP.page('Main Page')
        globs = {'errored': False}
        def handler(err):
            """Dummy handler"""
            globs['errored'] = True
            del err
        with mw.catch('protectedpage', handler):
            mainpage.edit('test illegal edit', 'test illegal edit')
        self.assertTrue(globs['errored'])
