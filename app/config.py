from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    GEOFENCE_LAT: float = 41.311081
    GEOFENCE_LON: float = 69.240562
    GEOFENCE_RADIUS_METERS: float = 500

    # Pydantic v2 usuli: qo'shimcha maydonlarni e'tiborsiz qoldirish
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()