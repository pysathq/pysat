#!/usr/bin/env python
#-*- coding:utf-8 -*-
##
## prepare.py
##
##  Created on: Jan 23, 2018
##      Author: Alexey S. Ignatiev
##      E-mail: aignatiev@ciencias.ulisboa.pt
##

#
#==============================================================================
from __future__ import print_function
import datetime
import os
import shutil
import sys
import tarfile
import zipfile

try:  # Python 2
    from urllib import urlopen
except ImportError:  # Python 3
    from urllib.request import urlopen


#
#==============================================================================
sources = {
    'glucose30': ('http://www.labri.fr/perso/lsimon/downloads/softwares/glucose-3.0.tgz', 'solvers/glucose30.tar.gz'),
    'lingeling': ('http://fmv.jku.at/lingeling/lingeling-bbc-9230380-160707-druplig-009.tar.gz', 'solvers/lingeling.tar.gz'),
    'minicard': ('https://github.com/liffiton/minicard/archive/v1.2.tar.gz', 'solvers/minicard.tar.gz'),
    'minisat22': ('http://minisat.se/downloads/minisat-2.2.0.tar.gz', 'solvers/minisat22.tar.gz'),
    'minisatgh': ('https://github.com/niklasso/minisat/archive/master.zip', 'solvers/minisatgh.zip')
}

#
#==============================================================================
to_extract = {
    'glucose30': [],
    'lingeling': ['druplig-009.zip', 'lingeling-bbc-9230380-160707.tar.gz'],
    'minicard': [],
    'minisat22': [],
    'minisatgh': []
}

#
#==============================================================================
to_move = {
    'glucose30': [],
    'lingeling': [
        ('druplig-009/druplig.c', 'druplig.c'),
        ('druplig-009/druplig.h', 'druplig.h'),
        ('lingeling-bbc-9230380-160707/lglconst.h', 'lglconst.h'),
        ('lingeling-bbc-9230380-160707/lglib.c', 'lglib.c'),
        ('lingeling-bbc-9230380-160707/lglib.h', 'lglib.h'),
        ('lingeling-bbc-9230380-160707/lgloptl.h', 'lgloptl.h'),
        ('lingeling-bbc-9230380-160707/lglopts.c', 'lglopts.c'),
        ('lingeling-bbc-9230380-160707/lglopts.h', 'lglopts.h')
    ],
    'minicard': [
        ('core', '_core'),
        ('minicard', 'core')
    ],
    'minisat22': [],
    'minisatgh': [
        ('minisat/core', 'core'),
        ('minisat/mtl', 'mtl'),
        ('minisat/utils', 'utils')
    ]
}

#
#==============================================================================
to_remove = {
    'glucose30': [
        'core/Dimacs.h',
        'core/Main.cc',
        'core/Makefile',
        'mtl/config.mk',
        'mtl/template.mk',
        'simp',
        'utils/Makefile'
    ],
    'lingeling': [
        'druplig-009',
        'druplig-009.zip',
        'lingeling-bbc-9230380-160707',
        'lingeling-bbc-9230380-160707.tar.gz',
        'extract-and-compile.sh',
        '.tar.gz',
        'README'
    ],
    'minicard': [
        '_core',
        'encodings',
        'minicard_encodings',
        'minicard_simp_encodings',
        'tests',
        'core/Dimacs.h',
        'core/Main.cc',
        'core/Makefile',
        'core/opb.h',
        'mtl/config.mk',
        'mtl/template.mk',
        'utils/Makefile',
        'LICENSE',
        'README',
        '.gitignore'
    ],
    'minisat22': [
        'core/Dimacs.h',
        'core/Main.cc',
        'core/Makefile',
        'doc',
        'mtl/config.mk',
        'mtl/template.mk',
        'simp',
        'utils/Makefile',
        'LICENSE',
        'README'
    ],
    'minisatgh': [
        'core/Dimacs.h',
        'core/Main.cc',
        'doc',
        'minisat',
        'CMakeLists.txt',
        'LICENSE',
        'Makefile',
        'README',
        '.gitignore'
    ]
}


#
#==============================================================================
def do(to_install):
    """
        Prepare all solvers specified in the command line.
    """

    for solver in to_install:
        print('preparing {0}'.format(solver))

        download_archive(*sources[solver])
        extract_archive(sources[solver][1], solver)
        adapt_files(solver)
        patch_solver(solver)
        compile_solver(solver)


#
#==============================================================================
def download_archive(url, save_to):
    """
        Downloads an archive and saves locally (taken from PySMT).
    """

    # first attempt to get a response
    response = urlopen(url)

    # handling redirections
    u = urlopen(response.geturl())

    meta = u.info()
    if meta.get('Content-Length') and len(meta.get('Content-Length')) > 0:
        filesz = int(meta.get('Content-Length'))
        if os.path.exists(save_to) and os.path.getsize(save_to) == filesz:
            print('not downloading {0} since it exists locally'.format(save_to))
            return

        print('downloading: {0} ({1} bytes)...'.format(save_to, filesz), end=' ')
        with open(save_to, 'wb') as fp:
            block_sz = 8192
            count = 0
            while True:
                buff = u.read(block_sz)
                if not buff:
                    break
                fp.write(buff)

            print('done')
    else:
        assert 0, 'something went wrong -- cannot download {0}'.format(save_to)


#
#==============================================================================
def extract_archive(archive, solver, put_inside = False):
    """
        Unzips/untars a previously downloaded archive file.
    """

    print('extracting {0}'.format(archive))
    root = os.path.join('solvers', solver if put_inside else '')

    if archive.endswith('.tar.gz'):
        if os.path.exists(archive[:-7]):
            shutil.rmtree(archive[:-7])

        tfile = tarfile.open(archive, 'r:gz')
        tfile.extractall(root)
        directory = tfile.getnames()[0]
    elif archive.endswith('.zip'):
        if os.path.exists(archive[:-4]):
            shutil.rmtree(archive[:-4])

        myzip = zipfile.ZipFile(archive, 'r')
        myzip.extractall(root)
        directory = myzip.namelist()[0]
        myzip.close()

    if not put_inside:
        if os.path.exists(os.path.join('solvers', solver)):
            shutil.rmtree(os.path.join('solvers', solver))

        shutil.move(os.path.join('solvers', directory), os.path.join('solvers', solver))


#
#==============================================================================
def adapt_files(solver):
    """
        Rename and remove files whenever necessary.
    """

    print("adapting {0}'s files".format(solver))
    root = os.path.join('solvers', solver)

    for arch in to_extract[solver]:
        arch = os.path.join(root, arch)
        extract_archive(arch, solver, put_inside=True)

    for fnames in to_move[solver]:
        old = os.path.join(root, fnames[0])
        new = os.path.join(root, fnames[1])
        os.rename(old, new)

    for f in to_remove[solver]:
        f = os.path.join(root, f)
        if os.path.isdir(f):
            shutil.rmtree(f)
        else:
            os.remove(f)


#
#==============================================================================
def patch_solver(solver):
    """
        Applies a patch to a given solver.
    """

    print('patching {0}'.format(solver))
    os.system('patch -p0 < solvers/patches/{0}.patch'.format(solver))


#
#==============================================================================
def compile_solver(solver):
    """
        Compiles a given solver as a library.
    """

    print('compiling {0}'.format(solver))
    os.system('cd solvers/{0} && make && cd ../..'.format(solver))
