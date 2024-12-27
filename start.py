import asyncio
from hypercorn.config import Config
from hypercorn.asyncio import serve
from main import app
import os

async def start_server():
    config = Config()
    config.bind = [f"0.0.0.0:{int(os.environ.get('PORT', 10000))}"]
    config.worker_class = "asyncio"
    config.workers = 4
    config.timeout = 300  # 5 minutes timeout
    config.graceful_timeout = 300
    config.keep_alive_timeout = 300
    await serve(app, config)

if __name__ == "__main__":
    asyncio.run(start_server())
