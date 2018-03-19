from unittest import TestCase
from sys import version_info
import mw_api_client as mw

if version_info[0] > 2:
    basestring = str

WP = mw.Wiki('https://en.wikipedia.org/w/api.php', 'Test suite')
class TestEdit(TestCase):
    def test_revisions(self):
        sandbox = WP.page('Project:Sandbox')
        for rev in sandbox.revisions(limit=10, rvprop='content'):
            self.assertTrue(isinstance(rev.content, basestring))
    def test_read_is_string(self):
        sandbox = WP.page('Project:Sandbox')
        content = sandbox.read()
        self.assertTrue(isinstance(content, basestring))
    def test_edit_success(self):
        wp = mw.Wiki('https://en.wikipedia.org/w/api.php', 'Automated testing')
        sandbox = wp.page('Project:Sandbox')
        result = sandbox.edit(sandbox.read() + '\n\nTesting edit',
                              'Testing API edit')
        self.assertTrue(result['edit']['result'] == 'Success')
    def test_missing_page(self):
        nonexistant = WP.page('asdfasdfasdfasdfasdfasdfsadfhjklhjklhkjhjkhjkh')
        nonexistant.info()
        self.assertTrue(hasattr(nonexistant, 'missing'))
    def test_user_contribs(self):
        jimbo = WP.user('Jimbo Wales')
        for rev in jimbo.contribs(limit=10):
            self.assertTrue(isinstance(rev, mw.Revision))
