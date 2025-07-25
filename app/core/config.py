from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "GrantHub.AI"
    JWT_SECRET: str
    JWT_ALGORITHM: str
    VERSION: str = "0.1.0"
    DATABASE_URL: str
    UPSTASH_REDIS_REST_URL: str
    UPSTASH_REDIS_REST_TOKEN: str
    
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str

    MAIL_USERNAME : str
    MAIL_PASSWORD : str
    MAIL_FROM : str
    MAIL_PORT: int
    MAIL_SERVER : str
    MAIL_FROM_NAME : str

    DOMAIN: str

    model_config = SettingsConfigDict(
        env_file = ".env",
        extra = "ignore"
    ) 

settings = Settings()
