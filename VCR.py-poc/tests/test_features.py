import os

import requests

import api

PIXEL = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="


def test_every_response_the_browser_gets_was_played_from_a_cassette(site):
    response = requests.get(site + "/books/list-books")

    assert response.headers["X-Vcr-Cassette"] == "books_list-books.yaml"
    assert response.headers["X-Vcr-Played"] == "1"


def test_creating_a_book_retapes_the_list_so_the_grid_is_not_stale(site):
    before = requests.get(site + "/books/list-books").json()["total"]

    created = requests.post(site + "/books/create-book", json={"title": "Tidy First?", "author": "Kent Beck", "year": 2023})

    assert "books_list-books.yaml" in created.headers["X-Vcr-Retaped"]
    after = requests.get(site + "/books/list-books").json()
    assert after["total"] == before + 1
    assert after["items"][-1]["title"] == "Tidy First?"


def test_editing_then_deleting_a_book_round_trips_through_the_tape(site):
    book = requests.post(site + "/books/create-book", json={"title": "Draft", "author": "Someone"}).json()

    requests.post(site + "/books/update-book", json={"id": book["id"], "title": "Final", "notes": "shipped"})
    titles = [b["title"] for b in requests.get(site + "/books/list-books").json()["items"]]
    assert "Final" in titles and "Draft" not in titles

    requests.post(site + "/books/delete-book", json={"id": book["id"]})
    assert "Final" not in [b["title"] for b in requests.get(site + "/books/list-books").json()["items"]]


def test_search_gets_its_own_tape_and_is_dropped_when_the_library_changes(site, cassettes):
    hits = requests.get(site + "/books/search-books?q=design").json()

    assert [b["title"] for b in hits["items"]] == ["Domain-Driven Design", "A Philosophy of Software Design"]
    search_tapes = [f for f in os.listdir(cassettes) if f.startswith("books_search-books__")]
    assert len(search_tapes) == 1

    requests.post(site + "/books/create-book", json={"title": "New Design Book", "tags": "design"})

    assert not [f for f in os.listdir(cassettes) if f.startswith("books_search-books__")]


def test_calculator_records_the_result_and_keeps_the_running_history(site):
    result = requests.post(site + "/calc/compute", json={"expression": "2+3*4"}).json()

    assert result["result"] == 14
    assert requests.get(site + "/calc/list-history").json()["items"][0]["expression"] == "2+3*4"


def test_calculator_refuses_anything_that_is_not_arithmetic(site):
    entry = requests.post(site + "/calc/compute", json={"expression": "__import__('os').listdir('/')"}).json()

    assert entry["ok"] is False
    assert entry["result"] is None


def test_dropped_image_bytes_live_in_the_temp_dir_not_in_the_cassette(site, cassettes):
    image = requests.post(site + "/images/upload-image", json={"name": "dot.png", "dataUrl": PIXEL}).json()

    assert os.path.exists(os.path.join(api.IMAGE_DIR, image["id"]))
    assert PIXEL[-24:] not in (cassettes / "images_list-images.yaml").read_text()
    assert requests.get(site + image["url"]).content.startswith(b"\x89PNG")


def test_deleting_an_image_takes_the_bytes_with_it(site):
    image = requests.post(site + "/images/upload-image", json={"name": "dot.png", "dataUrl": PIXEL}).json()

    requests.post(site + "/images/delete-image", json={"id": image["id"]})

    assert not os.path.exists(os.path.join(api.IMAGE_DIR, image["id"]))
    assert requests.get(site + "/images/list-images").json()["total"] == 0


def test_an_image_added_by_url_is_referenced_not_downloaded(site):
    remote = "https://example.com/cat.png"

    image = requests.post(site + "/images/upload-image", json={"url": remote}).json()

    assert image["source"] == "url"
    assert image["url"] == remote
    assert not os.path.exists(os.path.join(api.IMAGE_DIR, image["id"]))


def test_notes_keep_their_todo_checklist_across_a_retape(site):
    note = requests.post(site + "/notes/create-note", json={
        "title": "Ship it", "body": "before friday",
        "todos": [{"id": "t1", "text": "write tests", "done": False}],
    }).json()

    requests.post(site + "/notes/update-note", json={
        "id": note["id"], "todos": [{"id": "t1", "text": "write tests", "done": True}],
    })

    stored = [n for n in requests.get(site + "/notes/list-notes").json()["items"] if n["id"] == note["id"]][0]
    assert stored["todos"][0]["done"] is True
    assert stored["title"] == "Ship it"


def test_game_score_is_recomputed_from_the_whole_history_tape(site):
    for _ in range(12):
        requests.post(site + "/game/play-round", json={"move": "rock"})

    data = requests.get(site + "/game/list-history").json()

    assert data["total"] == 12
    assert sum(data["score"].values()) == 12


def test_game_rejects_a_move_that_is_not_in_the_rules(site):
    response = requests.post(site + "/game/play-round", json={"move": "lizard"})

    assert response.status_code == 400
    assert requests.get(site + "/game/list-history").json()["total"] == 0


def test_a_published_post_keeps_its_video_and_image_fields(site):
    post = requests.post(site + "/blog/create-post", json={
        "title": "Tapes", "body": "on replay", "youtube": "dQw4w9WgXcQ",
        "image": "https://example.com/a.jpg",
    }).json()

    listed = requests.get(site + "/blog/list-posts").json()["items"][0]
    assert listed["id"] == post["id"]
    assert listed["youtube"] == "dQw4w9WgXcQ"
    assert listed["image"] == "https://example.com/a.jpg"


def test_editing_and_deleting_a_post_updates_the_blog_tape(site):
    post = requests.post(site + "/blog/create-post", json={"title": "Draft"}).json()

    requests.post(site + "/blog/update-post", json={"id": post["id"], "title": "Published"})
    assert requests.get(site + "/blog/list-posts").json()["items"][0]["title"] == "Published"

    requests.post(site + "/blog/delete-post", json={"id": post["id"]})
    assert post["id"] not in [p["id"] for p in requests.get(site + "/blog/list-posts").json()["items"]]


def test_missing_records_are_reported_as_not_found(site):
    assert requests.post(site + "/notes/delete-note", json={"id": "nope"}).status_code == 404
    assert requests.post(site + "/books/update-book", json={"id": "nope"}).status_code == 404


def test_an_endpoint_with_no_cassette_answers_501_instead_of_pretending(site):
    response = requests.get(site + "/blog/list-drafts")

    assert response.status_code == 501
    assert response.json()["endpoint"] == "/blog/list-drafts"
