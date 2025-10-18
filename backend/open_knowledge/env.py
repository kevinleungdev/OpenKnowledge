import os
import logging
from shutil import ExecError
import sys

from pathlib import Path

####################################
# Load .env file
####################################

# Use .resolve() to get the canonical path, removing any '..' and '.' components
ENV_FILE_PATH = Path(__file__).resolve()

# OPEN_KNOWLEDGE_DIR should be the directory where env.py resides (open_knowledge/)
OPEN_KNOWLEDGE_DIR = ENV_FILE_PATH.parent

# BACKEND_DIR is the parent of OPEN_KNOWLEDGE_DIR
BACKEND_DIR = OPEN_KNOWLEDGE_DIR.parent

# BASE_DIR is the parent of BACKEND_DIR
BASE_DIR = BACKEND_DIR.parent

try:
    from dotenv import load_dotenv, find_dotenv

    load_dotenv(find_dotenv(str(BASE_DIR / ".env")))
except ImportError:
    print("dotenv not installed, skipping...")


####################################
# LOGGING
####################################

GLOBAL_LOG_LEVEL = os.environ.get("GLOBAL_LOG_LEVEL", "").upper()
if GLOBAL_LOG_LEVEL in logging.getLevelNamesMapping():
    logging.basicConfig(stream=sys.stdout, level=GLOBAL_LOG_LEVEL, force=True)
else:
    GLOBAL_LOG_LEVEL = "INFO"

log = logging.getLogger(__name__)
log.info(f"Global log level set to {GLOBAL_LOG_LEVEL}")

log_sources = [
    "CONFIG",
    "DB",
    "IMAGES",
    "MAIN",
    "MODELS",
    "OLLAMA",
    "OPENAI",
    "RAG",
]

SRC_LOG_LEVELS = {}

for source in log_sources:
    log_env_var = f"{source}_LOG_LEVEL"
    SRC_LOG_LEVELS[source] = os.environ.get(log_env_var, "").upper()
    if SRC_LOG_LEVELS[source] not in logging.getLevelNamesMapping():
        SRC_LOG_LEVELS[source] = GLOBAL_LOG_LEVEL
    log.info(f"{log_env_var}: {SRC_LOG_LEVELS[source]}")

log.setLevel(SRC_LOG_LEVELS["CONFIG"])


DATA_DIR = Path(os.environ.get("DATA_DIR", BASE_DIR / "data")).resolve()


####################################
# Database
####################################

DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{DATA_DIR}/knowledgebase.db")

DATABASE_TYPE = os.environ.get("DATABASE_TYPE")
DATABASE_USER = os.environ.get("DATABASE_USER")
DATABASE_PASSWORD = os.environ.get("DATABASE_PASSWORD")

DATABASE_CRED = ""
if DATABASE_USER:
    DATABASE_CRED += f"{DATABASE_USER}"
if DATABASE_PASSWORD:
    DATABASE_CRED += f":{DATABASE_PASSWORD}"

DB_VARS = {
    "db_type": DATABASE_TYPE,
    "db_cred": DATABASE_CRED,
    "db_host": os.environ.get("DATABASE_HOST"),
    "db_port": os.environ.get("DATABASE_PORT"),
    "db_name": os.environ.get("DATABASE_NAME"),
}

if all(DB_VARS.values()):
    DATABASE_URL = f"{DB_VARS['db_type']}://{DB_VARS['db_cred']}@{DB_VARS['db_host']}:{DB_VARS['db_port']}/{DB_VARS['db_name']}"
elif DATABASE_TYPE == "sqlite+sqlcipher" and not os.environ.get("DATABASE_URL"):
    # Handle SQLCipher with local file when DATABASE_URL wasn't explicitly set
    DATABASE_URL = f"sqlite+sqlcipher:///{DATA_DIR}/knowledgebase.db"

if "postgres://" in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://")

DATABASE_SCHEMA = os.environ.get("DATABASE_SCHEMA", None)

DATABASE_POOL_SIZE = os.environ.get("DATABASE_POOL_SIZE", None)

if DATABASE_POOL_SIZE is not None:
    try:
        DATABASE_POOL_SIZE = int(DATABASE_POOL_SIZE)
    except Exception:
        DATABASE_POOL_SIZE = None

DATABASE_POOL_MAX_OVERFLOW = os.environ.get("DATABASE_POOL_MAX_OVERFLOW", 0)

if DATABASE_POOL_MAX_OVERFLOW == "":
    DATABASE_POOL_MAX_OVERFLOW = 0
else:
    try:
        DATABASE_POOL_MAX_OVERFLOW = int(DATABASE_POOL_MAX_OVERFLOW)
    except Exception:
        DATABASE_POOL_MAX_OVERFLOW = 0

DATABASE_POOL_TIMEOUT = os.environ.get("DATABASE_POOL_TIMEOUT", 30)

if DATABASE_POOL_TIMEOUT == "":
    DATABASE_POOL_TIMEOUT = 30
