#!/usr/bin/env python
#-*- coding:utf-8 -*-
##
## _utils.py
##
##  Created on: Nov 27, 2019
##      Author: Alexey S. Ignatiev
##      E-mail: aignatiev@ciencias.ulisboa.pt
##

"""
    ===============
    List of classes
    ===============

    .. autosummary::
        :nosignatures:

        MainThread

    ==================
    Module description
    ==================

    This simple module is supposed to implement auxiliary classes and routines
    that are used by the other (main) modules of PySAT.

    ==============
    Module details
    ==============
"""

#
#==============================================================================
import threading


#
#==============================================================================
class MainThread(object):
    """
        A dummy class for checking whether the current thread is the main one.
        This is currently necessary for proper signal handling when making
        oracle calls and creating cardinality encodings.
    """

    @staticmethod
    def check():
        """
            The actual checker.
        """

        try:  # for Python > 3.4
            res = threading.current_thread() is threading.main_thread()
        except AttributeError:
            res = isinstance(threading.current_thread(), threading._MainThread)

        return res
