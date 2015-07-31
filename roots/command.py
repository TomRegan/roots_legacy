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

from os.path import isfile, exists, expanduser
from collections import namedtuple
from texttable import Texttable
import yaml

from configuration import user_configuration, default_configuration
from format import EpubFormat
from isbndb import Service
from diff import diff
import storage
import files
import logger



Complete = namedtuple('Complete', 'message')
Error = namedtuple('Error', 'reason')

def command(arguments, configuration):
    """Returns an appropriate command."""
    if 'import' in arguments and arguments['import']:
        return Import(arguments, configuration)
    if 'update' in arguments and  arguments['update']:
        return Update(arguments, configuration)
    if 'config' in arguments and arguments['config']:
        return Config(arguments, configuration)
    if 'list' in arguments and arguments['list']:
        return List(arguments, configuration)
    if 'fields' in arguments and arguments['fields']:
        return Fields(arguments, configuration)
    if 'remote' in arguments and arguments['remote']:
        return RemoteLookup(arguments, configuration)


class BaseCommand(object):
    """Base command class."""
    def __init__(self, arguments, configuration):
        self._arguments = arguments
        self._configuration = configuration
        self.log = logger.get_logger(self.__class__.__name__, configuration)

    @property
    def name(self):
        return self.__class__.__name__


# TODO: move into a separate module
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

    def execute(self):
        """Loads the library metadata and selects entries from it.
        """

        restrict, select = self._parse_query()
        results = books_as_tuple(self._configuration, restrict, select)
        if len(results) == 0:
            return None, Error("No matches for %s." % select)
        elif self._configuration['list']['table'] or self._arguments['-t']:
            return Complete(self._print_results_table(results)), None
        return Complete('\n'.join(self._print_results(results))), None

    def _parse_query(self):
        """Extract select and restrict operations from the query.
        """
        user_query = self._arguments['<query>']
        if user_query:
            if ':' in user_query[0]:
                restrict, select = user_query[0].split(':')
                select += ' '.join([s for s in user_query[1:]])
                return restrict, select
            else:
                return 'title', ' '.join(user_query)
        return None, None

    def _print_results(self, results):
        """Print author, title and ISBN depending on the option.
        """
        buf = []
        if self._arguments['-a']:
            for author in sorted({result[0] for result in results}):
                buf.append(author)
        elif self._configuration['list']['isbn'] or self._arguments['-i']:
            for result in sorted(results):
                buf.append("%s - %s - %s" % result)
        else:
            for result in sorted(results):
                buf.append("%s - %s" % result[:2])
        return buf

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
        return table.draw()


class Fields(BaseCommand):

    def execute(self):
        books = storage.load(self._configuration, 'library', self.log)
        fields = set()
        for book in books:
            for field in book.keys():
                if field[0] is not '_':
                    fields.add(field)
        return Complete('\n'.join(fields)), None


class Config(BaseCommand):

    def execute(self):
        """Prints configuration.
        """
        if self._arguments['-p'] or self._arguments['--path']:
            return Complete(self._configuration['system']['configfile']), None
        if self._arguments['-d'] or self._arguments['--default']:
            configuration = default_configuration()
        else:
            configuration = user_configuration()
        configuration.pop('system')
        msg = yaml.dump(configuration, default_flow_style=False)
        return Complete(msg), None


class Update(BaseCommand):

    def execute(self):
        """Updates the library.
        """
        books = []
        directory = self._configuration['directory']
        if not exists(directory):
            return None, Error('Cannot open library: %s' % directory)
        moves, books = files.find_moves(self._configuration, directory)
        moved = 0
        # if the user has chosen the move option, they'll be renamed
        # according to their new author / title, otherwise just
        # update the database
        if self._configuration['import']['move']:
            moved = files.move_to_library(self._configuration, moves)
            if self._configuration['import']['prune']:
                files.prune(self._configuration)
        # here we begin the database update
        found = len(books)
        if found > 0:
            storage.store(self._configuration, {'library': books}, self.log)

        msg = 'Updated %d %s, moved %d.' % (
            found, found != 1 and 'books' or 'book', moved
        )
        return Complete(msg), None


class Import(BaseCommand):

    def execute(self):
        """Imports new e-books.
        """
        srcpath = self._arguments['<path>']
        if isfile(srcpath):
            return None, Error("Source path should not be a file: %s" % srcpath)
        directory = expanduser(self._configuration['directory'])
        if not exists(directory):
            return None, Error('Cannot open library: %s' % directory)
        moves, books = files.find_moves(self._configuration,
                                        self._arguments['<path>'])
        count = files.move_to_library(self._configuration, moves)
        if count > 0:
            storage.update(self._configuration, 'library', books,
                           lambda x, y: x + y, logger=self.log)
        msg = 'Imported %d %s.' % (count, count != 1 and 'books' or 'book')
        return Complete(msg), None


class RemoteLookup(BaseCommand):

    def execute(self):
        """Looks up book data from ISBNDB"""
        restrict, select = self._parse_query()
        old_books = books_as_map(self._configuration, restrict, select)
        request = Service(self._configuration)
        new_books = request.request(old_books)
        books = [book for  book in
                 [diff(a, b) for a, b in zip(old_books, new_books)]
                ]
        return Complete(books), None

    def _parse_query(self):
        """Extract select and restrict operations from the query."""
        user_query = self._arguments['<query>']
        if user_query:
            if ':' in user_query[0]:
                restrict, select = user_query[0].split(':')
                return restrict, ' '.join([select] + user_query[1:])
            else:
                return 'title', ' '.join(user_query)
        return None, None
