import pytest

from notes_app.store import MAX_BODY, MAX_TITLE, NoteError, NoteStore


def test_ids_are_never_reused_so_a_deleted_note_link_never_points_to_another_note() -> None:
    store = NoteStore()
    first = store.add("first", "")
    assert store.delete(first.id)
    second = store.add("second", "")
    assert second.id != first.id
    assert store.get(first.id) is None


def test_newest_note_comes_first_so_the_ui_shows_latest_work_on_top() -> None:
    store = NoteStore()
    store.add("old", "")
    store.add("new", "")
    assert [note.title for note in store.all()] == ["new", "old"]


def test_whitespace_is_trimmed_so_blank_titles_cannot_sneak_in() -> None:
    store = NoteStore()
    note = store.add("  groceries  ", "  milk  ")
    assert (note.title, note.body) == ("groceries", "milk")
    with pytest.raises(NoteError, match="title is required"):
        store.add("   ", "body")


def test_limits_reject_oversized_input_to_keep_memory_bounded() -> None:
    store = NoteStore()
    store.add("t" * MAX_TITLE, "b" * MAX_BODY)
    with pytest.raises(NoteError, match="title"):
        store.add("t" * (MAX_TITLE + 1), "")
    with pytest.raises(NoteError, match="body"):
        store.add("ok", "b" * (MAX_BODY + 1))


def test_non_string_fields_are_rejected_because_json_clients_can_send_anything() -> None:
    store = NoteStore()
    with pytest.raises(NoteError, match="title must be a string"):
        store.add(42, "")
    with pytest.raises(NoteError, match="body must be a string"):
        store.add("ok", None)
    assert store.all() == []


def test_delete_of_missing_note_reports_false_so_the_api_can_answer_404() -> None:
    assert NoteStore().delete(999) is False
