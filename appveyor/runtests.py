#!/usr/bin/env python
#-*- coding:utf-8 -*-
##
## runtests.py
##
##  Created on: Apr 21, 2020
##      Author: Alexey Ignatiev
##      E-mail: alexey.ignatiev@monash.edu
##  Taken from: https://github.com/rjungbeck/pysat/blob/master/runtest.py

#
#==============================================================================
import argparse
import glob
import os
import subprocess
import sys


#
#==============================================================================
def pycall(cmd):
    fullcmd = [sys.executable] + cmd.split()
    cwd = 'tests' if cmd.startswith('-m pytest') else None

    ret = subprocess.call(fullcmd, cwd=cwd)

    if ret not in (0, 5):
        print('{0} returned {1}'.format(cmd, ret))
        raise OSError


#
#==============================================================================
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Install and test wheels build',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--wheels', type=str, default='dist/*.whl', help='Wheel glob')
    parser.add_argument('--test', type=str, default='-m pytest', help='Test command')
    params = parser.parse_args()

    for wheel in glob.glob(params.wheels):
        pycall('-m pip install --upgrade {0}'.format(wheel))

    # pycall(params.test)

    for tfile in glob.glob('tests/*.py'):
        pycall(params.test + ' -v ' + os.path.basename(tfile))

    sys.exit(0)
