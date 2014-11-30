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
from os.path import join, isfile
from sys import modules
from inspect import isclass, getmembers

import pickle
import yaml

from configuration import user_configuration, default_configuration


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


class Fields(_Command):
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
        self._commands = {n.lower(): c
                          for n, c in getmembers(modules[__name__], isclass)
                          if n is not self.name and '_' not in n[0]}

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


class Config(_Command):

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
