import uuid

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from models import Board, Card, Column, User


def make_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def touch(entity: Board | Column | Card) -> None:
    entity.updated_at = func.current_timestamp()


def find_user(session: Session, user_id: str) -> User:
    user = session.get(User, user_id)
    if not user:
        user = session.scalar(select(User).where(User.username == user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def find_board(session: Session, board_id: str) -> Board:
    board = session.get(Board, board_id)
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")
    return board


def find_column(session: Session, column_id: str) -> Column:
    column = session.get(Column, column_id)
    if not column:
        raise HTTPException(status_code=404, detail="Column not found")
    return column


def find_card(session: Session, card_id: str) -> Card:
    card = session.get(Card, card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    return card


def cards_for_column(session: Session, column_id: str) -> list[Card]:
    return list(
        session.scalars(
            select(Card).where(Card.column_id == column_id).order_by(Card.position)
        )
    )


def rewrite_positions(session: Session, cards: list[Card]) -> None:
    for position, card in enumerate(cards):
        card.position = -(position + 1)
    session.flush()
    for position, card in enumerate(cards):
        card.position = position
        touch(card)


def _require_owns_board(board: Board, current_user: User) -> None:
    if board.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
