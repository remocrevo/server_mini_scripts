from hypercorn.config import Config
from hypercorn.run import run
from main import app
import os

if __name__ == "__main__":
    config = Config()
    config.bind = [f"0.0.0.0:{int(os.environ.get('PORT', 10000))}"]
    config.workers = 4
    config.timeout = 300
    config.graceful_timeout = 300
    config.keep_alive_timeout = 300
    run(app, config)
