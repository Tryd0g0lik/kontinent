import os
import dotenv

dotenv.load_dotenv()

SECRET_KEY_DJ = os.getenv("SECRET_KEY_DJ", "")
POSTGRES_DB = os.getenv("POSTGRES_DB", "")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")
POSTGRES_USER = os.getenv("POSTGRES_USER", "")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "")
DB_ENGINE = os.getenv("DB_ENGINE", "")
DB_TO_REMOTE_HOST = os.getenv("DB_TO_REMOTE_HOST", "")
DATABASE_LOCAL = os.getenv("DATABASE_LOCAL", "")
DATABASE_ENGINE_LOCAL = os.getenv("DATABASE_ENGINE_LOCAL", "")
APP_TIME_ZONE = os.getenv("APP_TIME_ZONE", "")
