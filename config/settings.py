'''File with settings and configs'''

from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

REAL_DATABASE_URL = os.getenv(
    "REAL_DATABASE_URL",
    "postgresql+asyncpg://postgres:123456@localhost:5433/schedule_db"
)   # connect string for the database

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres_test:123456_test@localhost:5434/schedule_db_test"
)   # connect string for the test database

ROOT_PATH = str(Path(__file__).parent.parent)

# Jwt, безопасность
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Все роли в системе
USERS_ROLES = os.getenv("USERS_ROLES", "Schedule Manager,Admin,Chief Admin").split(",")
