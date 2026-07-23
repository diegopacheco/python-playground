# python-essentials-bleach

Sanitize untrusted HTML and neutralize XSS with `bleach`, using tag and attribute allowlists.

### What it does

`src/main.py` takes a dirty HTML string containing a `<script>` tag and a `javascript:` link, then cleans it against an allowlist of tags and attributes, strips all tags in a second pass, and safely linkifies plain URLs.

### Features

- Tag allowlist (`p`, `b`, `a`)
- Attribute allowlist (`href` on `a`)
- Dangerous `<script>` and `javascript:` payloads removed
- Full tag stripping mode
- `linkify` to auto-wrap plain URLs

### Stack

- Python 3.14.6
- bleach

### Architecture

`run.sh` -> `src/main.py` passes the input through `bleach.clean` -> the html5lib parser rebuilds the DOM keeping only allowlisted tags and attributes -> sanitized markup is printed.

### Install

```bash
./install-deps.sh
```

### Run

```bash
./run.sh
```

### Output

```
dirty: <p>hello <script>alert("xss")</script> <a href="javascript:evil()">click</a> <b>world</b></p>
clean: <p>hello &lt;script&gt;alert("xss")&lt;/script&gt; <a>click</a> <b>world</b></p>
stripped: hello alert("xss") click world
linkified: visit <a href="http://example.com" rel="nofollow">http://example.com</a> now
```
