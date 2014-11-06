#!/usr/bin/env python
# -*- coding utf-8 -*-
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
import xml.etree.ElementTree as ET
import yaml
import re

from os import path
from os import walk
from os import makedirs
from os.path import join
from shutil import copy2 as _copy


def load_metadata(epub_filename, search):
    """Reads an epub file and returns its OPS / OEBPS blob"""
    if not zipfile.is_zipfile(epub_filename):
        print "%s is not an epub file" % epub_filename
        return
    with zipfile.ZipFile(epub_filename, 'r') as epub_file:
        meta_data = None
        try:
            meta_data = epub_file.read("META-INF/container.xml")
        except Exception:
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

def move_to_library(srcpath, book, move=_copy):
    """Move files to the library
    """
    config = None
    try:
        with open("_config.yaml") as config_file:
            config = yaml.safe_load(config_file)
    except Exception:
        print "Failed to load configuration"
        return
    destination_dir = path.join(config['directory'], book['author'])
    destination_file = "%s.%s" % (book['title'], "epub")
    # FIXME --- fewer path.joins please
    destpath = path.join(destination_dir, _sanitize_path(destination_file))
    try:
        if not path.exists(destination_dir):
            makedirs(destination_dir)
    except OSError:
        print "Error creating path %s" % destination_dir
        return
    print "%s ->\n%s" % (path.basename(srcpath), destpath)
    try:
        move(srcpath, destpath)
    except IOError, ioerror:
        print "Error copying %s (%s)" % (srcpath, ioerror.errno)


def _sanitize_path(srcpath, replacements=None):
    """Takes a path (as a Unicode string) and makes sure that it is
    legal. Returns a new path. Only works with fragments; won't work
    reliably on Windows when a path begins with a drive letter. Path
    separators (including altsep!) should already be cleaned from the
    path components. If replacements is specified, it is used *instead*
    of the default set of replacements; it must be a list of (compiled
    regex, replacement string) pairs.
    """
    replacements = replacements or [
        (re.compile(ur'[\\/]'), u'_'),  # / and \ -- forbidden everywhere.
        (re.compile(ur'^\.'), u'_'),  # Leading dot (hidden files on Unix).
        (re.compile(ur'[\x00-\x1f]'), u''),  # Control characters.
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


def usage(message=None):
    """Prints a usage message
    """
    if message is not None:
        print message
    print """Usage
Do stuff
"""

def do_import(srcpath, search):
    """TODO"""
    count = 0
    for (srcpath, dirnames, filenames) in walk(srcpath):
        for filename in filenames:
            if filename.endswith(".epub"):
                filepath = join(srcpath, filename)
                content_xml = load_metadata(filepath, search)
                if content_xml is None:
                    print "Failed to process %s" % filename
                    continue
                book = load_ops_data(content_xml, search)
                move_to_library(filepath, book)
                count += 1
    print "Imported %s" % count, count is not 1 and "books" or "book"


def do_command(cmd, args):
    """TODO"""

    def locate_element(x, y):
        if x is None or y is None:
            return
        elements = [e for e in x.iter() if e.tag.endswith(y)]
        if elements is None or len(elements) < 1:
            return
        return elements[0]

    if cmd == "import":
        if len(args) < 1:
            usage("%d is not the right number of arguments for %s"
                  % (len(args), cmd))
            return
        do_import(args[0], locate_element)
    elif cmd == "reimport":
        pass
    else:
        usage("%s is not a command" % cmd)


def main(args):
    """Does the main things."""
    if len(args) < 2:
        usage()
        return
    do_command(args[1], args[2:])


if __name__ == '__main__':
    main(sys.argv)
