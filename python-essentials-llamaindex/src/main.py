import os

from llama_index.core import Settings, SimpleDirectoryReader, VectorStoreIndex
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.llms.ollama import Ollama

MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2")
EMBED_MODEL = os.environ.get("OLLAMA_EMBED_MODEL", "nomic-embed-text")

QUESTIONS = [
    "What does the project use for PostgreSQL connection pooling?",
    "Which library turns a Python class into a command line interface?",
    "What is pgvector used for?",
]


def main() -> None:
    Settings.llm = Ollama(model=MODEL, request_timeout=120.0)
    Settings.embed_model = OllamaEmbedding(model_name=EMBED_MODEL)

    documents = SimpleDirectoryReader("data").load_data()
    print(f"loaded {len(documents)} documents")

    index = VectorStoreIndex.from_documents(documents)
    engine = index.as_query_engine()

    for question in QUESTIONS:
        answer = engine.query(question)
        print(f"\nQ: {question}")
        print(f"A: {answer}")


if __name__ == "__main__":
    main()
