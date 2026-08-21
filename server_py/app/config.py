import os
from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PORT: int = int(os.getenv("PORT", "22313"))
    DATA_DIR: str = os.getenv("DATA_DIR", str(Path(__file__).resolve().parent.parent.parent / "data"))
    SECRET_KEY: str = os.getenv("WARDEN_API_KEY", "warden_jwt_secret_key_change_me_in_production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    TIMEZONE: str = os.getenv("TZ", "Europe/Vienna")
    DEV_FIXTURE_MODE: bool = os.getenv("DEV_FIXTURE_MODE", "false").lower() == "true"
    
    @property
    def db_path(self) -> str:
        return os.path.join(self.DATA_DIR, "warden.db")
    
    @property
    def servers_dir(self) -> str:
        d = os.path.join(self.DATA_DIR, "servers")
        os.makedirs(d, exist_ok=True)
        return d
    
    @property
    def backups_dir(self) -> str:
        d = os.path.join(self.DATA_DIR, "backups")
        os.makedirs(d, exist_ok=True)
        return d
    
    @property
    def logs_dir(self) -> str:
        d = os.path.join(self.DATA_DIR, "logs")
        os.makedirs(d, exist_ok=True)
        return d

settings = Settings()
os.makedirs(settings.DATA_DIR, exist_ok=True)
os.makedirs(settings.servers_dir, exist_ok=True)
os.makedirs(settings.backups_dir, exist_ok=True)
os.makedirs(settings.logs_dir, exist_ok=True)
