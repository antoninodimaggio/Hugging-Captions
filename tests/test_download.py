import os
import sys
import unittest
sys.path.insert(0, os.path.abspath('..'))
import download

class TestDownload(unittest.TestCase):


    def test_remove_dumb(self):
        # these are dumb captions
        dumb_captions_true = ['https://www.google.com is a dumb caption',
                               'hello please follow is a dumb caption',
                               'Come get this free money.',
                               'I love using periods ....']
        for caption in dumb_captions_true:
            with self.subTest(caption=caption):
                result = download.remove_dumb(caption)
                self.assertTrue(result)

        # these are not dumb captions
        dumb_captions_false = ['That dog is very nice!',
                              'I can not get enough of the summer sun',
                              'This is so cool ..']
        for caption in dumb_captions_false:
            with self.subTest(caption=caption):
                result = download.remove_dumb(caption)
                self.assertFalse(result)


    def test_remove_block_hashtags(self):
        new_line = 'I wrote my caption \n\n\n #hello #Ilovetags #keepgoing #yes'
        bullet = 'What is your favorite caption!!!\u2022 #now #add #a #million'
        with self.subTest(new_line):
            self.assertEqual(download.remove_block_hashtags(new_line),
                             'I wrote my caption')
        with self.subTest(bullet):
            self.assertEqual(download.remove_block_hashtags(bullet),
                             'What is your favorite caption!!!')


    def test_remove_long_seq(self):
        lots_of_tags = 'Hi I love using #hashtags #becuase #of #how #nice #they #look'
        only_three_tags = 'Hi I love using #hashtags #becuase #of'
        with self.subTest(lots_of_tags):
            self.assertEqual(download.remove_long_seq(lots_of_tags, threshold=3),
                             'Hi I love using')
        with self.subTest(only_three_tags):
            self.assertEqual(download.remove_long_seq(only_three_tags, threshold=3),
                             'Hi I love using #hashtags #becuase #of')

                             
if __name__ == '__main__':
    unittest.main()
