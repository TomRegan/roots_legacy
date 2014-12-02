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
"""e-book formats
"""

import zipfile
import xml.etree.ElementTree as ET
import re

from urlparse import urljoin
from urllib import pathname2url as to_url
from hashlib import sha1


class BaseFormat(object):

    def load(self, srcpath):
        """Return a dict representing an e-book.
        """
        return {}

    def _author(self, string):
        """Return the normalised author name.
        """
        name = string.split(',')
        return len(name) == 1 and string or ' '.join([name[1], name[0]]).strip()

    def _isbn(self, number):
        """Return an ISBN given a (possibly malformed) string.
        """
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
                        return element.text
        return elements[0].text or elements[0]


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
            book['_url_path'] = urljoin('file:', to_url(srcpath))
            return book

    def _load_metadata(self, epub_filename):
        """Reads an epub file and returns its OPS / OEBPS blob.
        """
        term = self._configuration['terminal']
        if not zipfile.is_zipfile(epub_filename):
            term.warn("Not importing %s because it is not a .epub file.",
                      epub_filename.replace("./", ""))
            return
        with zipfile.ZipFile(epub_filename, 'r') as epub_file:
            meta_data = None
            try:
                meta_data = epub_file.read("META-INF/container.xml")
            except Exception:
                term.warn("Could not locate a container file in %s", epub_filename)
                return
            meta_xml = ET.fromstring(meta_data)
            full_path = self._search(meta_xml, "rootfile")
            if full_path is None:
                term.warn("Could not locate a metadata file in %s", epub_filename)
                return
            return ET.fromstring(epub_file.read(full_path.attrib["full-path"]))

    def _load_ops_data(self, xml_data):
        """Constructs a dictionary from OPS XML data.
        """
        return {
            'title': self._search(xml_data, 'title') or '',
            'author': self._author(self._search(xml_data, 'creator') or ''),
            'isbn': self._isbn(self._search(xml_data, 'identifier', 'isbn') or '')
        }
