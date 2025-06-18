from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.orm import MappedAsDataclass, DeclarativeBase


class Base(DeclarativeBase, MappedAsDataclass):
    pass


class ReturnToWorkFromTests(Base):
    __tablename__ = 'return_to_work_from_tests'

    queue: Mapped[str] = mapped_column(String)
    priority: Mapped[str] = mapped_column(String)
    type: Mapped[str] = mapped_column(String)
    key: Mapped[str] = mapped_column(String, primary_key=True)
    summary: Mapped[str] = mapped_column(String)
    assignee: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String)
    returns_to_work: Mapped[int] = mapped_column(Integer)


class ReturnToWorkFromReview(Base):
    __tablename__ = 'return_to_work_from_review'

    queue: Mapped[str] = mapped_column(String)
    priority: Mapped[str] = mapped_column(String)
    type: Mapped[str] = mapped_column(String)
    key: Mapped[str] = mapped_column(String, primary_key=True)
    summary: Mapped[str] = mapped_column(String)
    assignee: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String)
    returns_to_work_from_review: Mapped[int] = mapped_column(Integer)


class DevDuration(Base):
    __tablename__ = 'dev_duration'

    queue: Mapped[str] = mapped_column(String)
    priority: Mapped[str] = mapped_column(String)
    type: Mapped[str] = mapped_column(String)
    key: Mapped[str] = mapped_column(String, primary_key=True)
    summary: Mapped[str] = mapped_column(String)
    assignee: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String)
    start_date: Mapped[str] = mapped_column(String)
    end_date: Mapped[str] = mapped_column(String)
    duration: Mapped[str] = mapped_column(String)
    parent_tag: Mapped[str] = mapped_column(String)
    returns_to_work_from_review: Mapped[int] = mapped_column(Integer)
