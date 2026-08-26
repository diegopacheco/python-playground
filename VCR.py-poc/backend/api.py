import ast
import base64
import operator
import os
import random
import tempfile
import time
import uuid

import tapes

IMAGE_DIR = os.path.join(tempfile.gettempdir(), "vcr-poc-images")

MOVES = ["rock", "paper", "scissors"]
BEATS = {"rock": "scissors", "paper": "rock", "scissors": "paper"}

OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

SEED_BOOKS = [
    {"id": "b1", "title": "The Pragmatic Programmer", "author": "Hunt & Thomas", "year": 1999, "tags": "craft", "notes": "Still the best onboarding gift"},
    {"id": "b2", "title": "Domain-Driven Design", "author": "Eric Evans", "year": 2003, "tags": "design", "notes": "The blue book"},
    {"id": "b3", "title": "Release It!", "author": "Michael Nygard", "year": 2007, "tags": "resilience", "notes": "Stability and capacity patterns"},
    {"id": "b4", "title": "Accelerate", "author": "Forsgren, Humble, Kim", "year": 2018, "tags": "delivery", "notes": "The four key metrics"},
    {"id": "b5", "title": "A Philosophy of Software Design", "author": "John Ousterhout", "year": 2018, "tags": "design", "notes": "Deep modules over thin ones"},
]

SEED_NOTES = [
    {
        "id": "n1",
        "title": "How the tapes work",
        "body": "Every response the UI sees comes out of vcr.use_cassette(record_mode='none').",
        "todos": [
            {"id": "t1", "text": "Seed the cassettes", "done": True},
            {"id": "t2", "text": "Check X-Vcr-Played on the network tab", "done": False},
            {"id": "t3", "text": "Delete a tape and watch the endpoint vanish", "done": False},
        ],
    },
    {
        "id": "n2",
        "title": "Weekend",
        "body": "Nothing work related.",
        "todos": [{"id": "t4", "text": "Coffee beans", "done": False}, {"id": "t5", "text": "Bike tune-up", "done": False}],
    },
]

SEED_POSTS = [
    {
        "id": "p1",
        "title": "Recording a backend that never shipped",
        "body": "VCR.py replays HTTP interactions from YAML tapes. Point the UI at a player instead of a server and the frontend cannot tell the difference. The endpoints do not exist. The tapes do.",
        "image": "",
        "youtube": "dQw4w9WgXcQ",
        "created": "2026-08-01T10:00:00Z",
    },
    {
        "id": "p2",
        "title": "Tapes beat handwritten mocks",
        "body": "A cassette is a full recorded exchange: status line, headers, body. A handwritten mock is a guess about one of those three, and it starts drifting the day you write it.",
        "image": "https://images.unsplash.com/photo-1507842217343-583bb7270b66?w=900&q=70",
        "youtube": "",
        "created": "2026-08-12T09:30:00Z",
    },
]

SEEDS = {
    "/books/list-books": {"items": SEED_BOOKS, "total": len(SEED_BOOKS)},
    "/calc/list-history": {"items": [], "total": 0},
    "/images/list-images": {"items": [], "total": 0},
    "/notes/list-notes": {"items": SEED_NOTES, "total": len(SEED_NOTES)},
    "/game/list-history": {"items": [], "total": 0, "score": {"win": 0, "loss": 0, "draw": 0}},
    "/blog/list-posts": {"items": SEED_POSTS, "total": len(SEED_POSTS)},
}


def seed():
    for path, payload in SEEDS.items():
        tapes.write("GET", path, payload)
    return sorted(SEEDS)


def new_id(prefix):
    return prefix + uuid.uuid4().hex[:8]


def now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def listing(items, **extra):
    payload = {"items": items, "total": len(items)}
    payload.update(extra)
    return payload


