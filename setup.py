from setuptools import setup
from mw_api_client import __doc__ as mwapi_doc

with open('README.rst', 'w') as f:
    f.write(mwapi_doc)
    longdesc = mwapi_doc

setup(
    name="mw-api-client",
    version="2.0.0",
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
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.6'
    ],
    keywords='mediawiki api requests',
    py_modules=['mw_api_client'],
    install_requires='requests',
    python_requires='>=2.7',
)
