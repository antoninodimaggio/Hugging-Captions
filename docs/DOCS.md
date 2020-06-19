## download.py

`download.py` downloads and cleans Instagram captions for a specific hashtag

**Flags**
* `--tag`: Hashtage page that you want to scrape for captions exclude the # [Required]
* `--caption-queries`: Each query returns ~150 captions (default: 30)
* `--min-likes`: Only use captions with >= min_likes (default: 30)

## tune_transformer.py
`tune_transformer.py` train the model and generate captions

**Flags**
* `--tag`: Hashtag page that we have scraped for captions exclude the # [Required]
* `--train`: Should we train the model (default: False)
* `--generate`: Should we generate captions (default: False)
* `--prompt`: Give the model something to start with when generating text 1-5 words will due (default= My\ Day)
* `--max-length`: Max length of caption text (default=60)
* `--min-length`: Min length of caption text (default=20)
* `--num-captions`: Number of captions to generate (default=40)
