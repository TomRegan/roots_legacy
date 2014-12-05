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

from roots.configuration import default_configuration
from roots.library import IsbndbService

import requests
import responses

import unittest


class TestLibrary(unittest.TestCase):

    @responses.activate
    def test_expectations(self):
        c = default_configuration()
        c['isbndb'] = {
            'key': 'AAAAAAAA',
            'rate': 5
        }

        response = {
            'data': [{
                'isbn13': '9780297859383',
                'isbn10': '0297859382',
                'summary': 'SUMMARY',
                'author_data': [{
                    'id': 'gillian_flynn',
                    'name': 'Gillian Flynn'
                }],
                'subject_ids': [
                    'literature_fiction',
                    'mystery_thriller_suspense_mystery'
                ],
                'title': 'Gone Girl'
            }],
            'index_searched': 'isbn'
        }

        input = [{
            'author': 'Gillian Flynn',
            'title': 'Gone Girl',
            'isbn': '9780297859383'
        }]
        url = 'http://isbndb.com/api/v2/yaml/AAAAAAAA/book/9780297859383'
        responses.add(responses.GET, (url),
                      body=yaml.dump(response, default_flow_style=False),
                      status=200, content_type='text/xml; charset=utf-8')

        cls = IsbndbService({})
        response = cls.request(input)
        self.assertEquals('Gillian Flynn', response[0]['author'])
        self.assertEquals('Gone Girl', response[0]['title'])
        self.assertEquals('9780297859383', response[0]['isbn'])
        self.assertEquals('SUMMARY', response[0]['description'])
        self.assertEquals({'literature', 'fiction', 'thriller', 'suspense',
                           'mystery'}, response[0]['keywords'])


    # should handle lists of books
    # should handle missing isbn in request
    # should handle missing data in response (isbn, author, title)
    # should use the correct auth key


if __name__ == '__main__':
    unittest.main()
