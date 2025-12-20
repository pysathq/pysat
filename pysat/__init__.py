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
VERSION = (1, 8, 'dev', 26)


# PEP440 Format
#==============================================================================
__version__ = '%d.%d.%s%d' % VERSION if len(VERSION) == 4 else \
              '%d.%d.%d' % VERSION


# all submodules
#==============================================================================
__all__ = ['card', 'engines', 'formula', 'pb', 'process', 'solvers']
