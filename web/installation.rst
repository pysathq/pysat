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
Finally, in order to compile "C extensions" included as modules, the installer
requires the headers of `Python <https://www.python.org/>`__ and `zlib
<https://www.zlib.net/>`__. Both can be installed using the standard package
repositories.

Note that although version `0.1.5.dev1` of PySAT brings Microsoft Windows
support, the toolkit was not extensively tested on this system. If you find
out that something is broken on Windows, please, `let us know
<https://github.com/pysathq/pysat/issues>`__. Your input is important.

Also note that using Clang is preferred on MacOS as there may be an issue with
GCC *being unaware of* the command-line option ``--stdlib=libc++``. Clang is
available on MacOS by default. To enforce the installer to use it, you need to
set the environment variable ``CC`` to ``/usr/bin/clang``. For that, do
``export CC=/usr/bin/clang`` if using Bash, or ``setenv CC /usr/bin/clang`` if
using tsch. *This is not needed on Linux!*

Once all the prerequisites are installed, the simplest way to get and start
using PySAT is to install the latest stable release of the toolkit from `PyPI
<https://pypi.org/>`__:

::

    $ pip install python-sat[pblib,aiger]

We encourage you to install the *optional* dependencies `pblib` and `aiger`,
as shown in the previous command. However, if it cannot be done (e.g. if their
installation fails), you can install PySAT with the functionality of `aiger`
and `pblib` disabled:

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
