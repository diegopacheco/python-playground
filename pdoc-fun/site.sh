#!/bin/bash

printf "Serving documentation at http://localhost:8000\n"
python3 -m http.server --directory ./docs 8000