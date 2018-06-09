============
Installation
============

There are several ways to install PySAT. The simplest way to get and start
using it is to install the latest stable release of the toolkit from `PyPI
<https://pypi.org/>`__:

::

    $ pip install python-sat

Once installed from PyPI, the toolkit at a later stage can be updated in the
following way:

::

    $ pip install -U python-sat

Alternatively, one can clone `the repository
<https://github.com/pysathq/pysat>`__ and execute the following command in the
local copy:

::

    $ python setup.py install

This will install the toolkit into the system's Python path. If another
destination directory is preferred, it can be set by

::

    $ python setup.py install --prefix=<where-to-install>

Both options (i.e. via ``pip`` or ``setup.py``) are supposed to download
and compile all the supported SAT solvers as well as prepare the
installation of PySAT.
