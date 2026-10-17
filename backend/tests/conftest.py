import os


os.environ.setdefault(
	"JWT_SECRET_KEY",
	"test-only-secret-key-that-must-never-be-used-in-production",
)