import argparse
import glob
import json
import os
import re
from functools import wraps
from langdetect import detect


def run_script(func):
    """ decorator to run forked instagram-scraper  """
    @wraps(func)
    def os_call(*args, **kwargs):
        python_str = f'instagram-scraper --media-types none --tag \
        {args[0]} --caption-queries {args[1]} --log-destination logging \
        --destination json'
        os.system(python_str)
    return os_call


@run_script
def download_hashtag_json(tag, caption_queries):
    if not os.path.exists('logging'):
        os.makedirs('logging')

    if not os.path.exists('json'):
        os.makedirs('json')


def get_captions(json_path, min_likes):

    def only_english(caption):
        """ make sure that the caption is in english (this is slow) """
        try:
            if detect(caption) == 'en':
                return True
            return False
        except Exception as e:
            # something went wrong we do not want this caption
            return False

    def caption(post):
        try:
            return post['node']['edge_media_to_caption']['edges'][0]['node']['text']
        except Exception as e:
            # if there is no caption then we do not want it
            return None

    with open(json_path, 'rb') as f:
         data = json.load(f)

    post_list = data['edge_hashtag_to_media']['edges']
    caption_list = [caption(post) for post in post_list
                    if post['node']['edge_liked_by']['count'] >= min_likes
                    and only_english(caption(post))
                    and caption(post) != None]
    return caption_list


def remove_dumb(caption):
    """ discard any caption that has any of these substrings """
    # make sure that these are all lower case
    # boring words, buisness promo, signs of low quality caption
    # this list is far from complete
    dumb_stuff = ['http', '@', 'follow','link', 'comment', '%',
                  'alcohol', 'order', 'sale', 'www', 'subscribe',
                  'clearance', '...']
    if any(dumb in caption.lower() for dumb in dumb_stuff):
        return True
    return False


def remove_block_hashtags(caption):
    """ people add these hidden hashtags at the bottom of their captions """
    # this list is not complete (still have new line issues)
    tokens = ['\n\n', '\n', '\u2022']
    for token in tokens:
        # deals with truncation issue (I am sure there is a way to fix this)
        if token in caption:
            caption = caption[0: caption.find(token)]
    return caption


def remove_long_seq(caption, threshold=3):
    """ if we have a bunch of hashtags in a row remove them """
    hashtag_idx = [m.span() for m in re.finditer(r'\B#\w+', caption)]
    if len(hashtag_idx) >= threshold:
        return caption[:hashtag_idx[0][0]]
    return caption


def write_line_by_line(path, total_text):
    with open(path, 'w') as f:
        f.write(total_text)


def extract(json_dir, min_likes):
    all_files = glob.glob(os.path.join(json_dir, "*.json"))
    print('Parsing JSON ...')
    n_list  = [get_captions(f, min_likes) for f in all_files]
    print('Done parsing JSON!')
    print('Starting to clean the data ...')
    # just leave all of these for loops for now, could improve in future
    caption_list = [cap for sublist in n_list for cap in sublist]
    caption_list = [cap for cap in caption_list if not remove_dumb(cap)]
    caption_list = [remove_block_hashtags(cap) for cap in caption_list]
    caption_list = [remove_long_seq(cap) for cap in caption_list if len(cap.split()) >=3]
    total_text = '\n'.join(caption_list)
    print('Done cleaning the data!')
    return total_text


def main():
    parser = argparse.ArgumentParser(description='Pull and clean hashtag data')
    parser.add_argument('--tag', type=str, help='Hashtage page that you want to scrape', required=True)
    parser.add_argument('--caption-queries', type=int, default=15, help='Each query returns ~150 captions (default: 15)')
    parser.add_argument('--min-likes', type=int, default=30, help='Only use captions with >= min_likes (default: 30)')
    args = parser.parse_args()
    download_hashtag_json(args.tag, args.caption_queries)
    total_text = extract(f'./json/{args.tag}/', args.min_likes)
    write_line_by_line(f'./text/training_text/{args.tag}.txt', total_text)


if __name__ == '__main__':
    main()
