# python-essentials-streamlit

A Streamlit data app with a text input, a slider, a live table, and a line chart built from a pandas DataFrame.

### How it works

`src/main.py` reads a name and a row count from widgets, builds a DataFrame of squares and cubes, and renders it as a table and a chart. Moving the slider re-runs the script and updates the page.

### Install

```bash
./install-deps.sh
```

### Run

```bash
./run.sh
```

Streamlit opens `http://localhost:8501` in the browser.

### Output

A web page showing a greeting, a slider, a table of `n / square / cube`, a line chart, and a "Show sum" button that reports the sum of squares.
