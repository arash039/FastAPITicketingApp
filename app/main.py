from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from app.database import Base
from app.db_connection import AsyncSessionLocal, get_db_session, get_engine
from sqlalchemy.ext.asyncio import AsyncSession
from app.operations import create_ticket, update_ticket_price, delete_ticket, get_ticket
from typing import Annotated
from pydantic import BaseModel, Field

@asynccontextmanager
async def lifespan(app: FastAPI):
	engine = get_engine()
	async with engine.begin() as conn:
		await conn.run_sync(Base.metadata.create_all)
		yield
	await engine.dispose()

app = FastAPI(lifespan=lifespan)

class TicketRequest(BaseModel):
	price: float | None
	show: str | None
	user: str | None

class TicketUpdateRequest(BaseModel):
	price: float | None = Field(None, ge=0)


@app.post("/ticket", response_model=dict[str, int])
async def create_ticket_route(
	ticket: TicketRequest,
	db_session: Annotated[AsyncSession, Depends(get_db_session)]
):
	ticket_id = await create_ticket(
		db_session,
		ticket.show,
		ticket.user,
		ticket.price
	)
	return {"ticket_id" : ticket_id}

@app.get("/tickets/{ticket_id}")
async def read_ticket(
	ticket_id: int,
	db_session: Annotated[AsyncSession, Depends(get_db_session)]
):
	ticket = await get_ticket(db_session, ticket_id)
	if ticket is None:
		raise HTTPException(
			status_code=404, detail="ticket not found"
		)
	return ticket

@app.put("/ticket/{ticket_id}/price/{new_price}")
async def update_ticket_route(
	ticket_id: int,
	new_price: float,
	db_session: Annotated[AsyncSession, Depends(get_db_session)]
):
	updated = await update_ticket_price(db_session, ticket_id, new_price)
	if not updated:
		raise HTTPException(
			status_code=404, detail="ticket not found"
		)
	return {"detail" : "ticket price updated"}


@app.delete("/ticket/{ticket_id}")
async def delete_ticket_route(
	db_session: Annotated[AsyncSession, Depends(get_db_session)],
	ticket_id: int
):
	ticket = await delete_ticket(db_session, ticket_id)
	if not ticket:
		raise HTTPException(
			status_code=404, detail="ticket not found"
		)
	return {"detail" : "ticket removed"}

