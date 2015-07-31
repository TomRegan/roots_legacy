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

import unittest

from diff import diff, Added, Removed, Modified, Unchanged

class TestDiff(unittest.TestCase):
    def test_addition_is_tagged(self):
        expected = {
            'title': [Added('Gone Girl')],
            'author': [Added('Gillian Flynn')]
        }
        actual = diff({}, {
            'title': 'Gone Girl',
            'author': 'Gillian Flynn'
        })
        self.assertEqual(expected, actual)
        self.equalTypes(expected, actual)

    def test_removal_is_tagged(self):
        expected = {'title': [Unchanged('Gone'), Removed(' Girl')]}
        actual = diff({'title': 'Gone Girl'}, {'title': 'Gone'})
        self.assertEqual(expected, actual)
        self.equalTypes(expected, actual)

    def test_insertion_is_tagged(self):
        expected = {'title': [Added('Gone '), Unchanged('Girl')]}
        actual = diff({'title': 'Girl'}, {'title': 'Gone Girl'})
        self.assertEqual(expected, actual)
        self.equalTypes(expected, actual)

    def test_replacement_is_tagged(self):
        expected = {'title': [Unchanged('G'), Modified('irl')]}
        actual = diff({'title': 'Gone'}, {'title': 'Girl'})
        self.assertEqual(expected, actual)
        self.equalTypes(expected, actual)

    def equalTypes(self, a, b):
        for k in a.keys():
            [self.assertTrue(x) for x in
             [type(x) == type(y) for (x, y) in zip(a[k], b[k])]
            ]
