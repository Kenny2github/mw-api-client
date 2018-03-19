from __future__ import print_function
import os
from setuptools import setup, Command
from re import match, S

with open('mw_api_client\\__init__.py', 'r') as f:
    longdesc = match('^"""(.*?)"""', f.read(), S).group(1)
with open('README.rst', 'w') as f2:
    f2.write(longdesc)

class PylintCommand(Command):
    user_options = [('rcfile', 'r', 'Other pylint rcfile to use',)]
    def initialize_options(self):
        self.pylint_rcfile = ''

    def finalize_options(self):
        if self.pylint_rcfile:
            assert os.path.exists(self.pylint_rcfile), \
                   'Specified config not found!'

    def run(self):
        command = 'python -m pylint '
        if self.pylint_rcfile:
            command += '--rcfile=' + self.pylint_rcfile + ' '
        status = 'OK'
        for pyfile in os.listdir('mw_api_client'):
            if pyfile.endswith('.py'):
                if os.system(command + 'mw_api_client\\' + pyfile) != 0:
                    status = 'FAIL'
        print()
        print(status)

setup(
    cmdclass={'pylint': PylintCommand},
    name="mw-api-client",
    version="3.0.0a2",
    description="A simple MediaWiki client.",
    long_description=longdesc,
    url="https://github.com/Kenny2github/mw-api-client",
    author="Ken Hilton",
    license="MIT",
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content :: Wiki',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.6'
    ],
    keywords='mediawiki api requests',
    packages=['mw_api_client'],
    install_requires='requests',
    python_requires='>=2.7',
    test_suite='nose.collector',
    tests_require=['nose'],
)
