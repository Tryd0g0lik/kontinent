import os
import dotenv

dotenv.load_dotenv()

SECRET_KEY_DJ = os.getenv("SECRET_KEY_DJ", "")
# db
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "")
POSTGRES_DB = os.getenv("POSTGRES_DB", "")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")
POSTGRES_USER = os.getenv("POSTGRES_USER", "")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "")
DB_ENGINE = os.getenv("DB_ENGINE", "")
DATABASE_LOCAL = os.getenv("DATABASE_LOCAL", "")
DATABASE_ENGINE_LOCAL = os.getenv("DATABASE_ENGINE_LOCAL", "")

# Redis
REDIS_LOCATION_URL = os.getenv("REDIS_LOCATION_URL", "")
DB_TO_RADIS_CACHE_USERS = os.getenv("DB_TO_RADIS_CACHE_USERS", "")
DB_TO_RADIS_PORT = os.getenv("DB_TO_RADIS_PORT", "")
DB_TO_RADIS_HOST = os.getenv("DB_TO_RADIS_HOST", "")
# And more
APP_TIME_ZONE = os.getenv("APP_TIME_ZONE", "")
DB_TO_REMOTE_HOST = os.getenv("DB_TO_REMOTE_HOST", "")
