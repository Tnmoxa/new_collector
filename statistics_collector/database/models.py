from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.orm import MappedAsDataclass, DeclarativeBase


class Base(DeclarativeBase, MappedAsDataclass):
    pass


class ReturnToWork(Base):
    __tablename__ = 'return_to_work'

    queue: Mapped[str] = mapped_column(String)
    priority: Mapped[str] = mapped_column(String)
    type: Mapped[str] = mapped_column(String)
    key: Mapped[str] = mapped_column(String, primary_key=True)
    summary: Mapped[str] = mapped_column(String)
    assignee: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String)
    returns_to_work: Mapped[int] = mapped_column(Integer)
