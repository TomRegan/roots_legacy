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

"""Command Line Interface
"""

from __future__ import print_function

from click import (
    Path,
    argument,
    command,
    confirm,
    echo_via_pager,
    get_terminal_size,
    group,
    option,
    pass_context,
    version_option
)


@group()
@version_option(version='1.0.0') # TODO: read the version from somewhere
@pass_context
def cli(ctx):
    """Command line interface entry point."""
    # TODO: gets the program name wrong
    pass


@cli.command(options_metavar='[-pd | --path | --default]',
             add_help_option=False)
@option('-p', '--path',
        help='Display the configuration file path.',
        is_flag=True)
@option('-d', '--default',
        help='Display configuration defaults.',
        is_flag=True)
@pass_context
def config(ctx, path, default):
    """Shows the configuration."""
    arguments = {
           'config': True,
               '-p': path,
           '--path': path,
               '-d': default,
        '--default': default
    }
    configuration = ctx.obj['configuration']
    ret, _ = ctx.obj['factory'](arguments, configuration).execute()
    print(ret.message)


@cli.command(options_metavar='', add_help_option=False)
@pass_context
def fields(ctx):
    """Shows fields that can be used in queries."""
    arguments = {'fields': True}
    configuration = ctx.obj['configuration']
    ret, _ = ctx.obj['factory'](arguments, configuration).execute()
    print(ret.message)


@cli.command(options_metavar='[-ait | --author | --isbn | --table]',
             add_help_option=False)
@option('-a', '--author',
        help='Show a list of matching authors',
        is_flag=True)
@option('-i', '--isbn',
        help='Show the ISBN number of each title.',
        is_flag=True)
@option('-t', '--table',
        help='Print the matches in a table.',
        is_flag=True)
@argument('query', nargs=-1, metavar='<query>...')
@pass_context
def list(ctx, author, isbn, table, query):
    """Queries the library.

    \b
    Examples:
      root list author:forster
        -> All titles by Forster.
    \b
      root list -a howards end
        -> All authors of matching titles.
    \b
      root list -i
        -> All known titles with ISBNs.
    """
    arguments = {
            'list': True,
         '<query>': query,
              '-t': table,
         '--table': table,
              '-a': author,
        '--author': author,
              '-i': isbn,
          '--isbn': isbn
    }
    configuration = ctx.obj['configuration']
    ret, err = ctx.obj['factory'](arguments, configuration).execute()
    if err:
        print(err.reason)
        return
    lines = ret.message.count('\n')
    _, height = get_terminal_size()
    # page if results are longer then a screen
    if lines > height:
        echo_via_pager(ret.message)
    else:
        print(ret.message)


@cli.command(options_metavar='', add_help_option=False)
@argument('query', nargs=-1, metavar='<query>...')
@pass_context
def update(ctx, query):
    """Updates the library."""
    configuration = ctx.obj['configuration']
    arguments = {'remote': True, '<query>': query}
    if confirm("Do you want to use a web service to fetch information for titles, \
like author, ISBN, and description?"):
        ctx.obj['factory'](arguments, configuration).execute()

    msg = '''If you update the library\n\
    - Files will be %s\n\
    - Empty Directories will%sbe removed\n\
These settings can be configured in %s''' % (
    configuration['import']['move'] and 'moved' or 'copied',
    configuration['import']['prune'] and ' ' or ' not ',
    configuration['system']['configfile']
)
    print(msg)
    if confirm('Do you want to continue?'):
        print('\nBeginning update.')
        arguments = {'update': True}
        ctx.obj['factory'](arguments, configuration).execute()
    else:
        print('\nNot updating library.')


@cli.command(options_metavar='', add_help_option=False)
@argument('command', metavar='<command>')
@pass_context
def help(ctx, command):
    """Shows help for a command.

    \b
    Examples:
      root help list
        -> Shows help for the list command.
    """
    # TODO: prints 'help' in usage, rather than command name
    if command in cli.commands:
        print(cli.commands[command].get_help(ctx))
    else:
        print('No such command: ' + command)


@cli.command(name='import', options_metavar='', add_help_option=False)
@argument('path', metavar='<path>', type=Path(exists=True))
@pass_context
def import_(ctx, path):
    """Imports new e-books.

    \b
   Examples:
      root import ~/Downloads/
        -> imports books from ~/Downloads/
    """
    arguments = {'import': True, '<path>': path}
    configuration = ctx.obj['configuration']
    res, err = ctx.obj['factory'](arguments, configuration).execute()
    if err:
        print(err.reason)
    else:
        print(res.message)
