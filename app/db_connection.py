from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///.database.db"

def get_engine():
	return create_async_engine(SQLALCHEMY_DATABASE_URL, echo=True) # echo for logging purpose

AsyncSessionLocal = sessionmaker(
	autocommit=False,
	autoflush=False,
	bind=get_engine(),
	class_=AsyncSession
)

async def get_db_session():
	async with AsyncSessionLocal() as session:
		yield session