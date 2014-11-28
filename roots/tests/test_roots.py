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

from roots import roots

class TestStringManipulation(unittest.TestCase):
    """Tests
    """
    def test_author_normalisation(self):
        self.assertEqual("Foo Bar", roots._author("Bar, Foo"))
        self.assertEqual("Eggs Spam", roots._author("Spam, Eggs"))


    def test_path_normalisation(self):
        c = roots._configuration()  # test defaults
        [self.assertEqual(roots._clean_path(i, c), e) for e, i in
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


    def test_isbn_determination(self):
        [self.assertEqual(roots._isbn(i), e) for e, i in
         [
             ("9783456789123", "9783456789123"),
             ("9793456789123", "9793456789123"),
             ("0123456789", "0123456789"),
             ("097522980X", "0-9752298-0-X"),
             ("097522980x", "0-9752298-0-x"),
             (None, ""),
             (None, '1'),  # too short
             (None, "01234567891234"),  # too long
             (None, "0a23456789123"),  # contains letters
             (None, "0123456789123")  # not a valid isbn
         ]
        ]


if __name__ == '__main__':
    unittest.main()
