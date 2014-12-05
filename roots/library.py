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

import yaml
import requests


class IsbndbService(object):
    def __init__(self, configuration):
        self._configuration = configuration

    def request(self, books):
        r = requests.get(
            'http://isbndb.com/api/v2/yaml/AAAAAAAA/book/9780297859383'
        )
        data = yaml.load(r.text)['data'][0]
        return [{
            'title': data['title'],
            'author': self._author(data),
            'isbn': data['isbn13'],
            'keywords': self._keywords(data),
            'description': data['summary']
        }]

    def _keywords(self, data):
        subject_ids = data['subject_ids']
        return {
            keyword for subject_ids in
            [subject_id.split('_') for subject_id in subject_ids]
            for keyword in subject_ids
        }

    def _author(self, data):
        return data['author_data'][0]['name']
