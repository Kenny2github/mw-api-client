from __future__ import print_function
from setuptools import setup
from re import match, S

with open('mw_api_client\\__init__.py', 'r') as f:
    longdesc = match('^"""(.*?)"""', f.read(), S).group(1)
with open('README.rst', 'w') as f2:
    f2.write(longdesc)

setup(
    name="mw-api-client",
    version="3.0.0rc1",
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
