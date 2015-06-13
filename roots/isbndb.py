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

"""Classes for interacting with the isbndb web service.
"""

import yaml
import requests

from string import digits

import storage


class Request(object):

    """Provides e-book information by claaing the isbndb api.
    """

    _blacklist = ['and']

    def __init__(self, configuration):
        self._configuration = configuration
        api_key = configuration['isbndb']['key']
        self._request_base = 'http://isbndb.com/api/v2/yaml/' + api_key
        self._term = configuration['terminal']

    def request(self, books):
        """Given a list of books, returns an updated list of
        books.
        """
        try:
            db = storage.load(self._configuration, 'isbndb')
            rate = db['rate']
        except:
            rate = self._configuration['isbndb']['rate']
            if rate is not None:
                self._term.debug('%s ISBNDB requests permitted.', rate)
            else:
                self._term.debug('ISBNDB requests not limited.')
        results = []

        for book in books:
            if rate is not None:
                if rate > 0:
                    rate -= 1
                else:
                    raise Exception("Calls to ISBNDB are throttled. "
                                    "Check the configuration.")

            response, err = self._http_request(book['isbn'])
            if err:
                response, err = self._http_request(book['title']
                                                   .replace(' ', '_').lower())
            if err:
                results.append(book)
                continue
            data = response['data'][0]
            results.append({
                'title': data['title'],
                'author': self._author(data),
                'isbn': data['isbn13'],
                'keywords': self._keywords(data),
                'description': data['summary']
            })
        if rate is not None:
            storage.store(self._configuration, {'isbndb': {'rate': rate}})
        return results

    def _http_request(self, query):
        if query is None or len(query) <= 0:
            return None, True
        request = '%s/book/%s' % (self._request_base, query)
        self._term.debug('Requesting %s', request)
        response = requests.get(request)
        if response.status_code != 200:
            self._term.debug('Response from server was %d.', response.status_code)
            return None, True
        response_data = yaml.load(response.text)
        return response_data, 'data' not in response_data.keys()

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
