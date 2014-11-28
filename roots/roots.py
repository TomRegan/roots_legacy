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
"""
Usage:
  root import <path>
  root update
  root list [-a | -i] [<query>]...
  root config [-p | -d | --path | --default]
  root help <command>
  root (-h | --help | --version)

Commands:
  import     Import new e-books.
  update     Update the library.
  list       Query the library.
  config     Show the configuration.
  help       Show help for a sub-command.

Options:
  -h --help  Show this help.
  --version  Show version.
"""

import zipfile
import xml.etree.ElementTree as ET
import yaml
import re
import blessings
import pickle

from os import path, walk, makedirs
from os.path import join, expanduser
from shutil import copy2 as _copy
from docopt import docopt
from urlparse import urljoin
from urllib import pathname2url as to_url
from hashlib import sha1

from command import List, Help


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
    term = Terminal()
    configuration['terminal'] = term
    if arguments['import']:
        srcpath = arguments['<path>']
        if path.isfile(srcpath):
            term.warn("source path should not be a file: %s", srcpath)
            return
        configuration['system']['srcpath'] = srcpath
        do_import(configuration)
    elif arguments['update']:
        do_update(configuration)
    elif arguments['config']:
        do_config(arguments, configuration)
    elif arguments['list']:
        List(arguments, configuration).do
    elif arguments['help']:
        Help(arguments, configuration).do


def do_import(configuration):
    """TODO"""
    moves = _consider_moves(configuration)
    count = _move_to_library(moves, configuration)
    print 'Imported %d %s.' % (count, count != 1 and 'books' or 'book')


def _consider_moves(configuration):
    """Determines the files to be moved and their destinations.
    """
    library = configuration['directory']
    moves = []
    for basepath, _, filenames in walk(configuration['system']['srcpath']):
        for filename in filenames:
            if not filename.endswith(".epub"):
                continue
            srcpath = join(basepath, filename)
            book = _load_book_data(srcpath, configuration)
            if book is None:
                continue
            destination_dir = path.join(library, book['author'])
            destination_file = _clean_path(
                book['title'] + '.epub', configuration)
            destpath = path.join(destination_dir, destination_file)
            moves.append((srcpath, destpath, destination_dir))
    return moves


def _load_book_data(srcpath, configuration):
    """Reads the metadata from an ebook file.
    """
    content_xml = _load_metadata(srcpath, configuration)
    if content_xml is not None:
        book = _load_ops_data(content_xml, configuration)
        if configuration['import']['hash']:
            with open(srcpath, 'rb') as zipfile:
                book['sha_hash'] = sha1(zipfile.read()).hexdigest()
        book['url_path'] = urljoin('file:', to_url(srcpath))
        return book


def _load_metadata(epub_filename, configuration):
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


def _load_ops_data(xml_data, configuration):
    """Constructs a dictionary from OPS XML data.
    """
    search = configuration['search']
    return {
        "title": search(xml_data, "title") or "",
        "author": _author(search(xml_data, "creator") or ""),
        "isbn": _isbn(search(xml_data, "identifier") or "")
    }


def _isbn(number, old_length=0):
    """Return an ISBN given a (possibly malformed) string.
    """
    number = number.replace('-', '')
    expr = (r'^[^\d]*('
            r'(97[8|9])?'  # ean
            r'\d{2}'       # group
            r'\d{4}'       # registrant
            r'\d{3}'       # publication
            r'[\d|xX]'     # check
            r')[^\d]*$')
    matches = re.search(expr, number)
    return matches is not None and matches.group(1) or None


def _author(string):
    """Return the normalised author name.
    """
    name = string.split(',')
    return len(name) == 1 and string or ' '.join([name[1], name[0]]).strip()


def _clean_path(srcpath, configuration):
    """Takes a path (as a Unicode string) and makes sure that it is
    legal.
    """
    replacements = configuration['import']['replacements']
    for expression, replacement in replacements.iteritems():
        srcpath = expression.sub(replacement, srcpath)
    return srcpath


def _move_to_library(moves, configuration, move=_copy):
    """Move files to the library
    """
    terminal = configuration['terminal']
    count = 0
    for srcpath, destpath, destination_dir in moves:
        try:
            if not path.exists(destination_dir):
                makedirs(destination_dir)
        except OSError:
            terminal.warn("Error creating path %s", destination_dir)
            continue
        if not configuration['import']['overwrite'] and path.isfile(destpath):
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


def do_update(configuration):
    """TODO"""
    books = []
    directory = configuration['directory']
    if not path.exists(directory):
        configuration['terminal'].warn('Cannot open library: %s', directory)
        return
    for basepath, _, filenames in walk(directory):
        for filename in filenames:
            if filename.endswith(".epub"):
                srcpath = join(basepath, filename)
                books.append(_load_book_data(srcpath, configuration))
    library = path.join(configuration['system']['configpath'],
                        configuration['library'])
    with open(library, 'wb') as library_file:
        pickle.dump(books, library_file)
    count = len(books)
    print 'Imported %d %s.' % (count, count != 1 and 'books' or 'book')


def do_config(arguments, configuration):
    """Prints configuration.
    """
    if arguments['-p'] or arguments['--path']:
        print configuration['system']['configfile']
    elif arguments['-d'] or arguments['--default']:
        print yaml.dump(_configuration(default=True, display=True),
                        default_flow_style=False)
    else:
        print yaml.dump(_configuration(display=True), default_flow_style=False)


def _configuration(default=False, display=False):
    """Loads YAML configuration.
    """
    custom = {}
    configuration = {
        'library': 'library.db',
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
            'overwrite': False,
            'hash': False
        },
        'system': {
            'configfile': '(Default configuration)',
            'configpath': '(Default configuration)'
        }
    }
    if default:
        return configuration
    default_config_path = path.join(
        path.expanduser('~'), '.config/roots/config.yaml')
    config_path = ''
    for config_path in [default_config_path, '_config.yaml']:
        if path.exists(config_path):
            configuration['system'] = {
                'configfile': path.abspath(config_path),
                'configpath': path.dirname(path.abspath(config_path))
            }
            break
    try:
        with open(config_path) as config_file:
            custom = yaml.safe_load(config_file)
    except Exception:
        pass
    if custom is not None:
        configuration = _update(configuration, custom)
    if display:
        configuration.pop('system')
    else:
        _compile_regex(configuration)
    return configuration


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
