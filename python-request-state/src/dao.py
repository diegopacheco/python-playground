import aiosqlite

from models import Game


class GameDao:
    def __init__(self, conn: aiosqlite.Connection) -> None:
        self.conn = conn
        self.conn.row_factory = aiosqlite.Row

    async def find_all(self) -> list[Game]:
        cursor = await self.conn.execute("SELECT * FROM games ORDER BY release_year, name")
        return [Game(**row) for row in await cursor.fetchall()]

    async def find_by_id(self, game_id: str) -> Game | None:
        cursor = await self.conn.execute("SELECT * FROM games WHERE id = ?", (game_id,))
        row = await cursor.fetchone()
        return Game(**row) if row else None

    async def insert(self, game: Game) -> None:
        await self.conn.execute(
            "INSERT INTO games VALUES (:id, :name, :description, :release_year, :image_url)",
            game.model_dump(),
        )
        await self.conn.commit()

    async def update(self, game: Game) -> bool:
        cursor = await self.conn.execute(
            "UPDATE games SET name = :name, description = :description, release_year = :release_year, image_url = :image_url WHERE id = :id",
            game.model_dump(),
        )
        await self.conn.commit()
        return cursor.rowcount == 1

    async def delete(self, game_id: str) -> bool:
        cursor = await self.conn.execute("DELETE FROM games WHERE id = ?", (game_id,))
        await self.conn.commit()
        return cursor.rowcount == 1
