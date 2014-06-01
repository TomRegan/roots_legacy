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
"""Dumps a bunch of data about epub files"""

import sys
import zipfile
import logging
import xml.etree.ElementTree as ET
import json

from os import path
from os import walk
from os.path import join


def load_metadata(epub_filename, search=lambda x, y: x[y]):
    """Reads an epub file and returns its OPS / OEBPS blob"""
    with zipfile.ZipFile(epub_filename, 'r') as epub_file:
        meta_data = None
        try:
            meta_data = epub_file.read("META-INF/container.xml")
        except Exception, e:
            logging.error(
                "Could not locate a container file in the epub bundle")
            return None
        meta_xml = ET.fromstring(meta_data)
        full_path = search(meta_xml, "rootfile").attrib["full-path"]
        if full_path is None:
            logging.error(
                "Could not locate a metadata file in the epub bundle")
            return None
        return ET.fromstring(epub_file.read(full_path))

def isbn(number, old_length=0):
    """Return an ISBN given a (possibly malformed) string"""
    length = len(number)
    if length == old_length:
        return None
    if length == 13 or length == 10:
        return int(number)
    return isbn(''.join([x for x in number if x.isdigit()]), length)

def load_ops_data(xml_data, search=lambda x, y: x[y]):
    """Constructs a dictionary from OPS XML data"""
    return {
        "title": search(xml_data, "title").text,
        "author": search(xml_data, "creator").text,
        "date": search(xml_data, "date").text,
        "ISBN": isbn(search(xml_data, "identifier").text),
        "language": search(xml_data, "language").text
    }

def main(args):
    """Does the main things."""
    logging.basicConfig(level=logging.DEBUG)

    locate_element = lambda x, y: [e for e in x.iter() if e.tag.endswith(y)][0]

    for (dirpath, dirnames, filenames) in walk(args[1]):
        for filename in filenames:
            if filename.endswith(".epub"):
                content_xml = load_metadata(
                    join(dirpath, filename), search=locate_element)
                book = load_ops_data(content_xml, search=locate_element)
                print path.basename(filename)
                print json.dumps(book, sort_keys=True, indent=2)

if __name__ == '__main__':
    main(sys.argv)
