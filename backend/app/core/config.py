import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
	database_url: str = os.getenv(
		"DATABASE_URL",
		"postgresql+psycopg://voxmind:voxmind@localhost:5432/voxmind",
	)
	jwt_secret_key: str = os.getenv(
		"JWT_SECRET_KEY",
		"development-only-secret-change-before-deployment",
	)
	jwt_algorithm: str = "HS256"
	access_token_expire_minutes: int = 30


settings = Settings()
