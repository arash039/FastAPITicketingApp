from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from app.database import Base
from app.db_connection import AsyncSessionLocal, get_db_session, get_engine
from sqlalchemy.ext.asyncio import AsyncSession
from app.operations import create_ticket, update_ticket_price, delete_ticket, get_ticket, update_ticket_details, create_event, create_sponsor, add_sponsor_to_event
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

class TicketDetailsUpdateRequest(BaseModel):
	seat: str | None = None
	ticket_type: str | None = None

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

@app.get("/ticket/{ticket_id}")
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

@app.put("/ticket/{ticket_id}")
async def update_ticket_details_route(
	ticket_id: int,
	ticket_update: TicketDetailsUpdateRequest,
	db_session: Annotated[AsyncSession, Depends(get_db_session)]
):
	update_dict_args = ticket_update.model_dump(exclude_unset=True)
	updated = await update_ticket_details(db_session, ticket_id, update_dict_args)

	if not updated:
		raise HTTPException(
			status_code=404, detail="ticket not found"
		)
	return {"detail" : "ticket details updated"}

@app.put("/ticket/{ticket_id}/price/{new_price}")
async def update_ticket_price_route(
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

@app.post("/event", response_model = dict[str, int])
async def create_event_route(
	db_session: Annotated[AsyncSession, Depends(get_db_session)],
	event_name: str,
	nb_tickets: int | None = 0
):
	event_id = await create_event(db_session, event_name, nb_tickets)
	return {"event_id": event_id}

@app.post(
    "/sponsor/{sponsor_name}",
    response_model=dict[str, int],
    responses={
        200: {
            "description": "Successful Response",
            "content": {
                "application/json": {
                    "example": {"sponsor_id": 12345}
                }
            },
        }
    },
)
async def register_sponsor(
    db_session: Annotated[
        AsyncSession, Depends(get_db_session)
    ],
    sponsor_name: str,
):
    sponsor_id = await create_sponsor(
        db_session, sponsor_name
    )
    if not sponsor_id:
        raise HTTPException(
            status_code=400,
            detail="Sponsor not created",
        )

    return {"sponsor_id": sponsor_id}

@app.post("/event/{event_id}/sponsor/{sponsor_id}")
async def register_sponsor_amount_contribution(
    db_session: Annotated[
        AsyncSession, Depends(get_db_session)
    ],
    sponsor_id: int,
    event_id: int,
    amount: float | None = 0,
):
    registered = await add_sponsor_to_event(
        db_session, event_id, sponsor_id, amount
    )
    if not registered:
        raise HTTPException(
            status_code=400,
            detail="Contribution not registered",
        )

    return {"detail": "Contribution registered"}