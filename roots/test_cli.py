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

"""Test for cli.
"""

import unittest

from files import _clean_path
from cli import update
from click.testing import CliRunner


class TestCli(unittest.TestCase):
    def test_config_should_succeed(self):
        runner = CliRunner()
        result = runner.invoke(update)
        # TODO: how to inject context into tests?
        #self.assertEqual(0, result.exit_code)


if __name__ == '__main__':
    unittest.main()