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

"""Commands.
"""

from __future__ import print_function

from os.path import isfile, exists
from inspect import getdoc
from collections import namedtuple
from texttable import Texttable
import yaml

from configuration import user_configuration, default_configuration
from format import EpubFormat
from isbndb import Service
import storage
import files

Error = namedtuple('Error', 'reason')

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
    elif arguments['test']:
        return Test(arguments, configuration)


class BaseCommand(object):

    """Base command class.
    """
    def __init__(self, arguments, configuration):
        self._arguments = arguments
        self._configuration = configuration
        self.out = print

    @property
    def name(self):
        return self.__class__.__name__

    @property
    def help(self):
        return getdoc(self)


#TODO move into a separate module
def books_as_tuple(configuration, restrict='title', select=None):
    return [(book['author'], book['title'], book['isbn'])
            for book in _query(configuration, restrict, select)]

def books_as_map(configuration, restrict='title', select=None):
    return _query(configuration, restrict, select)

def _query(configuration, restrict='title', select=None):
    books = storage.load(configuration, 'library')
    if select is None:
        return books
    else:
        return [book for book in books
                if restrict in book.keys()
                and select.upper()
                in unicode(book[restrict]).upper()]


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

    def execute(self):
        """Loads the library metadata and selects entries from it.
        """

        restrict, select = self._parse_query()
        results = books_as_tuple(self._configuration, restrict, select)
        if len(results) == 0:
            return None, Error("No matches for %s." % select)
        elif self._configuration['list']['table'] or self._arguments['-t']:
            self._print_results_table(results)
        else:
            self._print_results(results)
        return None, None

    def _parse_query(self):
        """Extract select and restrict operations from the query.
        """
        user_query = self._arguments['<query>']
        if user_query:
            if ':' in user_query[0]:
                restrict, select = user_query[0].split(':')
                return restrict, ' '.join([select] + user_query[1:])
            else:
                return 'title', ' '.join(user_query)
        return None, None

    def _print_results(self, results):
        """Print author, title and ISBN depending on the option.
        """
        if self._arguments['-a']:
            for author in sorted({result[0] for result in results}):
                self.out(author)
        elif self._configuration['list']['isbn'] or self._arguments['-i']:
            for result in sorted(results):
                self.out("%s - %s - %s" % result)
        else:
            for result in sorted(results):
                self.out("%s - %s" % result[:2])

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
            if isbn is None:
                isbn = ""
            row = [author.encode('utf-8'), title.encode('utf-8')]
            if self._configuration['list']['isbn'] or self._arguments['-i']:
                row += [isbn.encode('utf-8')]
            table.add_row(row)
        self.out(table.draw())


class Fields(BaseCommand):

    """Usage: root fields
    Synopsis: Shows fields that can be used in queries.
    """

    def execute(self):
        books = storage.load(self._configuration, 'library')
        fields = set()
        for book in books:
            for field in book.keys():
                if field[0] is not '_':
                    fields.add(field)
        self.out('\n'.join(fields))


class Help(BaseCommand):

    """Usage: root help [%s]
    Synopsis: Shows help for a command.

    Examples:
      root help list
        -> Shows help for the list command.
    """

    def __init__(self, arguments, configuration):
        super(Help, self).__init__(arguments, configuration)
        self._commands = {
            command.__name__.lower(): command
            for command in BaseCommand.__subclasses__()
        }

    def execute(self):
        """Prints documentation for the command.
        """
        command = self._arguments['<command>'].lower()
        if command in self._commands.keys():
            self.out(self._commands[command]
                     (self._arguments, self._configuration).help)
            return None, None
        self.out('No such command: ' + command)
        self.out(self.help)
        return None, None

    @property
    def help(self):
        """Returns help string.
        """
        return getdoc(self) % ' | '.join(sorted(self._commands.keys()))


class Config(BaseCommand):

    """Usage: root config [-p | --path | -d | --default]
    Synopsis: Shows the configuration.

    Options:
      -p,--path     Display the configuration file path.
      -d,--default  Display configuration defaults.
    """

    def execute(self):
        """Prints configuration.
        """
        if self._arguments['-p'] or self._arguments['--path']:
            self.out(self._configuration['system']['configfile'])
            return
        if self._arguments['-d'] or self._arguments['--default']:
            configuration = default_configuration()
        else:
            configuration = user_configuration()
        configuration.pop('system')
        self.out(yaml.dump(configuration, default_flow_style=False))
        return None, None


class Update(BaseCommand):

    """Usage: root update
    Synopsis: Updates the library.
    """

    def execute(self):
        """Updates the library.
        """
        books = []
        directory = self._configuration['directory']
        if not exists(directory):
            return None, Error('Cannot open library: %s' % directory)
        moves, books = files.find_moves(self._configuration, directory)
        moved = 0
        if self._configuration['import']['move']:
            moved = files.move_to_library(self._configuration, moves)
            if self._configuration['import']['prune']:
                files.prune(self._configuration)
        found = len(books)
        if found > 0:
            storage.store(self._configuration, {'library': books})

        self.out('Updated %d %s, moved %d.' % (
            found, found != 1 and 'books' or 'book', moved
        ))
        return None, None


class Import(BaseCommand):

    """Usage: root import <path>
    Synopsis: Imports new e-books.

    Examples:
      root import ~/Downloads/
        -> imports books from ~/Downloads/
    """

    def execute(self):
        """Imports new e-books.
        """
        srcpath = self._arguments['<path>']
        if isfile(srcpath):
            return None, Error("Source path should not be a file: %s" % srcpath)
        directory = self._configuration['directory']
        if not exists(directory):
            return None, Error('Cannot open library: %s' % directory)
        moves, books = files.find_moves(self._configuration,
                                        self._arguments['<path>'])
        count = files.move_to_library(self._configuration, moves)
        if count > 0:
            storage.update(self._configuration, 'library', books,
                           lambda x, y: x + y)
        self.out('Imported %d %s.' % (count, count != 1 and 'books' or 'book'))
        return None, None

class Test(BaseCommand):

    """Usage: root test [<query>]...
    Synopsis: Test the isbndb command.
    """

    def execute(self):
        """Tests the ISBNDB command
        """
        restrict, select = self._parse_query()
        books = books_as_map(self._configuration, restrict, select)
        request = Service(self._configuration)
        self.out(books)
        books = request.request(books)
        self.out(books)
        return None, None

    def _parse_query(self):
        """Extract select and restrict operations from the query.
        """
        user_query = self._arguments['<query>']
        if user_query:
            if ':' in user_query[0]:
                restrict, select = user_query[0].split(':')
                return restrict, ' '.join([select] + user_query[1:])
            else:
                return 'title', ' '.join(user_query)
        return None, None
