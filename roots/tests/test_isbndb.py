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

"""ISBDDB unit tests.
"""

import yaml

from roots.isbndb import Service

import responses
import tempfile
import unittest


@unittest.skip("needs updating, rate throttling coupled to storage")
class TestIsbndb(unittest.TestCase):

    @responses.activate
    def test_response_includes_all_fields(self):
        input = [{
            'author': 'Gillian Flynn',
            'title': 'Gone Girl',
            'isbn': '9780297859383'
        }]

        responses.add(responses.GET,
                      'http://isbndb.com/api/v2/yaml/AAAAAAAA/book/9780297859383',
                      body=self.gone_girl_response, status=200,
                      content_type='text/xml; charset=utf-8')

        cls = Service(self.configuration)
        response = cls.request(input)
        self.assertEquals(1, len(responses.calls))
        self.assertEquals('Gillian Flynn', response[0]['author'])
        self.assertEquals('Gone Girl', response[0]['title'])
        self.assertEquals('9780297859383', response[0]['isbn'])
        self.assertEquals('SUMMARY', response[0]['description'])
        self.assertEquals({'literature', 'fiction', 'thriller', 'suspense',
                           'mystery'}, response[0]['keywords'])

    @responses.activate
    def test_lists_of_books_are_updated(self):
        input = [{
            'author': 'Gillian Flynn',
            'title': 'Gone Girl',
            'isbn': '9780297859383'
        }, {
            'author': 'Wil Wheaton',
            'title': 'Just a Geek',
            'isbn': '9780596806'
        }]

        responses.add(responses.GET,
                      'http://isbndb.com/api/v2/yaml/AAAAAAAA/book/9780297859383',
                      body=self.gone_girl_response, status=200,
                      content_type='text/xml; charset=utf-8')
        responses.add(responses.GET,
                      'http://isbndb.com/api/v2/yaml/AAAAAAAA/book/9780596806',
                      body=self.just_a_geek_response, status=200,
                      content_type='text/xml; charset=utf-8')

        cls = Service(self.configuration)
        response = cls.request(input)
        self.assertEquals(2, len(responses.calls))
        self.assertEquals(2, len(response))
        self.assertEquals('Wil Wheaton', response[1]['author'])
        self.assertEquals('Just a Geek', response[1]['title'])
        self.assertEquals('9789780596804', response[1]['isbn'])
        self.assertEquals('', response[1]['description'])
        self.assertEquals({'wheaton', 'wil', 'television', 'actors',
                           'actresses', 'united', 'states', 'biography',
                           'webmasters', 'fame'}, response[1]['keywords'])

    @responses.activate
    def test_error_received_from_service(self):
        input = [{
            'author': 'Gillian Flynn',
            'title': 'Gone Girl',
            'isbn': '0999999X'
        }]

        responses.add(responses.GET,
                      'http://isbndb.com/api/v2/yaml/AAAAAAAA/book/0999999X',
                      body=yaml.dump({
                          'error': 'Unable to locate 0999999X'
                      }, default_flow_style=False),
                      content_type='text/xml; charset=utf-8')
        responses.add(responses.GET,
                      'http://isbndb.com/api/v2/yaml/AAAAAAAA/book/gone_girl',
                      body=self.gone_girl_response, status=200,
                      content_type='text/xml; charset=utf-8')

        cls = Service(self.configuration)
        response = cls.request(input)
        self.assertEquals(2, len(responses.calls))
        self.assertEquals(1, len(response))
        self.assertEquals('Gillian Flynn', response[0]['author'])
        self.assertEquals('Gone Girl', response[0]['title'])
        self.assertEquals('9780297859383', response[0]['isbn'])
        self.assertEquals('SUMMARY', response[0]['description'])
        self.assertEquals({'literature', 'fiction', 'thriller', 'suspense',
                           'mystery'}, response[0]['keywords'])


    @responses.activate
    def test_the_correct_auth_key_is_used(self):
        input = [{
            'author': 'Gillian Flynn',
            'title': 'Gone Girl',
            'isbn': '0999999X'
        }]

        responses.add(responses.GET,
                      'http://isbndb.com/api/v2/yaml/BBBBBB/book/0999999X',
                      body=self.gone_girl_response, status=200,
                      content_type='text/xml; charset=utf-8')

        configuration = self.configuration
        configuration['isbndb'] = {
            'key': 'BBBBBB',
            'limit': None
        }
        cls = Service(configuration)
        cls.request(input)
        self.assertEquals(
            'http://isbndb.com/api/v2/yaml/BBBBBB/book/0999999X',
            responses.calls[0].response.url)

    @responses.activate
    def test_no_data_found(self):
        input = [{
            'author': 'Gillian Flynn',
            'title': 'Gone Girl',
            'isbn': '0999999X'
        }]

        responses.add(responses.GET,
                      'http://isbndb.com/api/v2/yaml/AAAAAAAA/book/0999999X',
                      body=yaml.dump({
                          'error': 'Unable to locate 0999999X'
                      }, default_flow_style=False),
                      content_type='text/xml; charset=utf-8')
        responses.add(responses.GET,
                      'http://isbndb.com/api/v2/yaml/AAAAAAAA/book/gone_girl',
                      body=yaml.dump({
                          'error': 'Unable to locate 0999999X'
                      }, default_flow_style=False),
                      content_type='text/xml; charset=utf-8')

        cls = Service(self.configuration)
        response = cls.request(input)
        self.assertEquals('Gillian Flynn', response[0]['author'])
        self.assertEquals('Gone Girl', response[0]['title'])
        self.assertEquals('0999999X', response[0]['isbn'])

    @responses.activate
    def test_the_throttle_rate_is_not_exceeded(self):

        input = [{
            'author': 'Gillian Flynn',
            'title': 'Gone Girl',
            'isbn': '9780297859383'
        }, {
            'author': 'Wil Wheaton',
            'title': 'Just a Geek',
            'isbn': '9780596806'
        }, {
            'author': 'Another Author',
            'title': 'Should Never Request This',
            'isbn': '099999999X'
        }]

        responses.add(responses.GET,
                      'http://isbndb.com/api/v2/yaml/AAAAAAAA/book/9780297859383',
                      body=self.gone_girl_response, status=200,
                      content_type='text/xml; charset=utf-8')
        responses.add(responses.GET,
                      'http://isbndb.com/api/v2/yaml/AAAAAAAA/book/9780596806',
                      body=self.just_a_geek_response, status=200,
                      content_type='text/xml; charset=utf-8')

        configuration = self.configuration
        configuration['isbndb'] = {
            'key': 'AAAAAAAA',
            'limit': 2
        }
        cls = Service(configuration)

        try:
            cls.request(input)
        except:
            pass
        self.assertEquals(2, len(responses.calls))

    @responses.activate
    def test_the_throttle_rate_is_not_exceeded_over_multiple_calls(self):
        input = [{
            'author': 'Gillian Flynn',
            'title': 'Gone Girl',
            'isbn': '0999999X'
        }]

        responses.add(responses.GET,
                      'http://isbndb.com/api/v2/yaml/AAAAAAAA/book/0999999X',
                      body=self.gone_girl_response, status=200,
                      content_type='text/xml; charset=utf-8')

        configuration = self.configuration
        configuration['isbndb'] = {
            'key': 'AAAAAAAA',
            'limit': 1
        }
        cls = Service(configuration)

        try:
            cls.request(input)
            cls.request(input)
        except:
            pass
        self.assertEquals(1, len(responses.calls))


    gone_girl_response = yaml.dump({
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
    }, default_flow_style=False)

    just_a_geek_response = yaml.dump({
        'data': [{
            'isbn10': '9780596806',
            'isbn13': '9789780596804',
            'summary': '',
            'author_data': [{
                'id': 'wil_wheaton',
                'name': 'Wil Wheaton'
            }],
            'subject_ids': [
                'wheaton_wil1',
                'television_actors_and_actresses_united_states_biography1',
                'webmasters_united_states_biography1',
                'fame1'
            ],
            'title': 'Just a Geek'
        }],
        'index_searched': 'isbn'
    }, default_flow_style=False)

    configuration = {
        'isbndb': {
            'key': 'AAAAAAAA',
            'limit': None
        },
        'system': {
            'configpath': tempfile.mkdtemp()
        },
        'library': 'library.db',
    }


if __name__ == '__main__':
    unittest.main()
