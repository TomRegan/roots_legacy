#!/usr/bin/env python
# -*- encoding: utf-8 -*-
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
"""Commands
"""

from pickle import load
from os.path import join
from sys import modules
from inspect import isclass, getmembers

class _Command(object):
    """Base command class.
    """
    @property
    def name(self):
        return self.__class__.__name__


    @property
    def help(self):
        return self.__doc__


class List(_Command):
    """Usage: root list [-a | -i] [<query>]...
Synopsis: Queries the library.

Options:
  -a  Show a list of matching authors.
  -i  Shou the ISBN number of each title.

Examples:
  root list author:forster
    -> All titles by Forster.

  root list -a title:room with a view
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
        books = []
        library_path = join(self._configuration['system']['configpath'],
                            self._configuration['library'])
        with open(library_path, 'rb') as library_file:
            books = load(library_file)
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
            configuration['terminal'].warn('No matches for %s.', select)
        elif self._arguments['-a']:
            for author in sorted({result[0] for result in results}):
                print author
        elif self._arguments['-i']:
            for result in sorted(results):
                print "%s - %s - %s" % result
        else:
            for result in sorted(results):
                print "%s - %s" % result[:2]


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


class Help(_Command):
    """Usage: root help [%s]
Synopsis: Shows help for a command.

Examples:
  root help list
    -> Shows help for the list command.
"""
    def __init__(self, arguments, configuration):
        self._arguments = arguments
        self._configuration = configuration


    @property
    def do(self):
        """Prints documentation for the command.
        """
        command = self._arguments['<command>']
        if command.lower() == 'list':
            print List(self._arguments, self._configuration).help
            return
        print self.help


    @property
    def help(self):
        """Returns help string.
        """
        commands = [n for n, _ in getmembers(modules[__name__], isclass)
                    if n is not self.name and '_' not in n[0]]
        return self.__doc__ % ' | '.join(commands)
