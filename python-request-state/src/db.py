import aiosqlite

SCHEMA: str = """
CREATE TABLE IF NOT EXISTS games (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    release_year INTEGER NOT NULL,
    image_url TEXT NOT NULL
)
"""

SUPER_MARIO_BROS: dict[str, str | int] = {
    "id": "3f1c2a8e-6b1d-4c1e-9a55-0d6f1b2e7c01",
    "name": "Super Mario Bros.",
    "description": "Nintendo's 1985 NES side-scroller where Mario runs through the Mushroom Kingdom to rescue Princess Toadstool from Bowser.",
    "release_year": 1985,
    "image_url": "https://upload.wikimedia.org/wikipedia/en/0/03/Super_Mario_Bros._box.png",
}


async def init_db(db_path: str) -> None:
    async with aiosqlite.connect(db_path) as conn:
        cursor = await conn.execute("SELECT 1 FROM sqlite_master WHERE name = 'games'")
        if await cursor.fetchone():
            return
        await conn.execute(SCHEMA)
        await conn.execute(
            "INSERT INTO games VALUES (:id, :name, :description, :release_year, :image_url)",
            SUPER_MARIO_BROS,
        )
        await conn.commit()
