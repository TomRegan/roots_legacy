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
"""roots

Usage:
  root import <path>
  root (-h | --help | --version)

Options:
  -h --help  show this
"""

import zipfile
import xml.etree.ElementTree as ET
import yaml
import re

from os import path
from os import walk
from os import makedirs
from os.path import join
from shutil import copy2 as _copy
from docopt import docopt


def load_metadata(epub_filename, search):
    """Reads an epub file and returns its OPS / OEBPS blob
    """
    if not zipfile.is_zipfile(epub_filename):
        print "'%s' is not a .epub file" % epub_filename.replace("./", "")
        return
    with zipfile.ZipFile(epub_filename, 'r') as epub_file:
        meta_data = None
        try:
            meta_data = epub_file.read("META-INF/container.xml")
        except Exception:
            print "Could not locate a container file in '%s'" % epub_filename
            return
        meta_xml = ET.fromstring(meta_data)
        full_path = search(meta_xml, "rootfile")
        if full_path is None:
            print "Could not locate a metadata file in '%s'" % epub_filename
            return
        return ET.fromstring(epub_file.read(full_path.attrib["full-path"]))


def _isbn(number, old_length=0):
    """Return an ISBN given a (possibly malformed) string
    """
    length = len(number)
    if length == 0:
        return None
    if length == old_length:
        return int(number)
    if number.isdigit() and (length == 13 or length == 10):
        return int(number)
    return _isbn(''.join([x for x in number if x.isdigit()]), length)


def _author(string):
    """Return the normalised author name
    """
    name = string.split(',')
    return len(name) == 1 and string or ' '.join([name[1], name[0]]).strip()


def load_ops_data(xml_data, search):
    """Constructs a dictionary from OPS XML data
    """
    title = search(xml_data, "title") or ""
    author = search(xml_data, "creator") or ""
    isbn = search(xml_data, "identifier") or ""
    return {
        "title": title,
        "author": _author(author),
        "ISBN": _isbn(isbn)
    }


def move_to_library(srcpath, book, configuration=None, move=_copy):
    """Move files to the library
    """
    destination_dir = path.join(configuration['directory'], book['author'])
    destination_file = _sanitize_path(book['title'] + '.epub')
    try:
        if not path.exists(destination_dir):
            makedirs(destination_dir)
    except OSError:
        print "Error creating path '%s'" % destination_dir
        return
    destpath = path.join(destination_dir, destination_file)
    if configuration['import']['overwrite'] is False and path.isfile(destpath):
        print 'Not importing %s because overwrite is not configured.' % srcpath
        return False
    print "%s ->\n%s" % (path.basename(srcpath), destpath)
    try:
        move(srcpath, destpath)
    except IOError, ioerror:
        print "Error copying %s (%s)" % (srcpath, ioerror.errno)
        return False
    return True


def _sanitize_path(srcpath, replacements=None):
    """Takes a path (as a Unicode string) and makes sure that it is
    legal.
    """
    replacements = replacements or [
        (re.compile(ur'[\\/]'), u'_'),  # / and \ -- forbidden everywhere.
        (re.compile(ur'^\.'), u'_'),    # Leading dot (hidden files on Unix).
        (re.compile(ur'[\x00-\x1f]'), u''),    # Control characters.
        (re.compile(ur'[<>:"\?\*\|]'), u'_'),  # Windows "reserved characters".
        (re.compile(ur'\.$'), u'_'),  # Trailing dots.
        (re.compile(ur'\s+$'), u''),  # Trailing whitespace.
    ]
    comps = _components(srcpath)
    if not comps:
        return ''
    for i, comp in enumerate(comps):
        for regex, repl in replacements:
            comp = regex.sub(repl, comp)
        comps[i] = comp
    return path.join(*comps)


def _components(srcpath):
    """Return a list of the path components in path. For instance:

       >>> components('/a/b/c')
       ['a', 'b', 'c']

    The argument should *not* be the result of a call to `syspath`.
    """
    comps = []
    ances = _ancestry(srcpath)
    for anc in ances:
        comp = path.basename(anc)
        if comp:
            comps.append(comp)
        else:  # root
            comps.append(anc)
    last = path.basename(srcpath)
    if last:
        comps.append(last)
    return comps


def _ancestry(srcpath):
    """Return a list consisting of path's parent directory, its
    grandparent, and so on. For instance:

       >>> ancestry('/a/b/c')
       ['/', '/a', '/a/b']

    The argument should *not* be the result of a call to `syspath`.
    """
    out = []
    last_path = None
    while srcpath:
        srcpath = path.dirname(srcpath)
        if srcpath == last_path:
            break
        last_path = srcpath
        if srcpath:
            # don't yield ''
            out.insert(0, srcpath)
    return out


def do_import(configuration):
    """TODO"""
    search = configuration['search']
    count = 0
    for srcpath, _, filenames in walk(configuration['srcpath']):
        for filename in filenames:
            if filename.endswith(".epub"):
                filepath = join(srcpath, filename)
                content_xml = load_metadata(filepath, search)
                if content_xml is None:
                    print "Failed to process '%s'" % filename
                    continue
                book = load_ops_data(content_xml, search)
                if move_to_library(filepath, book, configuration):
                    count += 1
    print "Imported %s" % count, count is not 1 and "books" or "book"


def do_command(arguments, configuration):
    """TODO"""
    def locate_element(x, y):
        if x is None or y is None:
            return
        elements = [e for e in x.iter() if e.tag.endswith(y)]
        if elements is None or len(elements) < 1:
            return
        return elements[0].text or elements[0]

    configuration['search'] = locate_element
    if arguments['import']:
        srcpath = arguments['<path>']
        if path.isfile(srcpath):
            print "source path should not be a file (%s)" % srcpath
            return
        configuration['srcpath'] = srcpath
        do_import(configuration)


def _configuration():
    """Loads YAML configuration.
    """
    try:
        with open("_config.yaml") as config_file:
            return yaml.safe_load(config_file)
    except Exception:
        print "Failed to load configuration"
        return False


def main():
    """TODO"""
    arguments = docopt(__doc__, version='0.0.1')
    configuration = _configuration()
    do_command(arguments, configuration)


if __name__ == '__main__':
    main()
