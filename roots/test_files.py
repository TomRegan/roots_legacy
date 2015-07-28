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

"""Files unit tests.
"""

import unittest

from configuration import default_configuration, compile_regex
from files import _clean_path


class FilesTest(unittest.TestCase):

    def test_import_normalisation(self):
        c = default_configuration()
        c['terminal'] = None
        compile_regex(c)
        [self.assertEqual(_clean_path(c, i), e) for e, i in
         [
             ("Space_ The Final Frontier", "Space: The Final Frontier"),
             ("Spaces, The Final Frontier", "Spaces, The Final Frontier   "),
             ("_invisible", ".invisible"),
             ("visible_", "visible."),
             ("windows___nix_", "windows<>*nix?"),
             ("put _that_ in your _", "put _that_ in your |"),
             ("valid.epub", "valid.epub")
         ]
        ]


if __name__ == '__main__':
    unittest.main()
