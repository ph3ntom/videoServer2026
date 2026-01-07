from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Application Settings
    APP_NAME: str = "StreamFlix"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"

    # Server Settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 1

    # Database Settings
    DATABASE_URL: str
    DATABASE_ECHO: bool = False

    # Security Settings
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS Settings
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000"
    ALLOWED_HOSTS: str = "*"

    # File Storage Settings
    UPLOAD_DIR: str = "/mnt/videos"
    THUMBNAIL_DIR: str = "/mnt/thumbnails"
    MAX_UPLOAD_SIZE: int = 5368709120  # 5GB
    ALLOWED_VIDEO_EXTENSIONS: str = ".mp4,.mkv,.avi,.mov,.webm"

    # Video Processing Settings
    FFMPEG_PATH: str = "/usr/bin/ffmpeg"
    FFPROBE_PATH: str = "/usr/bin/ffprobe"
    THUMBNAIL_WIDTH: int = 320
    THUMBNAIL_HEIGHT: int = 180
    MAX_THUMBNAILS_PER_VIDEO: int = 15
    SCENE_DETECTION_THRESHOLD: float = 0.3

    # Admin Settings
    ADMIN_EMAIL: str = "admin@streamflix.local"
    ADMIN_PASSWORD: str = "changeme123"

    # Email Settings
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 1025
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "noreply@streamflix.com"
    SMTP_FROM_NAME: str = "StreamFlix"
    EMAIL_VERIFICATION_EXPIRE_HOURS: int = 24
    FRONTEND_URL: str = "http://localhost:5174"

    @property
    def allowed_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]

    @property
    def allowed_video_extensions_list(self) -> List[str]:
        return [ext.strip() for ext in self.ALLOWED_VIDEO_EXTENSIONS.split(",")]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
