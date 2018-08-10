============
Installation
============

There are several ways to install PySAT. At this point, either way assumes you
are using a POSIX-compliant operating system with GNU `make
<https://www.gnu.org/software/make/>`__ and `patch
<http://savannah.gnu.org/projects/patch/>`__ installed and available from the
command line. Installation also relies on a C/C++ compiler supporting C++11,
e.g. `GCC <https://gcc.gnu.org/>`__ or `Clang <https://clang.llvm.org/>`__, as
well as the ``six`` `Python package <https://pypi.org/project/six/>`__.

Note that PySAT was not tested on the Microsoft Windows platform, and so *it is
not yet supported*. We are working on resolving this issue but your input may
be needed.

Once all the prerequisites are installed, the simplest way to get and start
using PySAT is to install the latest stable release of the toolkit from `PyPI
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
