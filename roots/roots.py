#!/usr/bin/env python
# -*- coding: utf-8 -*-
#   Copyright 2014 Tom Regan
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
"""
Usage:
  root import <path>
  root update
  root list [-a | -i] [<query>]...
  root fields
  root config [-p | -d | --path | --default]
  root help <command>
  root (-h | --help | --version)

Commands:
  import     Import new e-books.
  update     Update the library.
  list       Query the library.
  fields     Show fields that can be used in queries.
  config     Show the configuration.
  help       Show help for a sub-command.

Options:
  -h --help  Show this help.
  --version  Show version.
"""


import re
import blessings
import pickle

from os import path, walk, makedirs
from os.path import join
from shutil import copy2 as _copy
from docopt import docopt

from command import List, Help, Config, Fields, Update
from configuration import user_configuration, compile_regex
from format import EpubFormat


class Terminal(blessings.Terminal):
    """Allows interaction with the terminal.
    """
    def warn(self, msg, *args):
        """Write a warning message to the terminal.
        """
        line_length = sum(len(x) for x in args)
        fmt = ''
        for word in msg.split():
            line_length += len(word)
            if line_length + len(word) > self.width:
                fmt += '\n' + word + ' '
                line_length = 0
            else:
                fmt += word + ' '
        print (self.red +
               fmt.replace('%s', self.yellow + "'%s'" + self.red) +
               self.normal) % args


def do_command(arguments, configuration):
    """TODO"""
    def locate_element(x, y):
        if x is None or y is None:
            return
        elements = [e for e in x.iter() if e.tag.endswith(y)]
        if elements is None or len(elements) < 1:
            return
        return elements[0].text or elements[0]

    configuration['search'] = locate_element
    term = Terminal()
    configuration['terminal'] = term
    if arguments['import']:
        srcpath = arguments['<path>']
        if path.isfile(srcpath):
            term.warn("source path should not be a file: %s", srcpath)
            return
        configuration['system']['srcpath'] = srcpath
        do_import(configuration)
    elif arguments['update']:
        Update(arguments, configuration).do
    elif arguments['config']:
        Config(arguments, configuration).do
    elif arguments['list']:
        List(arguments, configuration).do
    elif arguments['help']:
        Help(arguments, configuration).do
    elif arguments['fields']:
        Fields(arguments, configuration).do


def do_import(configuration):
    """TODO"""
    directory = configuration['directory']
    if not path.exists(directory):
        configuration['terminal'].warn('Cannot open library: %s', directory)
        return
    moves = _consider_moves(configuration)
    count = _move_to_library(moves, configuration)
    print 'Imported %d %s.' % (count, count != 1 and 'books' or 'book')


def _consider_moves(configuration):
    """Determines the files to be moved and their destinations.
    """
    library = configuration['directory']
    moves = []
    for basepath, _, filenames in walk(configuration['system']['srcpath']):
        for filename in filenames:
            if not filename.endswith(".epub"):
                continue
            srcpath = join(basepath, filename)
            #book = _load_book_data(srcpath, configuration)
            book = EpubFormat(configuration).load(srcpath)
            if book is None:
                continue
            destination_dir = path.join(library, book['author'])
            destination_file = _clean_path(
                book['title'] + '.epub', configuration)
            destpath = path.join(destination_dir, destination_file)
            moves.append((srcpath, destpath, destination_dir))
    return moves


def _clean_path(srcpath, configuration):
    """Takes a path (as a Unicode string) and makes sure that it is
    legal.
    """
    replacements = configuration['import']['replacements']
    for expression, replacement in replacements.iteritems():
        srcpath = expression.sub(replacement, srcpath)
    return srcpath


def _move_to_library(moves, configuration, move=_copy):
    """Move files to the library
    """
    terminal = configuration['terminal']
    count = 0
    for srcpath, destpath, destination_dir in moves:
        try:
            if not path.exists(destination_dir):
                makedirs(destination_dir)
        except OSError:
            terminal.warn("Error creating path %s", destination_dir)
            continue
        if not configuration['import']['overwrite'] and path.isfile(destpath):
            terminal.warn("Not importing %s because it already exists in the "
                          "library.", srcpath)
            continue
        print "%s ->\n%s" % (path.basename(srcpath), destpath)
        try:
            move(srcpath, destpath)
            count += 1
        except IOError, ioerror:
            terminal.warn("Error copying %s (%s)", srcpath, ioerror.errno)
            continue
    return count


def main():
    """TODO"""
    arguments = docopt(__doc__, version='0.0.1')
    configuration = user_configuration()
    compile_regex(configuration)
    do_command(arguments, configuration)


if __name__ == '__main__':
    main()
