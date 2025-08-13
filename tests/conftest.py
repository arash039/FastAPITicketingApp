import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base, Ticket
from app.db_connection import get_db_session
from app.main import app

@pytest.fixture
def db_engine_test():
	engine = create_async_engine("sqlite+aiosqlite:///:memory:")
	return engine

@pytest.fixture
async def db_session_test(db_engine_test):
	TestAsyncSessionLocal = sessionmaker(bind=db_engine_test, class_=AsyncSession)
	async with db_engine_test.begin() as conn:
		await conn.run_sync(Base.metadata.drop_all)
		await conn.run_sync(Base.metadata.create_all)

		async with TestAsyncSessionLocal() as session:
			yield session

		await conn.run_sync(Base.metadata.drop_all)
	await db_engine_test.dispose()

@pytest.fixture
async def add_single_ticket(db_session_test):
    ticket = Ticket(
        id = 1234,
        show = "another show",
		user = "test user",
		price = 1000
    )
    async with db_session_test.begin():
        db_session_test.add(ticket)
        await db_session_test.commit()

@pytest.fixture
def test_client(db_session_test):
	client = TestClient(app=app)
	app.dependency_overrides[get_db_session] = lambda: db_session_test
	
	return client