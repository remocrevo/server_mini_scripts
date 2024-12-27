import asyncio
from hypercorn.config import Config
from hypercorn.asyncio import serve
from main import app
import os

config = Config()
config.bind = [f"0.0.0.0:{int(os.environ.get('PORT', 10000))}"]
config.timeout = 300
config.graceful_timeout = 300
config.keep_alive_timeout = 300

asyncio.run(serve(app, config))
