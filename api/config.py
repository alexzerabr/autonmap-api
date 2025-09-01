from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    API_SECRET_KEY: str
    DEBUG: bool = False
    DATABASE_URL: str
    REDIS_URL: str
    GLOBAL_IP_ALLOWLIST: str = "127.0.0.1"
    WEBHOOK_HMAC_SECRET: str
    
settings = Settings()
