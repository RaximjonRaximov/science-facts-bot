import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.bot import build_bot
from app.db import FactsDatabase
from app.facts import FactsStore
from app.web import register_routes

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


# Build store and database eagerly so routes can be registered.
# The SQLite file is created under data/ relative to the project root.
store = FactsStore()
db = FactsDatabase()

app = FastAPI(
    title="Science Facts Bot",
    version="1.0.0",
    lifespan=make_lifespan(store, db),
)
register_routes(app, store, db)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
