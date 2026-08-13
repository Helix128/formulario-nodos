from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, create_engine, event
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker


class Base(DeclarativeBase):
    pass


class Response(Base):
    __tablename__ = "responses"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(250))
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    preference_1: Mapped[str] = mapped_column(String(100))
    preference_2: Mapped[str] = mapped_column(String(100))
    additional_idea: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    slots: Mapped[list["ResponseSlot"]] = relationship(cascade="all, delete-orphan")


class ResponseSlot(Base):
    __tablename__ = "response_slots"
    __table_args__ = (UniqueConstraint("response_id", "day_id", "slot_id", name="uq_response_slot"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    response_id: Mapped[int] = mapped_column(ForeignKey("responses.id", ondelete="CASCADE"), index=True)
    day_id: Mapped[str] = mapped_column(String(100))
    slot_id: Mapped[str] = mapped_column(String(100))
    busy: Mapped[bool] = mapped_column(default=False)


def make_session_factory(database_path):
    database_path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{database_path}", connect_args={"check_same_thread": False})
    @event.listens_for(engine, "connect")
    def configure_sqlite(dbapi_connection, _):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False), engine
