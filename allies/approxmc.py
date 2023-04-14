#!/usr/bin/env python
#-*- coding:utf-8 -*-
##
## approxmc.py
##
##  Created on: Apr 14, 2023
##      Author: Mate Soos
##      E-mail: soos.mate@gmail.com
##

"""
    ===============
    List of classes
    ===============

    .. autosummary::
        :nosignatures:

        Counter

    ==================
    Module description
    ==================

    Some description. Consult examples/*.py to see how this could be done. :-)

    ==============
    Module details
    ==============
"""

#
#==============================================================================
from __future__ import print_function

# we need pyapproxmc to be installed:
pyapproxmc_present = True
try:
    from pyapproxmc import Counter as AppCounter
except ImportError:
    pyapproxmc_present = False


#
#==============================================================================
class Counter(object):
    """
        Class doc-string.
    """

    def __init__(self, formula=None, some_other_arguments):
        """
            Constructor.
        """

        assert pyapproxmc_present, 'Package \'pyapproxmc\' is unavailable. Check your installation.'

        self.counter = AppCounter(...)

    def __del__(self):
        """
            Destructor.
        """

        if self.counter:
            self.counter... # calling destructor
            self.counter = None

    def some_method(self):
        """
            Method
        """

        pass


#
#==============================================================================
if __name__ == '__main__':
    pass
