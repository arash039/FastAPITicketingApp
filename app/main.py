from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from app.database import Base
from app.db_connection import AsyncSessionLocal, get_db_session, get_engine
from sqlalchemy.ext.asyncio import AsyncSession
from app.operations import create_ticket, update_ticket_price, delete_ticket, get_ticket, update_ticket_details, create_event, create_sponsor, add_sponsor_to_event, get_events_with_sponsors, sell_ticket_to_user
from typing import Annotated
from pydantic import BaseModel, Field
from app.security import store_credit_card_info, retrive_card_info

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

class CreditCardRequest(BaseModel):
	holder_name: str
	number: str
	expiry_date: str
	cvv: str

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

@app.get("/events-with-sponsors")
async def events_with_sponsors(
	db_session: AsyncSession = Depends(get_db_session)
):
    events = await get_events_with_sponsors(db_session)

    return [
        {
            "id": event.id,
            "name": event.name,
            "sponsors": [
                {"id": sponsor.id, "name": sponsor.name}
                for sponsor in event.sponsors
            ]
        }
        for event in events
    ]

@app.post("/creditcard")
async def save_credit_card_info(
	credit_card: CreditCardRequest,
	db_session: AsyncSession = Depends(get_db_session),
):
	credit_crad_id = await store_credit_card_info(
		db_session,
		credit_card.number,
		credit_card.holder_name,
		credit_card.expiry_date,
		credit_card.cvv
	)
	
	return {"creditcard_id" : credit_crad_id}

@app.get("/creditcard/{card_id}")
async def get_credit_card_info(
	card_id: int,
	db_session: AsyncSession = Depends(get_db_session)
):
	credit_card = await retrive_card_info( db_session=db_session, card_id=card_id)
	if credit_card is None:
		raise HTTPException(
			status_code=404,
			detail="card not found"
		)
	return credit_card

@app.put("/sellticket/{ticket_id}")
async def sell_ticket_to_user_route(
	ticket_id: int,
	user: str,
	db_session: AsyncSession = Depends(get_db_session)
):
	ticket = await get_ticket(db_session, ticket_id)

	if not ticket:
		raise HTTPException(
			status_code=404,
			detail="ticket not found"
		)
	
	sell_status =  await sell_ticket_to_user(db_session, ticket_id, user)

	if sell_status == True:
		return f"Ticket sold to {user} successully"
	else:
		return f"Ticket is already sold to {user}"