else:
    try:
        DATABASE_POOL_TIMEOUT = int(DATABASE_POOL_TIMEOUT)
    except Exception:
        DATABASE_POOL_TIMEOUT = 30

DATABASE_POOL_RECYCLE = os.environ.get("DATABASE_POOL_RECYCLE", 3600)

if DATABASE_POOL_RECYCLE == "":
    DATABASE_POOL_RECYCLE = 3600
else:
    try:
        DATABASE_POOL_RECYCLE = int(DATABASE_POOL_RECYCLE)
    except Exception:
        DATABASE_POOL_RECYCLE = 3600


####################################
# VECTOR DATABASE
####################################

VECTOR_DB = os.environ.get("VECTOR_DB", "pgvector")

# Pgvector
PGVECTOR_DB_URL = os.getenv("PGVECTOR_DB_URL", DATABASE_URL)

if VECTOR_DB == "pgvector" and not PGVECTOR_DB_URL.startswith("postgres"):
    raise ValueError(
        "Pgvector requires setting PGVECTOR_DB_URL or using Postgres with vector extension as the primary database."
    )
PGVECTOR_INITIALIZE_MAX_VECTOR_LENGTH = int(
    os.getenv("PGVECTOR_INITIALIZE_MAX_VECTOR_LENGTH", 1536)
)

PGVECTOR_PGCRYPTO = os.getenv("PGVECTOR_PGCRYPTO", "false").lower() == "true"

PGVECTOR_PGCRYPTO_KEY = os.getenv("PGVECTOR_PGCRYPTO_KEY", None)
if PGVECTOR_PGCRYPTO and not PGVECTOR_PGCRYPTO_KEY:
    raise ValueError(
        "PGVECTOR_PGCRYPTO is enabled but PGVECTOR_PGCRYPTO_KEY is not set. Please provide a valid key."
    )

PGVECTOR_POOL_SIZE = os.environ.get("PGVECTOR_POOL_SIZE", None)

if PGVECTOR_POOL_SIZE != None:
    try:
        PGVECTOR_POOL_SIZE = int(PGVECTOR_POOL_SIZE)
    except Exception:
        PGVECTOR_POOL_SIZE = None

PGVECTOR_POOL_MAX_OVERFLOW = os.environ.get("PGVECTOR_POOL_MAX_OVERFLOW", 0)

if PGVECTOR_POOL_MAX_OVERFLOW == "":
    PGVECTOR_POOL_MAX_OVERFLOW = 0
else:
    try:
        PGVECTOR_POOL_MAX_OVERFLOW = int(PGVECTOR_POOL_MAX_OVERFLOW)
    except Exception:
        PGVECTOR_POOL_MAX_OVERFLOW = 0

PGVECTOR_POOL_TIMEOUT = os.environ.get("PGVECTOR_POOL_TIMEOUT", 30)

if PGVECTOR_POOL_TIMEOUT == "":
    PGVECTOR_POOL_TIMEOUT = 30
else:
    try:
        PGVECTOR_POOL_TIMEOUT = int(PGVECTOR_POOL_TIMEOUT)
    except Exception:
        PGVECTOR_POOL_TIMEOUT = 30

PGVECTOR_POOL_RECYCLE = os.environ.get("PGVECTOR_POOL_RECYCLE", 3600)

if PGVECTOR_POOL_RECYCLE == "":
    PGVECTOR_POOL_RECYCLE = 3600
else:
    try:
        PGVECTOR_POOL_RECYCLE = int(PGVECTOR_POOL_RECYCLE)
    except Exception:
        PGVECTOR_POOL_RECYCLE = 3600


####################################
# UVICORN WORKERS
####################################

# Number of uvicorn workers to handle requests
UVICORN_WORKERS = os.environ.get("UVICORN_WORKERS", 1)
try:
    UVICORN_WORKERS = int(UVICORN_WORKERS)
    if UVICORN_WORKERS < 1:
        UVICORN_WORKERS = 1
except ValueError:
    UVICORN_WORKERS = 1
    log.info(f"Invalid UVICORN_WORKERS value, defaulting to {UVICORN_WORKERS}")


####################################
# STORAGE PROVIDER
####################################

STORAGE_PROVIDER = os.environ.get("STORAGE_PROVIDER", "local")

S3_ACCESS_KEY_ID = os.environ.get("S3_ACCESS_KEY_ID", None)
S3_SECRET_ACCESS_KEY = os.environ.get("S3_SECRET_ACCESS_KEY", None)
S3_REGION_NAME = os.environ.get("S3_REGION_NAME", None)
S3_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME", None)
S3_KEY_PREFIX = os.environ.get("S3_KEY_PREFIX", None)
S3_ENDPOINT_URL = os.environ.get("S3_ENDPOINT_URL", None)
S3_ENABLE_TAGGING = os.environ.get("S3_ENABLE_TAGGING", "false").lower() == "true"


####################################
# File Upload DIR
####################################

UPLOAD_DIR = DATA_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


####################################
# Miscellaneous
####################################

ENV = os.environ.get("ENV", "dev")