import asyncio
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI

from .bot import bot
from .config import settings
from .routes import router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    task = asyncio.create_task(bot.start(settings.BOT_TOKEN))
    # Yield to the event loop so bot.start() can begin login before wait_until_ready()
    await asyncio.sleep(0)
    await bot.wait_until_ready()
    yield
    await bot.close()
    task.cancel()
    with suppress(asyncio.CancelledError):
        await task


app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None)
app.include_router(router)
