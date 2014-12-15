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
  root list [-ait] [<query>]...
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
import blessings

from docopt import docopt

from command import command
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
    term = Terminal()
    configuration['terminal'] = term
    cmd = command(arguments, configuration)
    try:
        cmd.do()
    except Exception, e:
        term.warn(e.args[0], *e.args[1:])


def main():
    """TODO"""
    arguments = docopt(__doc__, version='1.0.0')
    configuration = user_configuration()
    compile_regex(configuration)
    do_command(arguments, configuration)


if __name__ == '__main__':
    main()
