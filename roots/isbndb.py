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

from datetime import date, timedelta
from collections import namedtuple
from string import digits

import storage

Rate = namedtuple('Rate', ['limit', 'date'])

class Service(object):
    """Provides e-book information by claaing the isbndb api.
    """
    class Throttle(object):
        """Enforces rate-throttling behaviour to limit excessive api calls.
        """
        def __init__(self, configuration):
            term = configuration['terminal']
            self._configuration = configuration
            try:
                db = storage.load(configuration, 'isbndb')
                self._rate = db['rate']
                if self._rate.date < date.today():
                    term.debug("Resetting limit, expired %s" % self._rate.date)
                    self._rate = Rate(limit=configuration['isbndb']['limit'],
                                      date=date.today())
            except:
                self._rate = Rate(limit=configuration['isbndb']['limit'],
                                  date=date.today())
            if self._rate is not None:
                term.debug('%s ISBNDB requests permitted on %s.',
                           self._rate.limit, self._rate.date)
            else:
                term.debug('ISBNDB requests not limited.')

        def check(self):
            """Throws an exception if the throttle rate has been exhausted.
            """
            if self._rate is not None:
                if self._rate.limit > 0:
                    new_limit = self._rate.limit - 1
                    storage.store(self._configuration, {
                        'isbndb': {
                            'rate': Rate(limit=new_limit, date=date.today())
                        }
                    })
                else:
                    raise Exception("Calls to ISBNDB are throttled. "
                                    "Check the configuration.")

    _blacklist = set(['and', 'of', 'is', 'but', 'for', 'or', 'nor' 'from',
                      'by', 'on', 'at', 'to', 'a', 'an', 'the', 'up'])

    def __init__(self, configuration):
        self._configuration = configuration
        api_key = configuration['isbndb']['key']
        self._request_base = 'http://isbndb.com/api/v2/yaml/' + api_key
        self._term = configuration['terminal']
        self._throttle = self.Throttle(configuration)

    def request(self, books):
        """Given a list of books, returns an updated list of
        books.
        """
        results = []
        for book in books:
            self._throttle.check()
            response, err = self._http_request(book['isbn'])
            if err:
                response, err = self._http_request(
                    book['title'].replace(' ', '_').lower())
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
        return results

    def _http_request(self, query):
        """Sends an http request.
        """
        if query is None or len(query) <= 0:
            return None, True
        request = '%s/book/%s' % (self._request_base, query)
        self._term.debug('Requesting %s', request)
        response = requests.get(request)
        status = response.status_code
        if status != 200:
            self._term.debug('Response from server was %d.', status)
            return None, True
        response_data = yaml.load(response.text)
        self._term.debug('response: ' + str(response_data))
        return response_data, 'data' not in response_data.keys()

    def _keywords(self, data):
        """Takes an underscore-separated list of keywords and
        returns a list of keywords with blacklisted words removed
        and digits stripped.
        """
        subject_ids = data['subject_ids']
        return { keyword for keyword in {
            keyword.translate(None, digits) for subject_ids in
            [subject_id.split('_') for subject_id in subject_ids]
            for keyword in subject_ids
            if keyword not in self._blacklist
        } if len(keyword) > 0 }

    def _author(self, data):
        return data['author_data'][0]['name']
