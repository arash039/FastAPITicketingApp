from sqlalchemy import Column, Float, ForeignKey, Table
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
	pass

class Ticket(Base):
	__tablename__ = "tickets"

	id: Mapped[int] = mapped_column(primary_key=True)
	price: Mapped[float] = mapped_column(nullable=True)
	show: Mapped[str | None]
	user: Mapped[str | None]