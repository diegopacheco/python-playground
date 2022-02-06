import asyncio
import uvloop

async def main():
    # Main entry-point.
    print('uvloop fun!')

uvloop.install()
asyncio.run(main())
