import asyncio
from contextlib import asynccontextmanager, suppress

import asyncpg
from fastapi import FastAPI

from .bot import bot
from .config import settings
from .routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.db = await asyncpg.create_pool(settings.DATABASE_URL)
    await app.state.db.execute(
        "CREATE TABLE IF NOT EXISTS extra_sponsors (user_id BIGINT PRIMARY KEY)"
    )
    bot.db = app.state.db

    task =asyncio.create_task(bot.start(settings.BOT_TOKEN))
    # Yield to the event loop so bot.start() can begin login before wait_until_ready()
    await asyncio.sleep(0)
    await bot.wait_until_ready()
    yield
    await bot.close()
    task.cancel()
    with suppress(asyncio.CancelledError):
        await task
    await app.state.db.close()


app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None)
app.include_router(router)
