from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "GrantHub.AI"
    JWT_SECRET: str
    JWT_ALGORITHM: str
    VERSION: str = "0.1.0"
    DATABASE_URL: str
    REDIS_HOST: str
    REDIS_PORT: int

    model_config = SettingsConfigDict(
        env_file = ".env",
        extra = "ignore"
    ) 

settings = Settings()
