#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2014 Tom Regan
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

from os import walk, makedirs
from os.path import join, isfile, dirname, basename, exists
from shutil import copy2 as _copy, move as _move
from format import EpubFormat


def find_moves(configuration, srcpath):
    """Determines the files to be moved and their destinations.
    """
    library = configuration['directory']
    terminal = configuration['terminal']
    moves, books = [], []
    for basepath, _, filenames in walk(srcpath):
        for filename in filenames:
            try:
                if not filename.lower().endswith(".epub"):
                    continue
                srcpath = join(basepath, filename)
                book = EpubFormat(configuration).load(srcpath)
                if book is None:
                    continue
                dstdir = join(library, clean_path(configuration, book['author']))
                dstfile = clean_path(configuration, book['title'] + '.epub')
            except Exception, e:
                if len(e.args) > 0:
                    terminal.warn("Not importing %s because " +
                                  str(e.args[0]).lower(), srcpath)
                continue
            dstpath = join(dstdir, dstfile)
            overwrite = configuration['import']['overwrite']
            if not overwrite and isfile(dstpath):
                terminal.warn("Not importing %s because it already "
                              "exists in the library.", srcpath)
                continue
            if srcpath != dstpath:
                moves.append((srcpath, dstpath))
                books.append(book)
    terminal.debug('_consider_moves() -> %s %s', moves, books)
    return moves, books

def clean_path(configuration, srcpath):
    """Takes a path (as a Unicode string) and makes sure that it is
    legal.
    """
    replacements = configuration['import']['replacements']
    for expression, replacement in replacements.iteritems():
        srcpath = expression.sub(replacement, srcpath)
    return srcpath

def move_to_library(configuration, moves, move=_copy):
    """Move files to the library
    """
    terminal = configuration['terminal']
    move = {
        True: _move,
        False: _copy
    }[configuration['import']['move']]
    moved = 0
    for srcpath, destpath in moves:
        destdir = dirname(destpath)
        try:
            if not exists(destdir):
                makedirs(destdir)
        except OSError:
            terminal.warn("Error creating path %s", destdir)
            continue
        print "%s ->\n%s" % (basename(srcpath), destpath)
        try:
            move(srcpath, destpath)
            moved += 1
        except IOError, ioe:
            terminal.warn("Error importing %s (%s)", srcpath, ioe.errno)
    terminal.debug('_move_to_library() -> %d', moved)
    return moved
