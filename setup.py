#!/usr/bin/env python
#-*- coding:utf-8 -*-
##
## setup.py
##
##  Created on: Jan 23, 2018
##      Author: Alexey S. Ignatiev
##      E-mail: aignatiev@ciencias.ulisboa.pt
##

#
#==============================================================================
import distutils.command.build
import distutils.command.install
from distutils.core import setup, Extension

import inspect, os, sys
sys.path.insert(0, os.path.join(os.path.realpath(os.path.abspath(os.path.split(inspect.getfile(inspect.currentframe()))[0])), 'solvers/'))
import prepare

from pysat import __version__

#
#==============================================================================
ROOT = os.path.abspath(os.path.dirname(__file__))

# solvers to install
#==============================================================================
to_install = ['glucose30', 'lingeling', 'minicard', 'minisat22', 'minisatgh']


# we need to redefine the build command to
# be able to download and compile solvers
#==============================================================================
class build(distutils.command.build.build):
    """
        Our custom builder class.
    """

    def run(self):
        """
            Download, patch and compile SAT solvers before building.
        """

        # download and compile solvers
        prepare.do(to_install)

        # now, do standard build
        distutils.command.build.build.run(self)


# C extensions: pycard and pysolvers
#==============================================================================
pycard_ext = Extension('pycard',
    sources=['cardenc/pycard.cc'],
    extra_compile_args=['-std=c++11', '-Wno-deprecated'],
    include_dirs=['cardenc'] ,
    language='c++',
    libraries=['stdc++'],
    library_dirs=[]
)

pysolvers_ext = Extension('pysolvers',
    sources = ['solvers/pysolvers.cc'],
    extra_compile_args = ['-std=c++11', '-Wno-deprecated'] + \
        list(map(lambda x: '-DWITH_{0}'.format(x.upper()), to_install)),
    include_dirs = ['solvers'],
    language = 'c++',
    libraries = to_install + ['stdc++'],
    library_dirs = list(map(lambda x: os.path.join('solvers', x), to_install))
)


# finally, calling standard distutils.core.setup()
#==============================================================================
setup(name='python-sat',
    packages=['pysat'],
    version=__version__,
    description='A Python library for prototyping with SAT oracles',
    long_description=open(os.path.join(ROOT, 'README.rst')).read(),
    long_description_content_type='text/x-rst; charset=UTF-8',
    license='MIT',
    author='Alexey Ignatiev, Joao Marques-Silva, Antonio Morgado',
    author_email='aignatiev@ciencias.ulisboa.pt, jpms@ciencias.ulisboa.pt, ajmorgado@ciencias.ulisboa.pt',
    url='https://github.com/alexeyignatiev/pysat',
    ext_modules=[pycard_ext, pysolvers_ext],
    cmdclass={'build': build},
    install_requires=['six']
)
