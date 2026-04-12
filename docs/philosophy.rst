Design philosophy
=================

This page outlines the high-level design philosophy of the current version of the project. Occasional comparison is made to previous versions of the project.

Lazy fetching to the max
~~~~~~~~~~~~~~~~~~~~~~~~

As **few API requests** should be made as possible.

Only request in async methods
-----------------------------

Previous versions of the project provided the occasional :class:`property` that would make an API request (such as ``Page.content`` which called and cached ``Page.read()``). For the current version, all API requests **must happen in methods**.

Additionally, only methods which actually **require an API request** are be ``async`` methods. Other methods which only act on data in memory are regular methods.

Combine requests where possible
-------------------------------

To further the goal of fewest requests, **requests should be combined** into single large requests where possible - either by design, or at least in a way easily leveragable by the user - such as by using `generators`_.

Cache results where sensible
----------------------------

To further the goal of fewest requests, **requested data should be cached in memory** and reused thence where sensible. "Sensible" means:

* There are usually more requests for that data than there are modifications (such as page content); *and*
* The use case doesn't need to ensure the data is current by nature (e.g. recent changes).

"Might as well" principle
-------------------------

With all of the above said, if a request must be made, we **"might as well" fetch as much metadata as we can**.

This does not mean fetching more entries of a stream than requested (there are rate limit and performance implications), but rather all data available for each entry (e.g. all ``rvprops``).

This *does* mean that more than one request may be made when only one might be strictly necessary. Combining this principle with the previous three means that any ``async`` method is a gateway into an unlimited number of API requests, but those requests are combined where possible, and caches used where sensible or else populated where available.

Compatibility or lack thereof
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This project's roots are in `scratch-wiki-client`_ by tjvr (f.k.a. blob8108), which was made with only the Scratch Wiki in mind, in an era when it was stuck on MediaWiki 1.22 with no upgrade in sight. It was then refined by AbyxDev (a.k.a. Kenny2github) to be a little more SW-agnostic, but development was still mostly centered around it and fairly closely tracked its series of MW version upgrades.

For the current version, the scope is more focused and MediaWiki compatibility is taken more seriously.

Ease of use over completeness
-----------------------------

Previous versions of the project were hampered and overcomplicated by a desire to support every action achievable using the API. For the current version, **fewer API features are supported** than in previous versions. Instead, the design focuses on being easy to use and intuitive.

That said, any feature that someone can demonstrate they actually used in the previous version is guaranteed to be implemented at some point, though likely not in the same form.

No simple map to API
--------------------

Previous versions of the project attempted to maintain a certain isomorphism between the library structure and the structure of the action API. While the API structure is a useful starting point, **no guarantees are made** that the structure of the current version of the project will resemble that of the API.

Only stable features
--------------------

Features of the API **deprecated by MediaWiki are not supported**, unless there is a desire to support the underlying action and no non-deprecated method exists to perform it.

Features of the API which are **experimental or incomplete are not supported** until they are stable and complete. Notably, as of MediaWiki 1.44.0, revision slots can only be *read*, but not *edited*, through the API. As such, revision slots are an *incomplete* feature and this project will not support accessing slots other than the ``main`` slot.

Version policy
--------------

- The project only supports the **latest currently-supported LTS versions of MediaWiki**.
	- To reflect this, the second component of each release's version number matches that of the MediaWiki version it supports, i.e. release ``4.43.2.3`` supports the version of MediaWiki 1.43 which is newest as of the ``2.3`` release.
- The third component of the version number is incremented when a feature is added or newly supported, *or* when a breaking change is made (including removing/unsupporting features).
	- This is intentional to force anyone who wishes to use new features to bring their code up to date in the process.
	- That said, **breaking changes will be preceded by at least two bugfix releases** in which the use of the to-be-broken feature is deprecated.
	- This also means there is no limit to the changes that may be made, breaking or otherwise, to support a new LTS version of MediaWiki.
- The fourth component of the version number is incremented when a change is made that does not fall into the above categories, including bugfixes.
	- A change in solely this component is the only change guaranteed to be backwards compatible.
	- One last bugfix release may be made after the corresponding LTS version reaches EOL, containing only fixes actually implemented but pending release.
- The project's **Python version support** is tied to the `MediaWiki version lifecycle`_ and the `Python version lifecycle`_.
	- The maximum Python version is the newest version of Python released before the project's corresponding MediaWiki LTS version goes EOL.
	- The minimum Python version is the oldest version still in the "bugfix" phase as of the first release of the project's corresponding MediaWiki LTS version, or a newer version if new Python features are needed/wanted to support a particular MediaWiki release.

.. mermaid:: versioning.mmd

Resemble human user
-------------------

The design of the project strives to make accomplishing tasks resemble the way a human user would do it, unless:

* The task is not accomplishable by a human user;
* The way a human user would do it is more tedious than necessary for a bot; or
* A bot would likely not be allowed to do it that way.

Complete type-correctness
~~~~~~~~~~~~~~~~~~~~~~~~~

This project was originally started during an era when Python 2/3 compatibility was important, and before type hinting was widely adopted. It is important now to ensure that **complete type hints are provided** and that the code is internally type-correct. VSCode's Pylance extension is the source of truth on this matter, but correctness with other checkers will be ensured on a best-effort, as-reported basis.

No lint
-------

Previous versions of this project placed great emphasis on passing Pylint with 10.00/10.00; however, that required exceptions to certain rules and artificially restricting functionality (especially things like "too many arguments"). This project relies only on type checking for static analysis; **lint does not determine functionality**.

.. _generators: https://www.mediawiki.org/wiki/API:Generators
.. _scratch-wiki-client: https://github.com/tjvr/scratch-wiki-client
.. _MediaWiki version lifecycle: https://www.mediawiki.org/wiki/Version_lifecycle
.. _Python version lifecycle: https://peps.python.org/pep-0602/
