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
"""Commands.
"""
from os.path import join, isfile, exists, basename
from os import walk, makedirs
from sys import modules
from inspect import isclass, getmembers
from shutil import copy2 as _copy

import pickle
import yaml

from configuration import user_configuration, default_configuration
from format import EpubFormat


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

    """Usage: root list [-a | -i] [<query>]...
Synopsis: Queries the library.

Options:
  -a  Show a list of matching authors.
  -i  Shou the ISBN number of each title.

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

    @property
    def do(self):
        """Loads the library metadata and selects entries from it.
        """
        library_path = join(self._configuration['system']['configpath'],
                            self._configuration['library'])
        with open(library_path, 'rb') as library_file:
            books = pickle.load(library_file)
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
            self._configuration['terminal'].warn('No matches for %s.', select)
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
        elif self._arguments['-i']:
            for result in sorted(results):
                print "%s - %s - %s" % result
        else:
            for result in sorted(results):
                print "%s - %s" % result[:2]


class Fields(BaseCommand):

    """Usage: root fields
Synopsis: Shows fields that can be used in queries.
"""

    def __init__(self, arguments, configuration):
        self._arguments = arguments
        self._configuration = configuration
        self._term = self._configuration['terminal']

    @property
    def do(self):
        library_path = join(self._configuration['system']['configpath'],
                            self._configuration['library'])
        if not isfile(library_path):
            self._term.warn('Cannot open database file: %s',
                            self._configuration['library'])
            return
        with open(library_path, 'rb') as library_file:
            books = pickle.load(library_file)
            fields = set()
            for book in books:
                for field in book.keys():
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
                          if n is not self.name
                          and n not in ['BaseCommand', 'EpubFormat']}

    @property
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

    @property
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

    @property
    def do(self):
        """Updates the library.
        """
        books = []
        directory = self._configuration['directory']
        term = self._configuration['terminal']
        if not exists(directory):
            term.warn('Cannot open library: %s', directory)
            return
        for basepath, _, filenames in walk(directory):
            for filename in filenames:
                if filename.endswith(".epub"):
                    srcpath = join(basepath, filename)
                    books.append(EpubFormat(self._configuration).load(srcpath))
        library = join(self._configuration['system']['configpath'],
                       self._configuration['library'])
        with open(library, 'wb') as library_file:
            pickle.dump(books, library_file)
            count = len(books)
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

    @property
    def do(self):
        """Imports new e-books.
        """
        term = self._configuration['terminal']
        srcpath = self._arguments['<path>']
        if isfile(srcpath):
            term.warn("source path should not be a file: %s", srcpath)
            return
        directory = self._configuration['directory']
        if not exists(directory):
            term.warn('Cannot open library: %s', directory)
            return
        moves = self._consider_moves()
        count = self._move_to_library(moves)
        print 'Imported %d %s.' % (count, count != 1 and 'books' or 'book')

    def _consider_moves(self):
        """Determines the files to be moved and their destinations.
        """
        library = self._configuration['directory']
        moves = []
        for basepath, _, filenames in walk(self._arguments['<path>']):
            for filename in filenames:
                if not filename.endswith(".epub"):
                    continue
                srcpath = join(basepath, filename)
                book = EpubFormat(self._configuration).load(srcpath)
                if book is None:
                    continue
                destination_dir = join(library, book['author'])
                destination_file = self._clean_path(
                    book['title'] + '.epub')
                destpath = join(destination_dir, destination_file)
                moves.append((srcpath, destpath, destination_dir))
        return moves

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
        terminal = self._configuration['terminal']
        count = 0
        for srcpath, destpath, destination_dir in moves:
            try:
                if not exists(destination_dir):
                    makedirs(destination_dir)
            except OSError:
                terminal.warn("Error creating path %s", destination_dir)
                continue
            overwrite = self._configuration['import']['overwrite']
            if not overwrite and isfile(destpath):
                terminal.warn("Not importing %s because it already exists "
                              "in the library.", srcpath)
                continue
            print "%s ->\n%s" % (basename(srcpath), destpath)
            try:
                move(srcpath, destpath)
                count += 1
            except IOError, ioerror:
                terminal.warn("Error copying %s (%s)", srcpath, ioerror.errno)
                continue
        return count
