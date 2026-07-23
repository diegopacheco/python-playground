# python-essentials-ollama

Run Llama (and other models) locally with the `ollama` Python client: chat, token streaming, and embeddings, no cloud API.

### What it does

`src/main.py` connects to a local Ollama server and performs three calls: a one-shot chat completion, a streamed chat completion printed token by token, and a text embedding with `nomic-embed-text`. The model is configurable through `OLLAMA_MODEL`.

### Features

- One-shot chat via `ollama.chat`
- Streamed responses token by token (`stream=True`)
- Text embeddings via `ollama.embeddings`
- Fully local inference, no API key
- Model selectable with `OLLAMA_MODEL` / `OLLAMA_EMBED_MODEL`

### Stack

- Python 3.14.6
- ollama (Python client)
- Ollama server + `llama3.2` and `nomic-embed-text` models

### Architecture

`test.sh` -> `start.sh` ensures the Ollama server is up and pulls the models -> `src/main.py` sends requests to `http://127.0.0.1:11434` -> Ollama runs the model locally and returns completions and embedding vectors.

### Requirements

Install Ollama from https://ollama.com and make sure it is running. `start.sh` pulls the models on first run.

### Install

```bash
./install-deps.sh
```

### Run

`start.sh` prepares the server and models, `test.sh` runs the whole flow, `stop.sh` stops any server `start.sh` launched.

```bash
./test.sh
```

To target a model you already have:

```bash
OLLAMA_MODEL=gemma4 ./run.sh
```

### Output

```
model: llama3.2
chat: Python is a high-level, interpreted programming language that is widely used for various purposes such as web development, data analysis, machine learning, and more due to its simplicity, flexibility, and large community of developers.
stream: 1
2
3
4
5
embedding model: nomic-embed-text dims: 768
embedding head: [-0.1523, -0.0307, -3.9119, 0.1917, 0.1337]
```
