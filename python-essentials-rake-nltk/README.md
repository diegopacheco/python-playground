# python-essentials-rake-nltk

Keyword and key-phrase extraction with RAKE (Rapid Automatic Keyword Extraction) on top of NLTK.

### What it does

`src/main.py` feeds a paragraph to `Rake`, which splits it on stopwords and punctuation, scores the candidate phrases by word degree over frequency, and prints the top ranked phrases with their scores.

### Features

- RAKE unsupervised keyword extraction
- NLTK stopwords and tokenizers
- Ranked phrases with numeric scores

### Stack

- Python 3.14.6
- rake-nltk (NLTK)

### Architecture

`run.sh` -> `src/main.py` builds a `Rake` instance -> `extract_keywords_from_text` tokenizes and splits on stopwords -> `get_ranked_phrases_with_scores` returns scored phrases sorted high to low.

### Install

Downloads the NLTK `stopwords` and `punkt` data the first time.

```bash
./install-deps.sh
```

### Run

```bash
./run.sh
```

### Output

```
ranked keywords:
  34.7  supports multiple programming paradigms including structured
  32.3  high level general purpose programming language
  25.0  design philosophy emphasizes code readability
  15.7  batteries included language due
  9.0  comprehensive standard library
  6.7  functional programming
  4.0  significant indentation
  ...
```
