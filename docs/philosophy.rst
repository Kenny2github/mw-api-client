Design philosophy
=================

This page outlines the high-level design philosophy of the current version of the project. Occasional comparison is made to previous versions of the project.

Lazy fetching to the max
~~~~~~~~~~~~~~~~~~~~~~~~

As **few API requests** should be made as possible.

Only request in async methods
-----------------------------

Previous versions of the project provided the occasional :class:`property` that would make an API request (such as ``Page.content`` which called and cached ``Page.read()``). For the current version, all API requests **must happen in methods**.

Additionally, only methods which actually **require an API request** will be ``async`` methods. Other methods which only act on data in memory will be regular methods.

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

This *does* mean that more than one request may be made when only one might be strictly necessary. Combining this principle with the previous three means that any ``async`` method is an entry into an unlimited number of API requests, but those requests will be combined where possible, and caches used where sensible or else populated where available.

Ease of use over completeness
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Previous versions of the project were hampered and overcomplicated by a desire to support every action achievable using the API. For the current version, **fewer API features will be supported** initially, if ever, as previous versions. Instead, the design will focus on being easy to use and intuitive.

That said, any feature that someone can demonstrate they actually used in the previous version is guaranteed to be implemented at some point, though likely not in the same form.

No simple map to API
--------------------

Previous versions of the project attempted to maintain a certain isomorphism between the library structure and the structure of the action API. While the API structure is a useful starting point, **no guarantees are made** that the structure of the current version of the project will resemble that of the API.

No deprecated features
----------------------

Features of the API **deprecated by MediaWiki shall not be supported**, unless no method exists to perform the same action.

Resemble human user
-------------------

The design of the project shall strive to make accomplishing tasks resemble the way a human user would do it, unless:

* The task is not accomplishable by a human user;
* The way a human user would do it is more tedious than necessary for a bot; or
* A bot would likely not be allowed to do it that way.

Complete type-correctness
~~~~~~~~~~~~~~~~~~~~~~~~~

This project was originally started during an era when Python 2/3 compatibility was important, and before type hinting was widely adopted. It is important now to ensure that **complete type hints are provided** and that the code is internally type-correct. VSCode's Pylance extension is the source of truth on this matter, but correctness with other checkers will be ensured on a best-effort basis.

No lint
-------

Previous versions of this project placed great emphasis on passing Pylint with 10.00/10.00; however, that required exceptions to certain rules and artificially restricting functionality (especially things like "too many arguments"). This project relies only on type checking for static analysis; **lint shall not determine functionality**.

.. _generators: https://www.mediawiki.org/wiki/API:Generators
