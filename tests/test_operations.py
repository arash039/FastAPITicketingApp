import asyncio
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import Ticket
from app.operations import create_ticket, update_ticket_price, delete_ticket, get_ticket, sell_ticket_to_user

async def assert_ticket_table_is_empty(db_session: AsyncSession):
	async with db_session as session:
		result = await session.execute(select(Ticket))
	assert result.all() == []

async def test_create_ticket_for_show1(db_session_test):
	await assert_ticket_table_is_empty(db_session_test)

	ticket_id = await create_ticket(db_session_test, "show1")

	async with db_session_test as session:
		result = await session.execute(select(Ticket))
		items = result.scalars().all()

	assert ticket_id == 1
	assert len(items) == 1
	assert items[0].show == "show1"

async def test_get_ticket(add_single_ticket, db_session_test):
	ticket = await get_ticket(db_session_test, 1234)

	assert ticket.id == 1234
	assert ticket.show == "another show"
	assert ticket.price == 1000

async def test_update_ticket_price(add_single_ticket, db_session_test):
	await update_ticket_price(db_session_test, ticket_id=1234, new_price=5000)
	ticket = await get_ticket(db_session_test, 1234)
	assert ticket.price == 5000

async def test_delete_ticket(add_single_ticket, db_session_test):
	assert await delete_ticket(db_session_test, 123) is False
	assert await delete_ticket(db_session_test, 1234) is True

async def test_concurrent_ticket_sell(
		add_special_ticket,
		db_session_test,
		seconf_session_test
):
	result = await asyncio.gather(
		sell_ticket_to_user(db_session_test, 12345, "User1"),
		sell_ticket_to_user(seconf_session_test, 12345, "User2")
	)

	assert result in ([True, False], [False, True])

	ticket = await get_ticket(db_session_test, 12345)

	if result[0]:
		assert ticket.user == "User1"
	else:
		assert ticket.user == "User2"