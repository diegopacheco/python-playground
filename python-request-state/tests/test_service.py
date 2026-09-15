import uuid

import pytest
from pydantic import ValidationError

from db import SUPER_MARIO_BROS, init_db
from models import GameInput
from service import GameNotFound

pytestmark = pytest.mark.anyio


def game_input(**overrides) -> GameInput:
    data = {
        "name": "The Legend of Zelda",
        "description": "Explore Hyrule",
        "release_year": 1986,
        "image_url": "https://example.org/zelda.png",
    }
    return GameInput(**{**data, **overrides})


async def test_fresh_database_ships_with_super_mario_bros(service):
    games = await service.list_games()
    assert [(g.name, g.release_year) for g in games] == [("Super Mario Bros.", 1985)]


async def test_seed_is_not_restored_after_user_deletes_it(db_path, service):
    await service.delete_game(SUPER_MARIO_BROS["id"])
    await init_db(db_path)
    assert await service.list_games() == []


async def test_create_assigns_a_server_side_uuid(service):
    game = await service.create_game(game_input())
    assert uuid.UUID(game.id).version == 4
    assert await service.get_game(game.id) == game


async def test_list_is_ordered_by_release_year(service):
    await service.create_game(game_input(name="Tetris", release_year=1984))
    assert [g.release_year for g in await service.list_games()] == [1984, 1985]


async def test_update_keeps_the_id_and_replaces_fields(service):
    game = await service.create_game(game_input())
    await service.update_game(game.id, game_input(name="Zelda II", release_year=1987))
    stored = await service.get_game(game.id)
    assert (stored.name, stored.release_year) == ("Zelda II", 1987)


async def test_missing_game_raises_not_found_for_every_operation(service):
    missing = str(uuid.uuid4())
    with pytest.raises(GameNotFound):
        await service.get_game(missing)
    with pytest.raises(GameNotFound):
        await service.update_game(missing, game_input())
    with pytest.raises(GameNotFound):
        await service.delete_game(missing)


def test_blank_name_is_rejected_after_trimming():
    with pytest.raises(ValidationError):
        game_input(name="   ")


def test_image_url_must_be_http():
    with pytest.raises(ValidationError):
        game_input(image_url="javascript:alert(1)")
