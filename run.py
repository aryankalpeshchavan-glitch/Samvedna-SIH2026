import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


async def main():
    import uvicorn
    config = uvicorn.Config(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())
