from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    
    TOO_SB_DB: Optional[str] = None
    
    app_env: str = "development"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

settings = Settings()
