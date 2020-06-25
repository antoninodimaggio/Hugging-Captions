import argparse
import glob
import json
import os
import re
import time
from functools import wraps
from langdetect import detect
from tqdm import tqdm


def time_function(func):
    """decorator to time a function """
    @wraps(func)
    def print_time(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        print(f'Finished {func.__name__!r} in {(end - start):.4f} secs')
        return result
    return print_time


def download_json(tag, caption_queries):
    """download json that contains captions"""
    if not os.path.exists('logging/instagram_scraper'):
        os.makedirs('logging')
    if not os.path.exists('json'):
        os.makedirs('json')
    cmd_str = f'instagram-scraper --media-types none --tag \
    {tag} --caption-queries {caption_queries} --log-destination \
    logging/instagram_scraper/ --destination json'
    os.system(cmd_str)


def parse_captions(json_path, min_likes):
    """parse json and put the captions in a list"""
    def only_english(caption):
        # make sure that the caption is in english (slow)
        try:
            if detect(caption) == 'en':
                return True
            return False
        except Exception:
            # something went wrong we do not want this caption
            return False

    def get_caption(post):
        try:
            return post['node']['edge_media_to_caption']['edges'][0]['node']['text']
        except Exception:
            # if there is no caption then we do not want it
            return None

    with open(json_path, 'rb') as f:
         data = json.load(f)

    post_list = data['edge_hashtag_to_media']['edges']
    caption_list = [get_caption(post) for post in post_list
                    if post['node']['edge_liked_by']['count'] >= min_likes
                    and only_english(get_caption(post))
                    and get_caption(post) != None]
    return caption_list


def remove_dumb(caption):
    """discard any caption that has any of these substrings"""
    # boring words, buisness promo, spam, ect.
    # not sure how I should deal with punctuation still
    punctuation = ['...', '---', '___', '_ _ _']
    special = ['@', '%']
    words = ['http', 'follow', 'link', 'comment', 'alcohol', 'order',
             'sale', 'www', 'subscribe',' clearance', 'twitter', 'money',
             'notifications', 'repost', 'facebook']
    dumb_stuff = punctuation + special + words
    if any(dumb.lower() in caption.lower() for dumb in dumb_stuff):
        return True
    return False


def remove_block_hashtags(caption):
    """attempt to remove hidden hashtags at the bottom of captions"""
    caption = caption.split('\n', 1)[0]
    clean_caption = caption.split('\u2022', 1)[0]
    return clean_caption


def remove_long_seq(caption, threshold=3):
    """if we have a bunch of hashtags in a row remove them"""
    hashtag_idx = [m.span() for m in re.finditer(r'\B#\w+', caption)]
    if len(hashtag_idx) >= threshold:
        return caption[:hashtag_idx[0][0]]
    return caption


def write_line_by_line(path, captions):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(captions)


# @time_function
def clean_captions(json_dir, min_likes):
    def clean(cap):
        cap = remove_block_hashtags(cap)
        cap = remove_long_seq(cap)
        return cap
    files = sorted(glob.glob(os.path.join(json_dir, "*.json")))
    ndim_captions  = [parse_captions(f, min_likes) for f in tqdm(files, desc='Parsing JSON')]
    captions = [cap for sublist in ndim_captions for cap in sublist]
    captions = [clean(cap) for cap in tqdm(captions, desc='Cleaning captions') if not remove_dumb(cap)]
    captions = '\n'.join([cap for cap in captions if len(cap.split()) >=3])
    return captions


@time_function
def run_clean(tag, caption_queries, min_likes):
    """download captions, clean captions, write clean captions"""
    download_json(tag, caption_queries)
    captions = clean_captions(f'./json/{tag}/', min_likes)
    write_line_by_line(f'./text/training_text/{tag}.txt', captions)


def main():
    parser = argparse.ArgumentParser(description='Pull and clean hashtag data')
    parser.add_argument('--tag', type=str, help='Hashtage page that you want to scrape exclude the #', required=True)
    parser.add_argument('--caption-queries', type=int, default=40, help='Each query returns ~150 captions (default: 100)')
    parser.add_argument('--min-likes', type=int, default=10, help='Only use captions with >= min_likes (default: 10)')
    args = parser.parse_args()
    run_clean(args.tag, args.caption_queries, args.min_likes)


if __name__ == '__main__':
    main()
