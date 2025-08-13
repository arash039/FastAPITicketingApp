from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from app.database import Ticket

async def create_ticket(
		db_session: AsyncSession,
		show_name: str,
		user: str = None,
		price: float = None
) -> int:
	ticket = Ticket(
		show = show_name,
		user = user,
		price = price
	)

	async with db_session.begin():
		db_session.add(ticket)
		await db_session.flush()
		ticket_id = ticket.id
		await db_session.commit()

	return ticket_id

async def get_ticket(
		db_session: AsyncSession,
		ticket_id: int
) -> Ticket | None:
	query = select(Ticket).where(Ticket.id == ticket_id)
	async with db_session as session:
		ticket = await session.execute(query)
		return ticket.scalars().first()
	
async def update_ticket_price(
		db_session: AsyncSession,
		ticket_id: int,
		new_price: float
) -> bool:
	query = update(Ticket).where(Ticket.id == ticket_id).values(price=new_price)
	async with db_session as session:
		ticket_updated = await session.execute(query)
		await session.commit()
		if ticket_updated.rowcount == 0:
			return False
		return True
	
async def delete_ticket(
		db_session: AsyncSession,
		ticket_id: int
) -> bool:
	query = delete(Ticket).where(Ticket.id == ticket_id)
	async with db_session as session:
		ticket_removed = await session.execute(query)
		await session.commit()
		if ticket_removed.rowcount == 0:
			return False
		return True