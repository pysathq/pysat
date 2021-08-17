#!/usr/bin/env python
#-*- coding:utf-8 -*-
##
## __init__.py
##
##  Created on: Mar 4, 2017
##      Author: Alexey S. Ignatiev
##      E-mail: aignatiev@ciencias.ulisboa.pt
##

# current version
#==============================================================================
VERSION = (0, 1, 7, "dev", 10)


# PEP440 Format
#==============================================================================
__version__ = "%d.%d.%d.%s%d" % VERSION if len(VERSION) == 5 else \
              "%d.%d.%d" % VERSION


# all submodules
#==============================================================================
__all__ = ['card', 'formula', 'pb', 'solvers']
