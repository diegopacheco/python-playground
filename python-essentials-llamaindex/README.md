# python-essentials-llamaindex

A fully local Retrieval-Augmented Generation (RAG) pipeline with LlamaIndex: ingest local documents, embed and index them, then answer questions grounded in that content using Ollama.

### What it does

`src/main.py` reads the text files in `data/`, embeds them with `nomic-embed-text`, builds an in-memory `VectorStoreIndex`, and answers questions through a query engine backed by a local `llama3.2` model. Retrieval and generation both run on the machine, with no cloud API.

### Features

- Document ingestion with `SimpleDirectoryReader`
- Local embeddings via `OllamaEmbedding` (`nomic-embed-text`)
- Local generation via `Ollama` (`llama3.2`)
- In-memory `VectorStoreIndex` and query engine
- Answers grounded in the `data/` corpus

### Stack

- Python 3.14.6
- llama-index-core + llama-index-llms-ollama + llama-index-embeddings-ollama
- Ollama server (`llama3.2`, `nomic-embed-text`)

### Architecture

`test.sh` -> `start.sh` ensures Ollama is up and pulls the models -> `src/main.py` loads `data/` -> each chunk is embedded with `nomic-embed-text` and stored in a `VectorStoreIndex` -> a question is embedded, the nearest chunks are retrieved, and `llama3.2` composes the final answer from them.

### Requirements

Install Ollama from https://ollama.com and make sure it is running. `start.sh` pulls the models on first run.

### Install

```bash
./install-deps.sh
```

### Run

`start.sh` prepares the models, `test.sh` runs the whole flow, `stop.sh` stops any server `start.sh` launched.

```bash
./test.sh
```

To use a model you already have:

```bash
OLLAMA_MODEL=gemma4 ./run.sh
```

### Output

Generation is non-deterministic, so wording varies between runs. A real run:

```
loaded 2 documents

Q: What does the project use for PostgreSQL connection pooling?
A: The project uses psycopg2's ThreadedConnectionPool for connection pooling.

Q: Which library turns a Python class into a command line interface?
A: The fire library.

Q: What is pgvector used for?
A: It stores embeddings as a vector column and enables nearest-neighbor similarity search with SQL queries.
```
