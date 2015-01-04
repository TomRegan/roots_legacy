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

    def _prefmt(self, pre, colour):
        return self.underline + colour + pre + self.normal + ": "

    def warn(self, msg, *args):
        """Write a warning message to the terminal.
        """
        replace_fmt = "'" + self.red + "%s" + self.normal +  "'"
        print (self._prefmt('Error', self.red)
               + msg.replace('%s', replace_fmt)
               + self.normal) % args

    def debug(self, msg, *args):
        """Write a debug message to the terminal.
        """
        if False:
            print (self._prefmt('Debug', self.blue) + msg) % args


def do_command(arguments, configuration):
    """TODO"""
    term = Terminal()
    configuration['terminal'] = term
    cmd = command(arguments, configuration)
    try:
        cmd.do()
    except Exception, e:
        if len(e.args) > 0:
            term.warn(e.args[0], *e.args[1:])
        else:
            term.warn("Unknown error")


def main():
    """TODO"""
    arguments = docopt(__doc__, version='1.0.0')
    configuration = user_configuration()
    compile_regex(configuration)
    do_command(arguments, configuration)


if __name__ == '__main__':
    main()
