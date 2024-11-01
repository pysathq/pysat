#!/usr/bin/env python
#-*- coding:utf-8 -*-
##
## genpatches.py
##
##  Created on: Dec 2, 2019
##      Author: Rüdiger Jungbeck
##      E-mail: ruediger.jungbeck@rsj.de
##

#
#==============================================================================
import argparse
import os
import contextlib
import platform
import shutil
import glob
import prepare


# solvers to install
#==============================================================================
to_install = ['cadical103', 'cadical153', 'gluecard30', 'gluecard41',
              'glucose30', 'glucose41', 'glucose421', 'kissat4', 'lingeling', 
              'maplechrono', 'maplecm', 'maplesat', 'mergesat3', 'minicard',
              'minisat22', 'minisatgh' ]


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
def execute(cmd):
    if platform.system() == 'Windows':
        cmd = 'wsl ' + cmd
    print(cmd)

    os.system(cmd)


#
#==============================================================================
def main():
    parser = argparse.ArgumentParser(description='Diff Generator',
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parms = parser.parse_args()

    shutil.rmtree('build/solvers', ignore_errors=True)

    file_types = ['*.obj', '*.o', '*.a'] # *.o and *.a are required for Glucose421
    with chdir('solvers'):
        for solver in to_install:
            with chdir(solver):
                for ft in file_types:
                    for filename in glob.glob("**/" + ft, recursive = True):
                        os.unlink(filename)

    shutil.copytree('solvers', 'build/solvers')

    for solver in to_install:
        print('preparing {0}'.format(solver))

        with chdir('build'):

            prepare.download_archive(prepare.sources[solver])
            prepare.extract_archive(prepare.sources[solver][-1], solver)
            prepare.adapt_files(solver)

        execute('diff -Naur build/solvers/%s solvers/%s > solvers/patches/%s.patch' % (solver, solver, solver,))


#
#==============================================================================
if __name__ == '__main__':
    main()
