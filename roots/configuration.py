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
"""Configuration settings.
"""

from os import path
import yaml
import re


def default_configuration():
    """Returns default configuration.
    """
    return {
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
        'isbndb' : {
            'key' : None,
            'limit' : None
        },
        'list': {
            'table': False,
            'isbn': False
        },
        'system': {
            'configfile': 'Default configuration',
            'configpath': None
        }
    }


def user_configuration():
    """Returns user configuration.
    """
    custom = {}
    configuration = default_configuration()
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


def compile_regex(configuration):
    """Compiles regexes in the configuration
    """
    replacements = configuration['import']['replacements']
    configuration['import']['replacements'] = {
        re.compile(k): v for k, v in replacements.iteritems()
    }
