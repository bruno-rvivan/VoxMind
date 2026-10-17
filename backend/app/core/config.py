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
		"",
	)
	jwt_algorithm: str = "HS256"
	access_token_expire_minutes: int = 30

	def __post_init__(self) -> None:
		if self.database_url.startswith("postgres://"):
			object.__setattr__(
				self,
				"database_url",
				self.database_url.replace("postgres://", "postgresql+psycopg://", 1),
			)
		elif self.database_url.startswith("postgresql://"):
			object.__setattr__(
				self,
				"database_url",
				self.database_url.replace("postgresql://", "postgresql+psycopg://", 1),
			)
		if len(self.jwt_secret_key) < 32:
			raise RuntimeError(
				"JWT_SECRET_KEY must contain at least 32 characters. "
				"Set it in the environment or in the local .env file."
			)


settings = Settings()
