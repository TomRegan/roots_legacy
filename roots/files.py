#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2015 Tom Regan
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""File operations.
"""

from __future__ import print_function

from os import walk, makedirs, rmdir
from os.path import (
    join,
    isfile,
    dirname,
    basename,
    exists,
    samefile,
    expanduser
)
from shutil import copy2 as _copy, move as _move
from format import EpubFormat


def find_moves(configuration, rootpath):
    """Determines the files to be moved and their destinations.
    """
    library = expanduser(configuration['directory'])
    moves, books = [], []
    for basepath, _, filenames in walk(rootpath):
        for filename in filenames:
            try:
                if not filename.lower().endswith(".epub"):
                    continue
                srcpath = join(basepath, filename)
                book = EpubFormat(configuration).load(srcpath)
                if book is None:
                    continue
                dstdir = join(library, _clean_path(configuration, book['author']))
                dstfile = _clean_path(configuration, book['title'] + '.epub')
            except Exception, e:
                if len(e.args) > 0:
                    print("Not importing %s because " +
                          str(e.args[0]).lower() % srcpath)
                continue
            dstpath = join(dstdir, dstfile)
            overwrite = configuration['import']['overwrite']
            if rootpath != library and not overwrite and isfile(dstpath):
                print("Not importing %s because it already "
                      "exists in the library." % srcpath)
                continue
            # if Update, all books, moves if path is wrong
            if samefile(rootpath, library):
                if not samefile(srcpath, dstpath):
                    moves.append((srcpath, dstpath))
                books.append(book)
            # if Import, all new books and moves
            elif not exists(dstpath) or not samefile(srcpath, dstpath):
                moves.append((srcpath, dstpath))
                books.append(book)
    return moves, books

def _clean_path(configuration, srcpath):
    """Takes a path (as a Unicode string) and makes sure that it is
    legal.
    """
    replacements = configuration['import']['replacements']
    for expression, replacement in replacements.iteritems():
        srcpath = expression.sub(replacement, srcpath)
    return srcpath.encode('utf-8')

def move_to_library(configuration, moves, move=_copy):
    """Move files to the library
    """
    if [configuration['import']['move']]:
        move = _move
    else:
        move = _copy
    moved = 0
    for srcpath, destpath in moves:
        destdir = dirname(destpath)
        try:
            if not exists(destdir):
                makedirs(destdir)
        except OSError:
            print("Error creating path %s" % destdir)
            continue
        print("%s ->\n%s" % (basename(srcpath), destpath))
        try:
            move(srcpath, destpath)
            moved += 1
        except IOError, ioe:
            print("Error importing %s (%s)" % srcpath, ioe.errno)
    print('_move_to_library() -> %d' % moved)
    return moved

def prune(configuration):
    """Removes empty directories
    """
    for basepath, dirnames, filenames in walk(configuration['directory'],
                                              topdown=False):
        if len(dirnames) == 0 and len(filenames) == 0:
            rmdir(basepath)
