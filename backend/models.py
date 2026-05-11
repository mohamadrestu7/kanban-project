from sqlalchemy import CheckConstraint, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[str] = mapped_column(String, server_default=func.current_timestamp())

    board: Mapped["Board"] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
    )
    conversations: Mapped[list["Conversation"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


class Board(Base):
    __tablename__ = "boards"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String, nullable=False, default="My Board")
    created_at: Mapped[str] = mapped_column(String, server_default=func.current_timestamp())
    updated_at: Mapped[str] = mapped_column(String, server_default=func.current_timestamp())

    user: Mapped[User] = relationship(back_populates="board")
    columns: Mapped[list["Column"]] = relationship(
        back_populates="board",
        cascade="all, delete-orphan",
        order_by="Column.position",
    )
    conversations: Mapped[list["Conversation"]] = relationship(
        back_populates="board",
        cascade="all, delete-orphan",
    )


class Column(Base):
    __tablename__ = "columns"
    __table_args__ = (UniqueConstraint("board_id", "position"),)

    id: Mapped[str] = mapped_column(String, primary_key=True)
    board_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("boards.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String, nullable=False)
    position: Mapped[int] = mapped_column(nullable=False)
    created_at: Mapped[str] = mapped_column(String, server_default=func.current_timestamp())
    updated_at: Mapped[str] = mapped_column(String, server_default=func.current_timestamp())

    board: Mapped[Board] = relationship(back_populates="columns")
    cards: Mapped[list["Card"]] = relationship(
        back_populates="column",
        cascade="all, delete-orphan",
        order_by="Card.position",
    )


class Card(Base):
    __tablename__ = "cards"
    __table_args__ = (UniqueConstraint("column_id", "position"),)

    id: Mapped[str] = mapped_column(String, primary_key=True)
    column_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("columns.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String, nullable=False)
    details: Mapped[str] = mapped_column(String, nullable=False, default="")
    position: Mapped[int] = mapped_column(nullable=False)
    created_at: Mapped[str] = mapped_column(String, server_default=func.current_timestamp())
    updated_at: Mapped[str] = mapped_column(String, server_default=func.current_timestamp())

    column: Mapped[Column] = relationship(back_populates="cards")


class Conversation(Base):
    __tablename__ = "conversations"
    __table_args__ = (CheckConstraint("role IN ('user', 'assistant')"),)

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    board_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("boards.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(String, nullable=False)
    message: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[str] = mapped_column(String, server_default=func.current_timestamp())

    user: Mapped[User] = relationship(back_populates="conversations")
    board: Mapped[Board] = relationship(back_populates="conversations")

