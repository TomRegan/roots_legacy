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

"""Functions for working with the Library.
"""

from os.path import join, isfile
import pickle
import shelve


def load(configuration, subject, logger=None):
    """Returns data from the library.
    """
    library_path = join(configuration['system']['configpath'],
                        configuration['library'])
    if logger is not None:
        logger.debug('loading %s (exists: %s)', library_path, isfile(library_path))
    if not isfile(library_path):
        raise Exception('Cannot open library: %s', library_path)
    try:
        library = shelve.open(library_path, flag='r')
        if subject in library:
            return library[subject]
    finally:
        library.close()


def store(configuration, data, logger=None):
    """Stores data in the library.
    """
    library_path = join(configuration['system']['configpath'],
                        configuration['library'])
    if logger is not None:
        logger.debug('storing %s (exists: %s)', library_path, isfile(library_path))
    if not isfile(library_path):
        data['version'] = 1
    library = shelve.open(library_path)
    for subject, entry in data.iteritems():
        library[subject] = entry
    library.close()

def update(configuration, subject, data, function, logger=None):
    """Updates data in the library.
    """
    try:
        existing_data = load(configuration, subject, logger)
    except:
        existing_data = None
    if existing_data is not None:
        data = function(data, existing_data)
    store(configuration, {subject: data}, logger)
