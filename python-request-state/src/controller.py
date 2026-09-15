import uuid

from fastapi import APIRouter, Request, status

from models import Game, GameInput
from service import GameService

router = APIRouter(prefix="/api/games")


def service(request: Request) -> GameService:
    return request.state.game_service


@router.get("")
async def list_games(request: Request) -> list[Game]:
    return await service(request).list_games()


@router.get("/{game_id}")
async def get_game(game_id: uuid.UUID, request: Request) -> Game:
    return await service(request).get_game(str(game_id))


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_game(data: GameInput, request: Request) -> Game:
    return await service(request).create_game(data)


@router.put("/{game_id}")
async def update_game(game_id: uuid.UUID, data: GameInput, request: Request) -> Game:
    return await service(request).update_game(str(game_id), data)


@router.delete("/{game_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_game(game_id: uuid.UUID, request: Request) -> None:
    await service(request).delete_game(str(game_id))
