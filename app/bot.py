import asyncpg
import discord

from .config import settings


class BotClient(discord.Client):
    db: asyncpg.Pool

    def __init__(self):
        intents = discord.Intents.default()
        intents.guilds = True
        intents.members = True
        super().__init__(intents=intents)

    async def _save_sponsors(self, user_ids: list[int]) -> None:
        await self.db.execute(
            "INSERT INTO extra_sponsors (user_id) SELECT unnest($1::bigint[]) "
            "ON CONFLICT DO NOTHING",
            user_ids,
        )

    async def on_ready(self):
        guild = self.get_guild(settings.GUILD_ID)
        role = guild.get_role(settings.SPONSOR_ROLE_ID) if guild else None
        if role is not None:
            await self._save_sponsors([member.id for member in role.members])

    async def on_member_update(self, before: discord.Member, after: discord.Member):
        role_id = settings.SPONSOR_ROLE_ID
        if before.get_role(role_id) is None and after.get_role(role_id) is not None:
            await self._save_sponsors([after.id])


bot = BotClient()
