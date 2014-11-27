#!/usr/bin/env python
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
"""Unit Tests.
"""

import unittest

import root

class TestStringManipulation(unittest.TestCase):
    """Tests
    """
    def test_author_normalisation(self):
        self.assertEqual("Foo Bar", root._author("Bar, Foo"))
        self.assertEqual("Eggs Spam", root._author("Spam, Eggs"))


    def test_path_normalisation(self):
        c = root._configuration()  # test defaults
        [self.assertEqual(e, root._clean_path(a, c)) for e, a in
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
