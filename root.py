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
import yaml

from os import path
from os import walk
from os import makedirs
from os.path import join
from shutil import copy2 as copy


def load_metadata(epub_filename, search):
    """Reads an epub file and returns its OPS / OEBPS blob"""
    if not zipfile.is_zipfile(epub_filename):
        print "%s is not an epub file" % epub_filename
        return
    with zipfile.ZipFile(epub_filename, 'r') as epub_file:
        meta_data = None
        try:
            meta_data = epub_file.read("META-INF/container.xml")
        except Exception, e:
            print "Could not locate a container file in the epub bundle"
            return
        meta_xml = ET.fromstring(meta_data)
        full_path = search(meta_xml, "rootfile")
        if full_path is None:
            print "Could not locate a metadata file in the epub bundle"
            return
        return ET.fromstring(epub_file.read(full_path.attrib["full-path"]))

def _isbn(number, old_length=0):
    """Return an ISBN given a (possibly malformed) string
    """
    length = len(number)
    if length == old_length:
        return int(number)
    if number.isdigit() and (length == 13 or length == 10):
        return int(number)
    return _isbn(''.join([x for x in number if x.isdigit()]), length)

def _author(string):
    """Return the normalised author name
    """
    name = string.split(',')
    return len(name) == 1  and string or ' '.join([name[1], name[0]]).strip()

def load_ops_data(xml_data, search):
    """Constructs a dictionary from OPS XML data
    """
    title = search(xml_data, "title")
    author = search(xml_data, "creator")
    isbn = search(xml_data, "identifier")
    return {
        "title": title is None and None or title.text,
        "author": author is None and None or _author(author.text),
        "ISBN": isbn is not None and _isbn(isbn.text) or None
    }

def move_to_library(srcpath, book):
    """Move files to the library
    """
    config = None
    try:
        with open("_config.yaml") as config_file:
            config = yaml.safe_load(config_file)
    except Exception, e:
        print "Failed to load configuration"
        return
    destination_dir = path.join(config['directory'], book['author'])
    destination_file = "%s.%s" % (book['title'], "epub")
    destpath = path.join(destination_dir, destination_file)
    try:
        if not path.exists(destination_dir):
            makedirs(destination_dir)
    except OSError, e:
        print "Error creating path %s" % destination_dir
        return
    print "%s ->\n%s" % (path.basename(srcpath), destpath)
    try:
        copy(srcpath, destpath)
    except IOError, e:
        print "Error copying %s (%s)" % (srcpath, e.errno)

def usage(message=None):
    """Prints a usage message
    """
    if message is not None:
        print message
    print """Usage
Do stuff
"""

def main(args):
    """Does the main things."""

    if len(args) < 2:
        usage()
        return

    command = args[1]

    if command not in ["import"]:
        usage("%s is not a command" % command)
        return

    if len(args) < 3:
        usage("%d is not the right number of arguments for %s"
              % (len(args) - 2, command))
        return

    dirpath = args[2]

    def locate_element(x, y):
        if x is None or y is None:
            return
        elements = [e for e in x.iter() if e.tag.endswith(y)]
        if elements is None or len(elements) < 1:
            return
        return elements[0]


    for (dirpath, dirnames, filenames) in walk(dirpath):
        for filename in filenames:
            if filename.endswith(".epub"):
                filepath = join(dirpath, filename)
                content_xml = load_metadata(filepath, search=locate_element)
                if content_xml is None:
                    print "Failed to process %s" % filename
                    continue
                book = load_ops_data(content_xml, search=locate_element)
                move_to_library(filepath, book)

if __name__ == '__main__':
    main(sys.argv)
