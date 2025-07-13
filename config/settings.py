'''File with settings and configs'''

from envparse import Env

env = Env()

REAL_DATABASE_URL = env.str(
    "REAL_DATABASE_URL",
    default="postgresql+asyncpg://shedule:shedule@localhost:5433/schedule_db"
)   # connect string for the database