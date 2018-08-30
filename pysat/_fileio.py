#!/usr/bin/env python
#-*- coding:utf-8 -*-
##
## _fileio.py
##
##  Created on: Aug 18, 2018
##      Author: Alexey S. Ignatiev
##      E-mail: aignatiev@ciencias.ulisboa.pt
##

"""
    ===============
    List of classes
    ===============

    .. autosummary::
        :nosignatures:

        FileObject

    ==================
    Module description
    ==================

    This simple module provides a basic interface to input/output operations on
    files. Its key design feature is the ability to work with both uncompressed
    and compressed files through a unified interface, thus, making it easier
    for a user to deal with various types of compressed files. The compression
    types supported include gzip, bzip2, and lzma (xz).

    The module is supposed to be mainly used by :mod:`pysat.formula`.

    A simple usage example is the following:

    .. code-block:: python

        >>> from pysat._fileio import FileObject
        >>>
        >>> with FileObject(name='formula.cnf', mode='r') as fp1:
        ...     contents1 = fp1.readlines()
        >>>
        >>> with FileObject(name='filename.txt.gz', compression='use_ext') as fp2:
        ...     contents2 = fp2.readlines()
        >>>
        >>> with FileObject(name='f.txt.bz2', mode='w', compression='bzip2') as fp3:
        ...     fp3.write('hello, world!\n')

    ==============
    Module details
    ==============
"""

#
#==============================================================================
import bz2
import codecs
import gzip
import os

lzma_present = True
try:  # for Python3
    import lzma
except ImportError:
    try:  # for Python2 + backports.lzma installed
        from backports import lzma
    except ImportError:  # for Python2 without lzma
        lzma_present = False


#
#==============================================================================
class FileObject(object):
    """
        Auxiliary class for convenient and uniform file manipulation, e.g. to
        open files creating standard file pointers and closing them. The class
        is used when opening DIMACS files for reading and writing. Supports
        both uncompressed and compressed files. Compression algorithms
        supported are ``gzip``, ``bzip2``, and ``lzma``. Algorithm ``lzma`` can
        be used in Python 3 by default and also in Python 2 if the
        ``backports.lzma`` package is installed.

        Note that the class opens a file in text mode.

        :param name: a file name to open
        :param mode: opening mode
        :param compression: compression type

        :type name: str
        :type mode: str
        :type compression: str

        Compression type can be ``None``, ``'gzip'``, ``'bzip2'``, ``'lzma'``,
        as well as ``'use_ext'``. If ``'use_ext'`` is specified, compression
        algorithm is defined by the extension of the given file name.
    """

    def __init__(self, name, mode='r', compression=None):
        """
            Constructor.
        """

        self.fp = None  # file pointer to give access to
        self.ctype = None  # compression type

        # in some cases an additional file pointer is needed
        self.fp_extra = None

        self.open(name, mode=mode, compression=compression)

    def open(self, name, mode='r', compression=None):
        """
            Open a file pointer. Note that a file is *always* opened in text
            mode. The method inherits its input parameters from the constructor
            of :class:`FileObject`.
        """

        if compression == 'use_ext':
            self.get_compression_type(name)
        else:
            self.ctype = compression

        if not self.ctype:
            self.fp = open(name, mode)
        elif self.ctype == 'gzip':
            self.fp = gzip.open(name, mode + 't')
        elif self.ctype == 'bzip2':
            try:
                # Python 3 supports opening bzip2 files in text mode
                # therefore, we prefer to open them this way
                self.fp = bz2.open(name, mode + 't')
            except:
                # BZ2File opens a file in binary mode
                # thus, we have to use codecs.getreader()
                # to be able to use it in text mode
                self.fp_extra = bz2.BZ2File(name, mode)

                if mode == 'r':
                    self.fp = codecs.getreader('ascii')(self.fp_extra)
                else:  # mode == 'w'
                    self.fp = codecs.getwriter('ascii')(self.fp_extra)
        else:  # self.ctype == 'lzma'
            # LZMA is available in Python 2 only if backports.lzma is installed
            # Python 3 supports it by default
            assert lzma_present, 'LZMA compression is unavailable.'
            self.fp = lzma.open(name, mode=mode + 't')

    def close(self):
        """
            Close a file pointer.
        """

        if self.fp:
            self.fp.close()
            self.fp = None

        if self.fp_extra:
            self.fp_extra.close()
            self.fp_extra = None

        self.ctype = None

    def get_compression_type(self, file_name):
        """
            Determine compression type for a given file using its extension.

            :param file_name: a given file name
            :type file_name: str
        """

        ext = os.path.splitext(file_name)[1]

        if ext == '.gz':
            self.ctype = 'gzip'
        elif ext == '.bz2':
            self.ctype = 'bzip2'
        elif ext in ('.xz', '.lzma'):
            self.ctype = 'lzma'
        else:
            self.ctype = None

    def __enter__(self):
        """
            'with' constructor.
        """

        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
            'with' destructor.
        """

        self.close()
