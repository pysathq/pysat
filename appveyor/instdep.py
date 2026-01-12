#!/usr/bin/env python
#-*- coding:utf-8 -*-
##
## instdep.py
##
##  Created on: Apr 19, 2020
##      Author: Alexey Ignatiev
##      E-mail: alexey.ignatiev@monash.edu
##  Taken from: https://github.com/rjungbeck/pysat/blob/master/instdep.py

#
#==============================================================================
import argparse
import os
import platform
import re
import requests
import sys

#
#==============================================================================
suffixes = {
    (2,  7, '32bit'): None,
    (3,  6, '32bit'): 'cp36-cp36m-win32',
    (3,  7, '32bit'): 'cp37-cp37m-win32',
    (3,  8, '32bit'): 'cp38-cp38-win32',
    (3,  9, '32bit'): 'cp39-cp39-win32',
    (3, 10, '32bit'): 'cp310-cp310-win32',
    (3, 11, '32bit'): 'cp311-cp311-win_amd32',
    (3, 12, '32bit'): 'cp312-cp312-win_amd32',
    (3, 13, '32bit'): 'cp313-cp313-win_amd32',
    (3, 14, '32bit'): 'cp314-cp314-win_amd32',
    (2,  7, '64bit'): None,
    (3,  6, '64bit'): 'cp36-cp36m-win_amd64',
    (3,  7, '64bit'): 'cp37-cp37m-win_amd64',
    (3,  8, '64bit'): 'cp38-cp38-win_amd64',
    (3,  9, '64bit'): 'cp39-cp39-win_amd64',
    (3, 10, '64bit'): 'cp310-cp310-win_amd64',
    (3, 11, '64bit'): 'cp311-cp311-win_amd64',
    (3, 12, '64bit'): 'cp312-cp312-win_amd64',
    (3, 13, '64bit'): 'cp313-cp313-win_amd64',
    (3, 14, '64bit'): 'cp314-cp314-win_amd64'
}


#
#==============================================================================
def pycall(cmd):
    fullcmd = sys.executable + ' ' + cmd
    print(fullcmd)
    os.system(fullcmd)


#
#==============================================================================
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Dependency installation',
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--release-url', type=str, default='https://api.github.com/repos/rjungbeck/pypblib/releases/latest',
                        help='Release URL')
    params = parser.parse_args()

    req = requests.get(params.release_url)
    rsp = req.json()

    version = sys.version_info[:2]
    architecture = platform.architecture()[0]
    wheelId = (version[0], version[1], architecture)
    suffix = suffixes[wheelId]

    print('Suffix', suffix)

    for asset in rsp['assets']:
        print(asset['name'])
        # if suffix and suffix in asset['name']:
        #     pycall('-m pip install --upgrade {0}'.format(asset['browser_download_url']))
