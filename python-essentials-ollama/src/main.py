import os

import ollama

MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2")
EMBED_MODEL = os.environ.get("OLLAMA_EMBED_MODEL", "nomic-embed-text")


def chat_once() -> None:
    response = ollama.chat(
        model=MODEL,
        messages=[{"role": "user", "content": "In one sentence, what is Python?"}],
    )
    print("chat:", response["message"]["content"].strip())


def chat_stream() -> None:
    print("stream: ", end="", flush=True)
    stream = ollama.chat(
        model=MODEL,
        messages=[{"role": "user", "content": "Count from 1 to 5, numbers only."}],
        stream=True,
    )
    for chunk in stream:
        print(chunk["message"]["content"], end="", flush=True)
    print()


def embed() -> None:
    result = ollama.embeddings(model=EMBED_MODEL, prompt="hello world")
    vector = result["embedding"]
    print(f"embedding model: {EMBED_MODEL} dims: {len(vector)}")
    print(f"embedding head: {[round(v, 4) for v in vector[:5]]}")


def main() -> None:
    print(f"model: {MODEL}")
    chat_once()
    chat_stream()
    embed()


if __name__ == "__main__":
    main()
