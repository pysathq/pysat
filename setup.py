#!/usr/bin/env python
#-*- coding:utf-8 -*-
##
## setup.py
##
##  Created on: Jan 23, 2018
##      Author: Alexey Ignatiev
##      E-mail: alexey.ignatiev@monash.edu
##

#
#==============================================================================
import os
import os.path
import contextlib
import glob

try:
    from setuptools import setup, Extension
    HAVE_SETUPTOOLS = True
except ImportError:
    from distutils.core import setup, Extension
    HAVE_SETUPTOOLS = False

import distutils.command.build
import distutils.command.build_ext
import distutils.command.install

import inspect, os, sys
sys.path.insert(0, os.path.join(os.path.realpath(os.path.abspath(os.path.split(inspect.getfile(inspect.currentframe()))[0])), 'solvers/'))
import platform
import prepare

from pysat import __version__


#
#==============================================================================
@contextlib.contextmanager
def chdir(new_dir):
    old_dir = os.getcwd()
    try:
        os.chdir(new_dir)
        yield
    finally:
        os.chdir(old_dir)


#
#==============================================================================
ROOT = os.path.abspath(os.path.dirname(__file__))

LONG_DESCRIPTION = """
A Python library providing a simple interface to a number of state-of-art
Boolean satisfiability (SAT) solvers and a few types of cardinality and
pseudo-Boolean encodings. The purpose of PySAT is to enable researchers
working on SAT and its applications and generalizations to easily prototype
with SAT oracles in Python while exploiting incrementally the power of the
original low-level implementations of modern SAT solvers.

With PySAT it should be easy for you to implement a MaxSAT solver, an
MUS/MCS extractor/enumerator, or any tool solving an application problem
with the (potentially multiple) use of a SAT oracle.

Details can be found at `https://pysathq.github.io <https://pysathq.github.io>`__.
"""


# solvers to install
#==============================================================================
to_install = ['cadical103', 'cadical153', 'cadical195', 'gluecard30',
              'gluecard41', 'glucose30', 'glucose41', 'glucose421',
              'lingeling', 'maplechrono', 'maplecm', 'maplesat', 'mergesat3',
              'minicard', 'minisat22', 'minisatgh']

# example and allies scripts to install as standalone executables
#==============================================================================
example_scripts = ['bbscan', 'bica', 'fm', 'genhard', 'lbx', 'lsu', 'mcsls',
                   'models', 'musx', 'optux', 'primer', 'rc2']
allies_scripts = ['approxmc', 'unigen']


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
        if platform.system() != 'Windows':
            prepare.do(to_install)

        # now, do standard build
        distutils.command.build.build.run(self)

# same with build_ext
#==============================================================================
class build_ext(distutils.command.build_ext.build_ext):
    """
        Our custom builder class.
    """

    def run(self):
        """
            Download, patch and compile SAT solvers before building.
        """
        # download and compile solvers
        if platform.system() != 'Windows':
            prepare.do(to_install)

        # now, do standard build
        distutils.command.build_ext.build_ext.run(self)


# compilation flags for C extensions
#==============================================================================
compile_flags, cpplib = ['-std=c++11', '-Wall', '-Wno-deprecated'],  ['stdc++']
if platform.system() == 'Darwin':
    compile_flags += ['--stdlib=libc++']
    cpplib = ['c++']
elif platform.system() == 'Windows':
    compile_flags = ['-DNBUILD', '-DNLGLYALSAT' , '/DINCREMENTAL', '-DNLGLOG',
            '-DNDEBUG', '-DNCHKSOL', '-DNLGLFILES', '-DNLGLDEMA', '-I./win']
    cpplib = []


# C extensions: pycard and pysolvers
#==============================================================================
pycard_ext = Extension('pycard',
    sources=['cardenc/pycard.cc'],
    extra_compile_args=compile_flags,
    include_dirs=['cardenc'] ,
    language='c++',
    libraries=cpplib,
    library_dirs=[]
)

pysolvers_sources = ['solvers/pysolvers.cc']

if platform.system() == 'Windows':
    prepare.do(to_install)
    with chdir('solvers'):
        for solver in to_install:
            with chdir(solver):
                for filename in glob.glob('*.c*'):
                    pysolvers_sources += ['solvers/%s/%s' % (solver, filename)]
                for filename in glob.glob('*/*.c*'):
                    pysolvers_sources += ['solvers/%s/%s' % (solver, filename)]
    libraries = []
    library_dirs = []
else:
    libraries = to_install + cpplib
    library_dirs = list(map(lambda x: os.path.join('solvers', x), to_install))

pysolvers_ext = Extension('pysolvers',
    sources=pysolvers_sources,
    extra_compile_args=compile_flags + \
        list(map(lambda x: '-DWITH_{0}'.format(x.upper()), to_install)),
    include_dirs=['solvers'],
    language='c++',
    libraries=libraries,
    library_dirs=library_dirs
)


# finally, calling standard setuptools.setup() (or distutils.core.setup())
#==============================================================================
setup(name='python-sat',
    packages=['pysat', 'pysat.examples', 'pysat.allies'],
    package_dir={'pysat.examples': 'examples', 'pysat.allies': 'allies'},
    version=__version__,
    description='A Python library for prototyping with SAT oracles',
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/x-rst; charset=UTF-8',
    license='MIT',
    license_files=('LICENSE.txt',),
    author='Alexey Ignatiev, Joao Marques-Silva, Antonio Morgado',
    author_email='alexey.ignatiev@monash.edu, joao.marques-silva@univ-toulouse.fr, ajrmorgado@gmail.com',
    url='https://github.com/pysathq/pysat',
    ext_modules=[pycard_ext, pysolvers_ext],
    scripts=['examples/{0}.py'.format(s) for s in example_scripts] + \
            ['allies/{0}.py'.format(s) for s in allies_scripts],
    cmdclass={'build': build},
    install_requires=['six'],
    extras_require = {
        'aiger': ['py-aiger-cnf>=2.0.0'],
        'approxmc': ['pyapproxmc>=4.1.8'],
        'cryptosat': ['pycryptosat>=5.11.18'],
        'pblib': ['pypblib>=0.0.3'],
        'unigen': ['pyunigen>=4.1.20']
    }
)
