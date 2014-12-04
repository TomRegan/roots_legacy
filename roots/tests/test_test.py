#!/usr/bin/env python

import unittest
from roots.format import EpubFormat
from roots.configuration import default_configuration
from mock import Mock, patch

class TestTest(unittest.TestCase):
    def test_test(self):
        with patch.object(EpubFormat, 'load') as mock_load:
            mock_load.return_value = {
                'author': None
            }
            cls = EpubFormat({})
            self.assertEquals({'author':None}, cls.load(''))


if __name__ == '__main__':
    unittest.main()
