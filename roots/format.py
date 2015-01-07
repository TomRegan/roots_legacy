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

"""e-book formats
"""

import zipfile
import xml.etree.ElementTree as ET
import re

from urlparse import urljoin
from urllib import pathname2url as to_url
from hashlib import sha1
from HTMLParser import HTMLParser


class BaseFormat(object):

    def load(self, srcpath):
        """Return a dict representing an e-book.
        """
        return {}

    def _author(self, string):
        """Return the normalised author name.
        """
        if string is None or len(string) == 0:
            return None
        names = sorted({x.strip() for x in string.split(';')})
        authors = self._reverse_csv_list(names)
        init, last = authors[:-1], authors[-1]
        if len(init) != 0:
            return ', '.join(init) + ' and ' + last
        return last

    def _reverse_csv_list(self, list):
        """If elements in a list are comma separated, and the comma
        is removed they are reversed, otherwise they are unchanged.
        ['b, a', 'c d'] -> ['a b', 'c d']
        """
        return [' '.join([first.strip(), last.strip()])
                if first is not None else last for (last, first) in
                [name.split(',') if len(name.split(',')) == 2 else (name, None)
                 for name in list]]

    def _isbn(self, number):
        """Return an ISBN given a (possibly malformed) string.
        """
        if number is None or len(number) == 0:
            return
        number = number.replace('-', '')
        expr = (r'^[^\d]*('
                r'(97[8|9])?'  # ean, excluded if ISBN-10
                r'\d{2}'       # group
                r'\d{4}'       # registrant
                r'\d{3}'       # publication
                r'[\d|xX]'     # check
                r')[^\d]*$')
        matches = re.search(expr, number)
        return matches is not None and matches.group(1) or None

    def _search(self, element, tag_name, attribute=None):
        if element is None or tag_name is None:
            return
        elements = [e for e in element.iter() if e.tag.endswith(tag_name)]
        if elements is None or len(elements) < 1:
            return
        elif attribute is not None:
            for element in elements:
                for attr in element.items():
                    if attr[1].lower() == attribute.lower():
                        return self._unescape(element.text)
        return self._unescape(elements[0].text or elements[0])

    def _unescape(self, string):
        return HTMLParser().unescape(string)


class EpubFormat(BaseFormat):

    def __init__(self, configuration):
        self._configuration = configuration

    def load(self, srcpath):
        """Reads the metadata from an ebook file.
        """
        content_xml = self._load_metadata(srcpath)
        if content_xml is not None:
            book = self._load_ops_data(content_xml)
            if self._configuration['import']['hash']:
                with open(srcpath, 'rb') as zipfile:
                    book['_sha_hash'] = sha1(zipfile.read()).hexdigest()
            return book

    def _load_metadata(self, epub_filename):
        """Reads an epub file and returns its OPS / OEBPS blob.
        """
        if not zipfile.is_zipfile(epub_filename):
            raise Exception("Not importing %s because it is not a .epub file.",
                            epub_filename.replace("./", ""))
        with zipfile.ZipFile(epub_filename, 'r') as epub_file:
            meta_data = None
            try:
                meta_data = epub_file.read("META-INF/container.xml")
            except Exception:
                raise Exception("Could not locate a container file in %s.",
                                epub_filename)
            meta_xml = ET.fromstring(meta_data)
            full_path = self._search(meta_xml, "rootfile")
            if full_path is None:
                raise Exception("Could not locate a metadata file in %s.",
                                epub_filename)
            return ET.fromstring(epub_file.read(full_path.attrib["full-path"]))

    def _load_ops_data(self, xml_data):
        """Constructs a dictionary from OPS XML data.
        """
        title = self._search(xml_data, 'title')
        author = self._author(self._search(xml_data, 'creator'))
        isbn = self._isbn(self._search(xml_data, 'identifier', 'isbn'))
        if isbn is None:
            isbn = ''
        if author is None or title is None:
            raise Exception("Required metadata is missing.")
        return {
            'title': title,
            'author': author,
            'isbn': isbn
        }
