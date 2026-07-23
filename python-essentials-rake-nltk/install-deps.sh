#!/bin/bash

pip3 install -r requirements.txt
python3 -c "import nltk; nltk.download('stopwords'); nltk.download('punkt'); nltk.download('punkt_tab')"
