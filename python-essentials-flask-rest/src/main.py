from flask import Flask, jsonify, request, abort

app = Flask(__name__)

books = {1: {"id": 1, "title": "Clean Code", "author": "Robert Martin"}}
next_id = {"value": 2}


@app.get("/books")
def list_books():
    return jsonify(list(books.values()))


@app.get("/books/<int:book_id>")
def get_book(book_id):
    if book_id not in books:
        abort(404, description="book not found")
    return jsonify(books[book_id])


@app.post("/books")
def create_book():
    body = request.get_json(force=True)
    book_id = next_id["value"]
    next_id["value"] += 1
    books[book_id] = {"id": book_id, "title": body["title"], "author": body["author"]}
    return jsonify(books[book_id]), 201


@app.put("/books/<int:book_id>")
def replace_book(book_id):
    if book_id not in books:
        abort(404, description="book not found")
    body = request.get_json(force=True)
    books[book_id] = {"id": book_id, "title": body["title"], "author": body["author"]}
    return jsonify(books[book_id])


@app.patch("/books/<int:book_id>")
def update_book(book_id):
    if book_id not in books:
        abort(404, description="book not found")
    body = request.get_json(force=True)
    books[book_id].update(body)
    return jsonify(books[book_id])


@app.delete("/books/<int:book_id>")
def delete_book(book_id):
    if book_id not in books:
        abort(404, description="book not found")
    removed = books.pop(book_id)
    return jsonify({"deleted": removed})


if __name__ == "__main__":
    app.run(port=5000)
