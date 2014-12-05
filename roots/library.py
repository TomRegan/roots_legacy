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

from string import digits


class IsbndbService(object):

    """Provides e-book information by claaing the isbndb api.
    """

    _blacklist = ['and']

    def __init__(self, configuration):
        self._configuration = configuration

    def request(self, books):
        """Given a list of books, returns an updated list of
        books.
        """
        results = []
        api_key = self._configuration['isbndb']['key']
        request_base = 'http://isbndb.com/api/v2/yaml/' + api_key
        for book in books:
            request = '%s/book/%s' % (request_base, book['isbn'])
            r = requests.get(request)
            response = yaml.load(r.text)
            # it doesn't need doing properly yet!
            if 'data' not in response.keys():
                request = '%s/book/%s' % (
                    request_base, book['title'].replace(' ', '_').lower()
                )
                r = requests.get(request)
                response = yaml.load(r.text)
                print response
                if 'data' not in response.keys():
                    continue
            data = response['data'][0]
            results.append({
                'title': data['title'],
                'author': self._author(data),
                'isbn': data['isbn13'],
                'keywords': self._keywords(data),
                'description': data['summary']
            })
        return results

    def _keywords(self, data):
        """Takes an underscore-separated list of keywords and
        returns a list of keywords with blacklisted words removed
        and digits stripped.
        """
        subject_ids = data['subject_ids']
        return {
            keyword.translate(None, digits) for subject_ids in
            [subject_id.split('_') for subject_id in subject_ids]
            for keyword in subject_ids
            if keyword not in self._blacklist
        }

    def _author(self, data):
        return data['author_data'][0]['name']
