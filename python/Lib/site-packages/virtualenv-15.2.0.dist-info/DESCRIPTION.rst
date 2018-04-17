Virtualenv
==========

`Mailing list <http://groups.google.com/group/python-virtualenv>`_ |
`Issues <https://github.com/pypa/virtualenv/issues>`_ |
`Github <https://github.com/pypa/virtualenv>`_ |
`PyPI <https://pypi.python.org/pypi/virtualenv/>`_ |
User IRC: #pypa
Dev IRC: #pypa-dev

Introduction
------------

``virtualenv`` is a tool to create isolated Python environments.

The basic problem being addressed is one of dependencies and versions,
and indirectly permissions. Imagine you have an application that
needs version 1 of LibFoo, but another application requires version
2. How can you use both these applications?  If you install
everything into ``/usr/lib/python2.7/site-packages`` (or whatever your
platform's standard location is), it's easy to end up in a situation
where you unintentionally upgrade an application that shouldn't be
upgraded.

Or more generally, what if you want to install an application *and
leave it be*?  If an application works, any change in its libraries or
the versions of those libraries can break the application.

Also, what if you can't install packages into the global
``site-packages`` directory?  For instance, on a shared host.

In all these cases, ``virtualenv`` can help you. It creates an
environment that has its own installation directories, that doesn't
share libraries with other virtualenv environments (and optionally
doesn't access the globally installed libraries either).

.. comment: 

Release History
===============

15.2.0 (2018-03-21)
-------------------

* Upgrade setuptools to 39.0.1.

* Upgrade pip to 9.0.3.

* Upgrade wheel to 0.30.0.


15.1.0 (2016-11-15)
-------------------

* Support Python 3.6.

* Upgrade setuptools to 28.0.0.

* Upgrade pip to 9.0.1.

* Don't install pre-release versions of pip, setuptools, or wheel from PyPI.


`Full Changelog <https://virtualenv.pypa.io/en/latest/changes.html>`_.

