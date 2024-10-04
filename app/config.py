from dotenv import load_dotenv
import os

from pydantic.v1 import BaseSettings

load_dotenv()
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")

class Settings(BaseSettings):
    database_url: str

    class Config:
        env_file = ".env"


settings = Settings()
