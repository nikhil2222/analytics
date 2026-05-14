from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Async engine (FastAPI) – leave this as-is
engine = create_async_engine(settings.DATABASE_URL, echo=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session

# Build sync DSN for psycopg2
SYNC_DATABASE_URL = settings.DATABASE_URL.replace(
    "postgresql+asyncpg://", "postgresql+psycopg2://"
)

# Strip async-specific ssl params not understood by psycopg2,
# and optionally add sslmode if you really need SSL.
# Example: if you currently have ?ssl=true
SYNC_DATABASE_URL = SYNC_DATABASE_URL.replace("?ssl=true", "").replace("&ssl=true", "")
SYNC_DATABASE_URL = SYNC_DATABASE_URL.replace("?ssl=false", "").replace("&ssl=false", "")

# If you want SSL for psycopg2, add sslmode manually:
# if "sslmode" not in SYNC_DATABASE_URL:
#     sep = "&" if "?" in SYNC_DATABASE_URL else "?"
#     SYNC_DATABASE_URL = f"{SYNC_DATABASE_URL}{sep}sslmode=require"

sync_engine = create_engine(
    SYNC_DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
)

SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False,
)