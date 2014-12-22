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
import pickle


def load(configuration):
    """Returns a list of books in the library.
    """
    library_path = join(configuration['system']['configpath'],
                        configuration['library'])
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
    if isfile(library_path):
        with open(library_path, 'a+b') as library_file:
            db = pickle.load(library_file)
            db['library'] = books
            pickle.dump(db, library_file)
    else:
        with open(library_path, 'wb') as library_file:
            db = {'version':'1', 'library':books}
            pickle.dump(db, library_file)
