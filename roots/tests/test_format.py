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
"""Format unit tests.
"""

import unittest

from roots.format import BaseFormat
import xml.etree.ElementTree as etree


class FormatTest(unittest.TestCase):

    def test_author_normalisation(self):
        cls = BaseFormat()
        self.assertEqual("Foo Bar", cls._author("Bar, Foo"))
        self.assertEqual("Eggs Spam", cls._author("Spam, Eggs"))
        self.assertEqual("Arthur C. Clarke", cls._author("Arthur C. Clarke"))
        self.assertEqual("Arthur C. Clarke", cls._author("Clarke, Arthur C."))
        self.assertEquals(None, cls._author(''))
        self.assertEquals(None, cls._author(None))
        self.assertEquals("Bob and Vic", cls._author("Bob; Vic"))
        self.assertEquals("Bob and Vic", cls._author("Vic; Bob"))
        self.assertEquals("Bob, Rita and Sue", cls._author("Rita; Sue; Bob"))
        self.assertEquals("Foo Bar and Eggs Spam", cls._author("Bar, Foo; Spam, Eggs"))


    def test_isbn_determination(self):
        cls = BaseFormat()
        [self.assertEqual(cls._isbn(i), e) for e, i in
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
             (None, "0123456789123"),  # not a valid isbn
             (None, None)
         ]
        ]

    def test_xml_search_for_author(self):
        cls = BaseFormat()
        element = etree.fromstring(self._opf_helper(
            '<dc:creator opf:file-as="Brand, Russell" '
            'opf:role="aut">Russell Brand</dc:creator>'))
        self.assertEquals("Russell Brand", cls._search(element, 'creator'))

    def test_xml_search_for_title(self):
        cls = BaseFormat()
        element = etree.fromstring(self._opf_helper(
            '<dc:title>Revolution</dc:title>'
        ))
        self.assertEquals("Revolution", cls._search(element, 'title'))

    def test_xml_search_for_isbn(self):
        cls = BaseFormat()
        element = etree.fromstring(self._opf_helper(
            '<dc:identifier opf:scheme="ISBN">9781101882924</dc:identifier>'
            '<dc:identifier opf:scheme="MOBI-ASIN">B00LKJHTJU</dc:identifier>'
        ))
        self.assertEquals("9781101882924", cls._search(element, 'identifier', 'isbn'))

        element = etree.fromstring(self._opf_helper(
            '<dc:identifier opf:scheme="MOBI-ASIN">B00LKJHTJU</dc:identifier>'
            '<dc:identifier opf:scheme="ISBN">9781101882924</dc:identifier>'
        ))
        self.assertEquals("9781101882924", cls._search(element, 'identifier', 'isbn'))

    def test_xml_search_for_rootfile(self):
        cls = BaseFormat()
        element = etree.fromstring('<?xml version="1.0"?>'
                                   '<container version="1.0" xmlns="urn:oasis:'
                                   'names:tc:opendocument:xmlns:container">'
                                   '<rootfiles>'
                                   '<rootfile full-path="content.opf" media-'
                                   'type="application/oebps-package+xml"/>'
                                   '</rootfiles>'
                                   '</container>'
        )
        self.assertEquals("content.opf",
                          cls._search(element, 'rootfile').attrib['full-path'])

    def _opf_helper(self, element):
        return ('<?xml version="1.0" encoding="utf-8"?>'
                '<metadata '
                'xmlns:dc="http://purl.org/dc/elements/1.1/" '
                'xmlns:opf="http://www.idpf.org/2007/opf">'
                '%s'
                '</metadata>') % element

if __name__ == '__main__':
    unittest.main()
