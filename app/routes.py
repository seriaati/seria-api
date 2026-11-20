import hmac

from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.security import APIKeyHeader
from cachetools import TTLCache

from .bot import bot
from .config import settings

router = APIRouter()
user_cache = TTLCache(maxsize=250, ttl=60 * 60)

_api_key_header = APIKeyHeader(name="x-api-key")


def verify_api_key(api_key: str = Security(_api_key_header)) -> None:
    if not hmac.compare_digest(api_key, settings.API_KEY):
        raise HTTPException(status_code=401, detail="Invalid API key")


@router.get("/health")
async def health():
    return {
        "status": "ok",
        "bot_ready": not bot.is_closed(),
        "bot_latency_ms": bot.latency * 1000,
    }


@router.get("/favicon.ico")
async def get_favicon():
    raise HTTPException(status_code=204, detail="No favicon available")


@router.get("/roles", dependencies=[Depends(verify_api_key)])
async def list_roles():
    guild = bot.get_guild(settings.GUILD_ID)
    if guild is None:
        raise HTTPException(status_code=503, detail="Guild not available")
    return [
        {
            "id": str(role.id),
            "name": role.name,
            "color": role.color.value,
            "position": role.position,
            "member_count": len(role.members),
        }
        for role in guild.roles
    ]


@router.get("/roles/{role_id}/members", dependencies=[Depends(verify_api_key)])
async def list_role_members(role_id: int):
    guild = bot.get_guild(settings.GUILD_ID)
    if guild is None:
        raise HTTPException(status_code=503, detail="Guild not available")
    role = guild.get_role(role_id)
    if role is None:
        raise HTTPException(status_code=404, detail="Role not found")
    return [
        {
            "id": str(member.id),
            "username": member.name,
            "display_name": member.display_name,
            "avatar_url": str(member.display_avatar.url)
            if member.display_avatar
            else None,
        }
        for member in role.members
    ]


@router.get("/sponsors", dependencies=[Depends(verify_api_key)])
async def list_sponsors():
    guild = bot.get_guild(settings.GUILD_ID)
    if guild is None:
        raise HTTPException(status_code=503, detail="Guild not available")
    role = guild.get_role(settings.SPONSOR_ROLE_ID)
    if role is None:
        raise HTTPException(status_code=404, detail="Sponsor role not found")

    seen_ids: set[int] = set()
    members = []

    for member in role.members:
        seen_ids.add(member.id)
        members.append(
            {
                "id": str(member.id),
                "username": member.name,
                "display_name": member.display_name,
                "avatar_url": str(member.display_avatar.url)
                if member.display_avatar
                else None,
            }
        )

    for user_id in settings.EXTRA_SPONSOR_USER_IDS:
        if user_id in seen_ids:
            continue

        member = guild.get_member(user_id)
        if member is None:
            member = user_cache.get(user_id)
        if member is None:
            member = await bot.fetch_user(user_id)
            user_cache[user_id] = member

        members.append(
            {
                "id": str(member.id),
                "username": member.name,
                "display_name": member.display_name,
                "avatar_url": str(member.display_avatar.url)
                if member.display_avatar
                else None,
            }
        )

    return members
