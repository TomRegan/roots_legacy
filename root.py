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
import blessings

from os import path
from os import walk
from os import makedirs
from os.path import join
from shutil import copy2 as _copy
from docopt import docopt


class Terminal(blessings.Terminal):
    """Allows interaction with the terminal.
    """
    def warn(self, msg, *args):
        """Write a warning message to the terminal.
        """
        line_length = sum(len(x) for x in args)
        fmt = ''
        for word in msg.split():
            line_length += len(word)
            if line_length + len(word) > self.width:
                fmt += '\n' + word + ' '
                line_length = 0
            else:
                fmt += word + ' '
        print (self.red +
               fmt.replace('%s', self.yellow + "'%s'" + self.red) +
               self.normal) % args



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



def _clean_path(srcpath, configuration):
    """Takes a path (as a Unicode string) and makes sure that it is
    legal.
    """
    replacements = configuration['import']['replacements']
    for expression, replacement in replacements.iteritems():
        srcpath = expression.sub(replacement, srcpath)
    return srcpath


def do_import(configuration):
    """TODO"""
    moves = _consider_moves(configuration)
    count = move_to_library(moves, configuration)
    print "Imported %s" % count, count is not 1 and "books" or "book"


def _consider_moves(configuration):
    """Determines the files to be moved and their destinations.
    """
    search = configuration['search']
    library = configuration['directory']
    terminal = configuration['terminal']
    moves = []
    for basepath, _, filenames in walk(configuration['srcpath']):
        for filename in filenames:
            if not filename.endswith(".epub"):
                continue
            srcpath = join(basepath, filename)
            content_xml = load_metadata(srcpath, configuration)
            if content_xml is None:
                continue
            book = load_ops_data(content_xml, search)
            destination_dir = path.join(library, book['author'])
            destination_file = _clean_path(
                book['title'] + '.epub', configuration)
            destpath = path.join(destination_dir, destination_file)
            moves.append((srcpath, destpath, destination_dir))
    return moves


def load_metadata(epub_filename, configuration):
    """Reads an epub file and returns its OPS / OEBPS blob.
    """
    search = configuration['search']
    term = configuration['terminal']
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
        full_path = search(meta_xml, "rootfile")
        if full_path is None:
            term.warn("Could not locate a metadata file in %s", epub_filename)
            return
        return ET.fromstring(epub_file.read(full_path.attrib["full-path"]))


def move_to_library(moves, configuration, move=_copy):
    """Move files to the library
    """
    overwrite = configuration['import']['overwrite']
    terminal = configuration['terminal']
    count = 0
    for srcpath, destpath, destination_dir in moves:
        try:
            if not path.exists(destination_dir):
                makedirs(destination_dir)
        except OSError:
            terminal.warn("Error creating path %s", destination_dir)
            continue
        if not overwrite and path.isfile(destpath):
            terminal.warn("Not importing %s because it already exists in the "
                          "library.", srcpath)

            continue
        print "%s ->\n%s" % (path.basename(srcpath), destpath)
        try:
            move(srcpath, destpath)
            count += 1
        except IOError, ioerror:
            terminal.warn("Error copying %s (%s)", srcpath, ioerror.errno)
            continue
    return count


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
    configuration['terminal'] = Terminal()
    if arguments['import']:
        srcpath = arguments['<path>']
        if path.isfile(srcpath):
            print "source path should not be a file (%s)" % srcpath
            return
        configuration['srcpath'] = srcpath
        do_import(configuration)


def _update(defaults, updates):
    """Updates a nested dictionary
    """
    for k, v in updates.iteritems():
        if type(v) is dict:
            replacement = _update(defaults.get(k, {}), v)
            defaults[k] = replacement
        else:
            defaults[k] = updates[k]
    return defaults


def _configuration():
    """Loads YAML configuration.
    """
    custom = {}
    default = {
        'directory': '~/Books',
        'import': {
            'replacements': {
                r'[\\/]': '_',
                r'^\.': '_',
                r'[\x00-\x1f]': '',
                r'[<>:"\?\*\|]': '_',
                r'\.$': '_',
                r'\s+$': ''
            },
            'overwrite': False
        }
    }
    try:
        with open("_config.yaml") as config_file:
            custom = yaml.safe_load(config_file)
    except Exception:
        print "Failed to load configuration"
    configuration = _update(default, custom)
    _compile_regex(configuration)
    return configuration


def _compile_regex(configuration):
    """Compiles regexes in the configuration
    """
    replacements = configuration['import']['replacements']
    configuration['import']['replacements'] = {
        re.compile(k): v for k, v in replacements.iteritems()
    }


def main():
    """TODO"""
    arguments = docopt(__doc__, version='0.0.1')
    configuration = _configuration()
    do_command(arguments, configuration)


if __name__ == '__main__':
    main()
