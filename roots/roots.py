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

"""
Usage:
  root import <path>
  root update
  root list [-ait] [<query>]...
  root fields
  root config [-p | -d | --path | --default]
  root test [<query>]...
  root help <command>
  root (-h | --help | --version)

Commands:
  import     Import new e-books.
  update     Update the library.
  list       Query the library.
  fields     Show fields that can be used in queries.
  config     Show the configuration.
  test       Test the new feature
  help       Show help for a sub-command.

Options:
  -h --help  Show this help.
  --version  Show version.
"""

from configuration import user_configuration, compile_regex
from command import command
from cli import cli


def main():
    """The entry point.
    """
    configuration = user_configuration()
    compile_regex(configuration)
    cli(obj={
        'configuration': configuration,
        'factory': command
    })


if __name__ == '__main__':
    main()
