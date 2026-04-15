from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    GUILD_ID: int
    BOT_TOKEN: str
    SPONSOR_ROLE_ID: int
    API_KEY: str
    EXTRA_SPONSOR_USER_IDS: list[int] = []

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
