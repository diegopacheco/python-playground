import socket

import pytest

import tapes


def test_a_taped_endpoint_answers_without_resolving_the_host(cassettes, monkeypatch):
    def explode(*args, **kwargs):
        raise AssertionError("DNS was used, so the response did not come off the tape")

    monkeypatch.setattr(socket, "getaddrinfo", explode)

    response, meta = tapes.play("GET", "/blog/list-posts")

    assert response.status_code == 200
    assert meta["played"] == 1
    assert response.json()["total"] == 2


def test_an_untaped_endpoint_cannot_be_reached(cassettes):
    with pytest.raises(tapes.NoTape):
        tapes.play("GET", "/blog/list-drafts")


def test_deleting_a_tape_removes_the_endpoint(cassettes):
    tapes.play("GET", "/notes/list-notes")

    (cassettes / "notes_list-notes.yaml").unlink()

    with pytest.raises(tapes.NoTape):
        tapes.play("GET", "/notes/list-notes")


def test_a_tape_is_the_readable_record_of_what_the_backend_would_have_said(cassettes):
    tapes.write("GET", "/books/list-books", {"items": [{"id": "b9", "title": "Only Book"}], "total": 1})

    assert tapes.read("/books/list-books")["items"][0]["title"] == "Only Book"
    assert tapes.play("GET", "/books/list-books")[0].json()["total"] == 1
