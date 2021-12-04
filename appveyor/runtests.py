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
import sys


#
#==============================================================================
def pycall(cmd):
    fullcmd = sys.executable + ' ' + cmd

    # trying to handle the issue of 'pysat.examples' module
    if cmd == '-m pytest':
        fullcmd = 'cd tests && ' + fullcmd

    ret = os.system(fullcmd)

    if ret != 0:
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

    pycall(params.test)

    sys.exit(0)