def evaluate(node):
    if isinstance(node, ast.Expression):
        return evaluate(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in OPERATORS:
        return OPERATORS[type(node.op)](evaluate(node.left), evaluate(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in OPERATORS:
        return OPERATORS[type(node.op)](evaluate(node.operand))
    raise ValueError("unsupported expression")


def compute_expression(expression):
    value = evaluate(ast.parse(expression, mode="eval"))
    return round(value, 10) if isinstance(value, float) else value


def store_image_bytes(image_id, data_url):
    header, _, encoded = data_url.partition(",")
    raw = base64.b64decode(encoded)
    os.makedirs(IMAGE_DIR, exist_ok=True)
    with open(os.path.join(IMAGE_DIR, image_id), "wb") as handle:
        handle.write(raw)
    return header.split(":")[-1].split(";")[0] or "image/png", len(raw)


def drop_image_bytes(image_id):
    path = os.path.join(IMAGE_DIR, image_id)
    if os.path.exists(path):
        os.remove(path)


def search_books(query_value):
    term = (query_value or "").strip().lower()
    items = tapes.read("/books/list-books")["items"]
    if term:
        items = [b for b in items if term in b["title"].lower() or term in b["author"].lower() or term in b["tags"].lower()]
    return listing(items, q=term)


def create_book(body):
    data = tapes.read("/books/list-books")
    book = {
        "id": new_id("b"),
        "title": body.get("title", ""),
        "author": body.get("author", ""),
        "year": int(body.get("year") or 0),
        "tags": body.get("tags", ""),
        "notes": body.get("notes", ""),
    }
    data["items"].append(book)
    return book, {"/books/list-books": listing(data["items"])}


def update_book(body):
    data = tapes.read("/books/list-books")
    for book in data["items"]:
        if book["id"] == body.get("id"):
            book.update({k: body.get(k, book[k]) for k in ("title", "author", "tags", "notes")})
            book["year"] = int(body.get("year") or book["year"])
            return book, {"/books/list-books": listing(data["items"])}
    raise LookupError("book not found")


def delete_book(body):
    data = tapes.read("/books/list-books")
    remaining = [b for b in data["items"] if b["id"] != body.get("id")]
    if len(remaining) == len(data["items"]):
        raise LookupError("book not found")
    return {"deleted": body.get("id")}, {"/books/list-books": listing(remaining)}


def compute(body):
    expression = (body.get("expression") or "").strip()
    entry = {"id": new_id("c"), "expression": expression, "at": now()}
    try:
        entry["result"] = compute_expression(expression)
        entry["ok"] = True
    except Exception:
        entry["result"] = None
        entry["ok"] = False
    history = tapes.read("/calc/list-history")["items"]
    history.insert(0, entry)
    return entry, {"/calc/list-history": listing(history[:100])}


def clear_calc_history(body):
    return {"cleared": True}, {"/calc/list-history": listing([])}


def upload_image(body):
    images = tapes.read("/images/list-images")["items"]
    image_id = new_id("i")
    if body.get("dataUrl"):
        mime, size = store_image_bytes(image_id, body["dataUrl"])
        image = {"id": image_id, "name": body.get("name") or "upload.png", "mime": mime, "size": size, "source": "drop", "url": "/images/raw/" + image_id}
    elif body.get("url"):
        image = {"id": image_id, "name": body.get("name") or body["url"].split("/")[-1][:48] or "remote", "mime": "image/*", "size": 0, "source": "url", "url": body["url"]}
    else:
        raise ValueError("dataUrl or url is required")
    image["created"] = now()
    images.insert(0, image)
    return image, {"/images/list-images": listing(images)}


def delete_image(body):
    images = tapes.read("/images/list-images")["items"]
    remaining = [i for i in images if i["id"] != body.get("id")]
    if len(remaining) == len(images):
        raise LookupError("image not found")
    drop_image_bytes(body.get("id"))
    return {"deleted": body.get("id")}, {"/images/list-images": listing(remaining)}


def create_note(body):
    notes = tapes.read("/notes/list-notes")["items"]
    note = {"id": new_id("n"), "title": body.get("title", ""), "body": body.get("body", ""), "todos": body.get("todos") or []}
    notes.append(note)
    return note, {"/notes/list-notes": listing(notes)}


def update_note(body):
    notes = tapes.read("/notes/list-notes")["items"]
    for note in notes:
        if note["id"] == body.get("id"):
            note.update({"title": body.get("title", note["title"]), "body": body.get("body", note["body"]), "todos": body.get("todos", note["todos"])})
            return note, {"/notes/list-notes": listing(notes)}
    raise LookupError("note not found")


def delete_note(body):
    notes = tapes.read("/notes/list-notes")["items"]
    remaining = [n for n in notes if n["id"] != body.get("id")]
    if len(remaining) == len(notes):
        raise LookupError("note not found")
    return {"deleted": body.get("id")}, {"/notes/list-notes": listing(remaining)}


def play_round(body):
    player = body.get("move")
    if player not in MOVES:
        raise ValueError("move must be rock, paper or scissors")
    pc = random.choice(MOVES)
    outcome = "draw" if pc == player else ("win" if BEATS[player] == pc else "loss")
    entry = {"id": new_id("r"), "player": player, "pc": pc, "outcome": outcome, "at": now()}
    data = tapes.read("/game/list-history")
    history = data["items"]
    history.insert(0, entry)
    score = {"win": 0, "loss": 0, "draw": 0}
    for row in history:
        score[row["outcome"]] += 1
    entry["score"] = score
    return entry, {"/game/list-history": listing(history[:100], score=score)}


def clear_game_history(body):
    return {"cleared": True}, {"/game/list-history": listing([], score={"win": 0, "loss": 0, "draw": 0})}


def create_post(body):
    posts = tapes.read("/blog/list-posts")["items"]
    post = {
        "id": new_id("p"),
        "title": body.get("title", ""),
        "body": body.get("body", ""),
        "image": body.get("image", ""),
        "youtube": body.get("youtube", ""),
        "created": now(),
    }
    posts.insert(0, post)
    return post, {"/blog/list-posts": listing(posts)}


def update_post(body):
    posts = tapes.read("/blog/list-posts")["items"]
    for post in posts:
        if post["id"] == body.get("id"):
            post.update({k: body.get(k, post[k]) for k in ("title", "body", "image", "youtube")})
            return post, {"/blog/list-posts": listing(posts)}
    raise LookupError("post not found")


def delete_post(body):
    posts = tapes.read("/blog/list-posts")["items"]
    remaining = [p for p in posts if p["id"] != body.get("id")]
    if len(remaining) == len(posts):
        raise LookupError("post not found")
    return {"deleted": body.get("id")}, {"/blog/list-posts": listing(remaining)}


READS = {"/books/search-books": search_books}

WRITES = {
    "/books/create-book": create_book,
    "/books/update-book": update_book,
    "/books/delete-book": delete_book,
    "/calc/compute": compute,
    "/calc/clear-history": clear_calc_history,
    "/images/upload-image": upload_image,
    "/images/delete-image": delete_image,
    "/notes/create-note": create_note,
    "/notes/update-note": update_note,
    "/notes/delete-note": delete_note,
    "/game/play-round": play_round,
    "/game/clear-history": clear_game_history,
    "/blog/create-post": create_post,
    "/blog/update-post": update_post,
    "/blog/delete-post": delete_post,
}

STALE_ON_WRITE = {"/books": "books_search-books__"}
