---
title: Installation
---

There are several ways to install PySAT. At this point, either way
assumes you are using a POSIX-compliant operating system with GNU
[make](https://www.gnu.org/software/make/) and
[patch](http://savannah.gnu.org/projects/patch/) installed and available
from the command line. Installation also relies on a C/C++ compiler
supporting C++11, e.g. [GCC](https://gcc.gnu.org/) or
[Clang](https://clang.llvm.org/), as well as the `six` [Python
package](https://pypi.org/project/six/). Finally, in order to compile
\"C extensions\" included as modules, the installer requires the headers
of [Python](https://www.python.org/) and [zlib](https://www.zlib.net/).
Both can be installed using the standard package repositories.

Note that although version *0.1.5.dev1* of PySAT brings Microsoft Windows
support, the toolkit was not extensively tested on this system. If you find
out that something is broken on Windows, please, [let us
know](https://github.com/pysathq/pysat/issues). Your input is important.

Also note that using Clang is preferred on MacOS as there may be an
issue with GCC *being unaware of* the command-line option
`--stdlib=libc++`. Clang is available on MacOS by default. To enforce
the installer to use it, you need to set the environment variable `CC`
to `/usr/bin/clang`. For that, do `export CC=/usr/bin/clang` if using
Bash, or `setenv CC /usr/bin/clang` if using tsch. *This is not needed
on Linux!*

Once all the prerequisites are installed, the simplest way to get and
start using PySAT is to install the latest stable release of the toolkit
from [PyPI](https://pypi.org/project/python-sat/):[^1]

[^1]: **NOTE:** For some shells, e.g. *zsh*, you may need to put the package
    names into single quotes, i.e. use `pip install
    'python-sat[aiger,approxmc,cryptosat,pblib]'`.

```bash
pip install python-sat[aiger,approxmc,cryptosat,pblib]
```

We encourage you to install the *optional* dependencies *pblib*, *aiger*,
*cryptosat*, and *approxmc*, as shown in the previous command. However, if it
cannot be done (e.g. if their installation fails), you can install PySAT with
the functionality of *aiger*, *approxmc*, *cryptosat*, and *pblib* disabled:

```bash
pip install python-sat
```

Once installed from PyPI, the toolkit at a later stage can be updated in
the following way:

```bash
pip install -U python-sat
```

Alternatively, one can clone [the
repository](https://github.com/pysathq/pysat) and execute the following
command in the local copy:

```bash
python setup.py install
```

This will install the toolkit into the system\'s Python path. If another
destination directory is preferred, it can be set by

```bash
python setup.py install --prefix=<where-to-install>
```

Both options (i.e. via `pip` or `setup.py`) are supposed to download and
compile all the supported SAT solvers as well as prepare the
installation of PySAT.
