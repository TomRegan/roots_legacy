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

"""Commands.
"""

from os.path import join, isfile, exists, basename
from os import walk, makedirs
from sys import modules
from inspect import isclass, getmembers
from shutil import copy2 as _copy, move as _move
from texttable import Texttable

import yaml

from configuration import user_configuration, default_configuration
from format import EpubFormat
import library


def command(arguments, configuration):
    """Returns an appropriate command.
    """
    if arguments['import']:
        return Import(arguments, configuration)
    elif arguments['update']:
        return Update(arguments, configuration)
    elif arguments['config']:
        return Config(arguments, configuration)
    elif arguments['list']:
        return List(arguments, configuration)
    elif arguments['help']:
        return Help(arguments, configuration)
    elif arguments['fields']:
        return Fields(arguments, configuration)


class BaseCommand(object):

    """Base command class.
    """
    @property
    def name(self):
        return self.__class__.__name__

    @property
    def help(self):
        return self.__doc__


class List(BaseCommand):

    """Usage: root list [-ait] [<query>]...
Synopsis: Queries the library.

Options:
  -a  Show a list of matching authors.
  -i  Show the ISBN number of each title.
  -t  Print the matches in a table.

Examples:
  root list author:forster
    -> All titles by Forster.

  root list -a howards end
    -> All authors of matching titles.

  root list -i
    -> All known titles with ISBNs.
"""

    def __init__(self, arguments, configuration):
        self._arguments = arguments
        self._configuration = configuration

    def do(self):
        """Loads the library metadata and selects entries from it.
        """
        books = library.load(self._configuration)['library']
        restrict, select = self._parse_query()
        if select is None:
            results = [(book['author'], book['title'], book['isbn'])
                       for book in books]
        else:
            results = [(book['author'], book['title'], book['isbn'])
                       for book in books
                       if restrict in book.keys()
                       and select.upper()
                       in unicode(book[restrict]).upper()]
        if len(results) == 0:
            raise Exception("No matches for %s.", select)
        elif self._configuration['list']['table'] or self._arguments['-t']:
            self._print_results_table(results)
        else:
            self._print_results(results)

    def _parse_query(self):
        """Extract select and restrict operations from the query.
        """
        query = self._arguments['<query>']
        if query:
            if ':' in query[0]:
                restrict, select = query[0].split(':')
                return restrict, ' '.join([select] + query[1:])
            else:
                return 'title', ' '.join(query)
        return None, None

    def _print_results(self, results):
        """Print author, title and ISBN depending on the option.
        """
        if self._arguments['-a']:
            for author in sorted({result[0] for result in results}):
                print author
        elif self._configuration['list']['isbn'] or self._arguments['-i']:
            for result in sorted(results):
                print "%s - %s - %s" % result
        else:
            for result in sorted(results):
                print "%s - %s" % result[:2]

    def _print_results_table(self, results):
        """Print results formatted in a table.
        """
        table = Texttable()
        table.set_chars(['-', '|', '+', '-'])
        table.set_deco(Texttable.BORDER | Texttable.HEADER | Texttable.VLINES)
        header_type = ['t', 't']
        header = ['Auther', 'Title']
        if self._configuration['list']['isbn'] or self._arguments['-i']:
            header_type += ['t']
            header += ['Isbn']
        table.set_cols_dtype(header_type)
        table.header(header)
        for author, title, isbn in results:
            if isbn is None: isbn = ""
            row = [author.encode('utf-8'), title.encode('utf-8')]
            if self._configuration['list']['isbn'] or self._arguments['-i']:
                row += [isbn.encode('utf-8')]
            table.add_row(row)
        print table.draw()


class Fields(BaseCommand):

    """Usage: root fields
Synopsis: Shows fields that can be used in queries.
"""

    def __init__(self, arguments, configuration):
        self._configuration = configuration

    def do(self):
        books = library.load(self._configuration)
        fields = set()
        for book in books:
            for field in book.keys():
                if field[0] is not '_':
                    fields.add(field)
        print '\n'.join(fields)


class Help(BaseCommand):

    """Usage: root help [%s]
Synopsis: Shows help for a command.

Examples:
  root help list
    -> Shows help for the list command.
"""

    def __init__(self, arguments, configuration):
        self._arguments = arguments
        self._configuration = configuration
        self._commands = {n.lower(): c
                          for n, c in getmembers(modules[__name__], isclass)
                          if n not in ['BaseCommand', 'EpubFormat', 'Texttable']}

    def do(self):
        """Prints documentation for the command.
        """
        command = self._arguments['<command>'].lower()
        if command in self._commands.keys():
            print self._commands[command](self._arguments,
                                          self._configuration).help
            return
        print 'No such command: ' + command
        print self.help

    @property
    def help(self):
        """Returns help string.
        """
        return self.__doc__ % ' | '.join(self._commands.keys())


