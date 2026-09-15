import uuid

from dao import GameDao
from models import Game, GameInput


class GameNotFound(Exception):
    pass


class GameService:
    def __init__(self, dao: GameDao) -> None:
        self.dao = dao

    async def list_games(self) -> list[Game]:
        return await self.dao.find_all()

    async def get_game(self, game_id: str) -> Game:
        game = await self.dao.find_by_id(game_id)
        if game is None:
            raise GameNotFound(game_id)
        return game

    async def create_game(self, data: GameInput) -> Game:
        game = Game(id=str(uuid.uuid4()), **data.model_dump())
        await self.dao.insert(game)
        return game

    async def update_game(self, game_id: str, data: GameInput) -> Game:
        game = Game(id=game_id, **data.model_dump())
        if not await self.dao.update(game):
            raise GameNotFound(game_id)
        return game

    async def delete_game(self, game_id: str) -> None:
        if not await self.dao.delete(game_id):
            raise GameNotFound(game_id)
