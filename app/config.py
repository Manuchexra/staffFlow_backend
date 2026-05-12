from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str
    SECRET_KEY: str
    ALGORITHM: str 
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int
    GEOFENCE_LAT: float
    GEOFENCE_LON: float
    GEOFENCE_RADIUS_METERS: float
    
    # Email SMTP sozlamalari
    SMTP_MOCK: bool = False  # False: real email, True: mock email (print)
    SMTP_SERVER: str
    SMTP_PORT: int
    SMTP_EMAIL: str
    SMTP_PASSWORD: str 
    SMTP_FROM_NAME: str

    # Pydantic v2 usuli: qo'shimcha maydonlarni e'tiborsiz qoldirish
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()