class Config(BaseCommand):

    """Usage: root config [-p | --path | -d | --default]
Synopsis: Shows the configuration.

Options:
  -p,--path     Display the configuration file path.
  -d,--default  Display configuration defaults.
"""

    def __init__(self, arguments, configuration):
        self._configuration = configuration
        self._arguments = arguments

    def do(self):
        """Prints configuration.
        """
        if self._arguments['-p'] or self._arguments['--path']:
            print self._configuration['system']['configfile']
            return
        if self._arguments['-d'] or self._arguments['--default']:
            configuration = default_configuration()
        else:
            configuration = user_configuration()
        configuration.pop('system')
        print yaml.dump(configuration, default_flow_style=False)


class Update(BaseCommand):

    """Usage: root update
Synopsis: Updates the library.
"""

    def __init__(self, arguments, configuration):
        self._arguments = arguments
        self._configuration = configuration

    def do(self):
        """Updates the library.
        """
        books = []
        directory = self._configuration['directory']
        if not exists(directory):
            raise Exception('Cannot open library: %s', directory)
        for basepath, _, filenames in walk(directory):
            for filename in filenames:
                if filename.endswith(".epub"):
                    srcpath = join(basepath, filename)
                    books.append(EpubFormat(self._configuration).load(srcpath))
        count = len(books)
        if count > 0:
            library.store(self._configuration, {'library': books})
        print 'Imported %d %s.' % (count, count != 1 and 'books' or 'book')


class Import(BaseCommand):

    """Usage: root import <path>
Synopsis: Imports new e-books.

Examples:
  root import ~/Downloads/
    -> imports books from ~/Downloads/
"""

    def __init__(self, arguments, configuration):
        self._arguments = arguments
        self._configuration = configuration
        self._term = configuration['terminal']

    def do(self):
        """Imports new e-books.
        """
        srcpath = self._arguments['<path>']
        if isfile(srcpath):
            raise Exception("Source path should not be a file: %s", srcpath)
        directory = self._configuration['directory']
        if not exists(directory):
            raise Exception('Cannot open library: %s', directory)
        moves, books = self._consider_moves()
        if self._configuration['import']['move']:
            move = _move
        else:
            move = _copy
        count = self._move_to_library(moves, move=move)
        if count > 0:
            library.store(self._configuration, {'library': books})
        print 'Imported %d %s.' % (count, count != 1 and 'books' or 'book')

    def _consider_moves(self):
        """Determines the files to be moved and their destinations.
        """
        library = self._configuration['directory']
        moves, books = [], []
        for basepath, _, filenames in walk(self._arguments['<path>']):
            for filename in filenames:
                try:
                    if not filename.lower().endswith(".epub"):
                        continue
                    srcpath = join(basepath, filename)
                    book = EpubFormat(self._configuration).load(srcpath)
                    if book is None:
                        continue
                    destination_dir = join(library, self._clean_path(
                        book['author']))
                    destination_file = self._clean_path(
                        book['title'] + '.epub')
                except Exception, e:
                    if len(e.args) > 0:
                        self._term.warn("Not importing %s because " +
                                        str(e.args[0]).lower(), srcpath)
                    continue
                destpath = join(destination_dir, destination_file)
                moves.append((srcpath, destpath, destination_dir))
                books.append(book)
        self._term.debug('_consider_moves() -> %s %s', moves, books)
        return moves, books

    def _clean_path(self, srcpath):
        """Takes a path (as a Unicode string) and makes sure that it is
        legal.
        """
        replacements = self._configuration['import']['replacements']
        for expression, replacement in replacements.iteritems():
            srcpath = expression.sub(replacement, srcpath)
        return srcpath

    def _move_to_library(self, moves, move=_copy):
        """Move files to the library
        """
        count = 0
        for srcpath, destpath, destination_dir in moves:
            try:
                if not exists(destination_dir):
                    makedirs(destination_dir)
            except OSError:
                self._term.warn("Error creating path %s", destination_dir)
                continue
            overwrite = self._configuration['import']['overwrite']
            if not overwrite and isfile(destpath):
                self._term.warn("Not importing %s because it already exists "
                              "in the library.", srcpath)
                continue
            print "%s ->\n%s" % (basename(srcpath), destpath)
            try:
                move(srcpath, destpath)
                count += 1
            except IOError, ioe:
                self._term.warn("Error copying %s (%s)", srcpath, ioe.errno)
                continue
        self._term.debug('_move_to_library() -> %d', count)
        return count
