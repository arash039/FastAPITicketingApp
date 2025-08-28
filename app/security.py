from cryptography.fernet import Fernet
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import CreditCard

cypher_key = Fernet.generate_key()
#cypher_key = b'-GBmAsJ4FELVCHCVydENBvRT59gDyy-nNfCgKnNQ0vg=' 
cypher_suite = Fernet(cypher_key)

def encrypt_credit_card_info(card_info: str) -> str:
	return cypher_suite.encrypt(card_info.encode()).decode()

def decrypt_credit_card_info(enc_card_info: str) -> str:
	return cypher_suite.decrypt(enc_card_info.encode()).decode()

async def store_credit_card_info(
		db_session: AsyncSession,
		card_number: str,
		card_holder_name: str,
		expiration_date: str,
		cvv: str
):
	encrypted_card_number = encrypt_credit_card_info(card_number)
	encrypted_card_cvv = encrypt_credit_card_info(cvv)

	credit_card = CreditCard(
		number = encrypted_card_number,
		holder_name = card_holder_name,
		expiration_date = expiration_date,
		cvv = encrypted_card_cvv
	)

	async with db_session.begin():
		db_session.add(credit_card)
		await db_session.flush()
		credit_card_id = credit_card.id
		await db_session.commit()
	
	return credit_card_id

async def retrive_card_info(
		db_session: AsyncSession,
		card_id: int
):
	query = select(CreditCard).where(CreditCard.id == card_id)

	async with db_session as session:
		result = await session.execute(query)
		credit_card = result.scalars().first()

	card_number = decrypt_credit_card_info(credit_card.number)
	cvv = decrypt_credit_card_info(credit_card.cvv)
	card_holder = credit_card.holder_name
	expiry = credit_card.expiration_date

	return {
		"card_number" : card_number,
		"cvv" : cvv,
		"card_holder" : card_holder,
		"expiry_date" : expiry
	}
