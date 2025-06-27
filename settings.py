'''File with settings and configs'''

from envparse import Env

env = Env()

REAL_DATABASE_URL = env.str(
    "REAL_DATABASE_URL",
    default="postgressql+asyncpg://schedule_db:postgres@0.0.0.0:5432/postgres"
)   # connect string for the database