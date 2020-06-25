import unittest
import sys
import os
sys.path.insert(0, os.path.abspath('..'))
import download

class TestDownload(unittest.TestCase):

    def test_remove_dumb(self):
        dumb_caption = 'https://www.google.com is a dumb caption'
        result = download.remove_dumb(dumb_caption)
        with self.subTest
        self.assertTrue(result)


if __name__ == '__main__':
    unittest.main()
