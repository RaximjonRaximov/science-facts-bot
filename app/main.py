import asyncio
import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from .bot import build_bot
from .db import FactsDatabase
from .facts import FactsStore
from .web import register_routes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def make_lifespan(store: FactsStore, db: FactsDatabase):
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        bot = await build_bot()
        bot_task = None
        if bot:
            logger.info("Starting Telegram bot polling")
            bot_task = asyncio.create_task(bot.run())
        else:
            logger.info("TELEGRAM_TOKEN not set; running web admin only")
        yield
        if bot_task:
            bot_task.cancel()
            try:
                await bot_task
            except asyncio.CancelledError:
                pass

    return lifespan


def build_app() -> FastAPI:
    store = FactsStore()
    db = FactsDatabase()
    app = FastAPI(
        title="Science Facts Bot",
        version="1.0.0",
        lifespan=make_lifespan(store, db),
    )
    register_routes(app, store, db)
    return app


app = build_app()


def main() -> None:
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
