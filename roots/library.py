#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2014 Tom Regan
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

""" Functions for working with the Library.
"""

from os.path import join, isfile
from shutil import move
import pickle


def load(configuration):
    """Returns a list of books in the library.
    """
    library_path = join(configuration['system']['configpath'],
                        configuration['library'])
    configuration['terminal'].debug('loading %s (exists: %s)', library_path,
                                    isfile(library_path))
    if not isfile(library_path):
        raise Exception('Cannot open library: %s', library_path)
    with open(library_path, 'rb') as library_file:
        db = pickle.load(library_file)
    return db['library']


def store(configuration, books):
    """Stores a list of books in the library.
    """
    library_path = join(configuration['system']['configpath'],
                        configuration['library'])
    term = configuration['terminal']
    term.debug('storing %s (exists: %s)', library_path,
               isfile(library_path))
    if isfile(library_path):
        with open(library_path, 'rb+') as library_file:
            try:
                db = pickle.load(library_file)
                db['library'] = books
                term.debug("Loaded data: %s", db)
                library_file.seek(0)
                pickle.dump(db, library_file)
            except:
                backup_path = library_path + '.bak'
                move(library_path, backup_path)
                term.warn("The library may be corrupt. Created a back up of "
                          "%s (%s). You may want to remove this backup "
                          "file", library_path, backup_path)
                store(configuration, books)
    else:
        with open(library_path, 'wb') as library_file:
            db = {'version':'1', 'library':books}
            pickle.dump(db, library_file)
