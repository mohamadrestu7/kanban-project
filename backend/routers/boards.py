from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from auth import get_current_user
from crud import (
    _require_owns_board,
    cards_for_column,
    find_board,
    find_card,
    find_column,
    find_user,
    make_id,
    rewrite_positions,
    touch,
)
from database import get_session
from models import Board, Card, Column, User
from schemas import BoardUpdate, CardCreate, CardMove, CardUpdate, ColumnUpdate
from serializers import serialize_board, serialize_card, serialize_column

router = APIRouter()


@router.get("/api/users/{user_id}/board")
def get_user_board(
    user_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    user = find_user(session, user_id)
    if user.id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    board = session.scalar(
        select(Board)
        .where(Board.user_id == user.id)
        .options(selectinload(Board.columns).selectinload(Column.cards))
    )
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")
    return serialize_board(board)


@router.put("/api/users/{user_id}/board")
def update_user_board(
    user_id: str,
    payload: BoardUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    user = find_user(session, user_id)
    if user.id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    board = session.scalar(select(Board).where(Board.user_id == user.id))
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")
    board.title = payload.title
    touch(board)
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(status_code=400, detail="Database constraint violation") from exc
    session.refresh(board)
    return serialize_board(
        session.scalar(
            select(Board)
            .where(Board.id == board.id)
            .options(selectinload(Board.columns).selectinload(Column.cards))
        )
    )


@router.get("/api/boards/{board_id}/columns")
def list_columns(
    board_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    board = find_board(session, board_id)
    _require_owns_board(board, current_user)
    columns = session.scalars(
        select(Column)
        .where(Column.board_id == board_id)
        .options(selectinload(Column.cards))
        .order_by(Column.position)
    )
    return [serialize_column(column) for column in columns]


@router.put("/api/boards/{board_id}/columns/{column_id}")
def update_column(
    board_id: str,
    column_id: str,
    payload: ColumnUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    board = find_board(session, board_id)
    _require_owns_board(board, current_user)
    column = find_column(session, column_id)
    if column.board_id != board_id:
        raise HTTPException(status_code=404, detail="Column not found")
    column.title = payload.title
    touch(column)
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(status_code=400, detail="Database constraint violation") from exc
    session.refresh(column)
    return serialize_column(column)


@router.post("/api/columns/{column_id}/cards", status_code=201)
def create_card(
    column_id: str,
    payload: CardCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    column = find_column(session, column_id)
    board = find_board(session, column.board_id)
    _require_owns_board(board, current_user)
    position = len(cards_for_column(session, column_id))
    card = Card(
        id=make_id("card"),
        column_id=column_id,
        title=payload.title,
        details=payload.details,
        position=position,
    )
    session.add(card)
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(status_code=400, detail="Database constraint violation") from exc
    session.refresh(card)
    return serialize_card(card)


@router.put("/api/cards/{card_id}")
def update_card(
    card_id: str,
    payload: CardUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    card = find_card(session, card_id)
    column = find_column(session, card.column_id)
    board = find_board(session, column.board_id)
    _require_owns_board(board, current_user)
    if payload.title is not None:
        card.title = payload.title
    if payload.details is not None:
        card.details = payload.details
    touch(card)
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(status_code=400, detail="Database constraint violation") from exc
    session.refresh(card)
    return serialize_card(card)


@router.delete("/api/cards/{card_id}")
def delete_card(
    card_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    card = find_card(session, card_id)
    column = find_column(session, card.column_id)
    board = find_board(session, column.board_id)
    _require_owns_board(board, current_user)
    column_id = card.column_id
    session.delete(card)
    session.flush()
    rewrite_positions(session, cards_for_column(session, column_id))
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(status_code=400, detail="Database constraint violation") from exc
    return {"status": "ok", "deleted_id": card_id}


@router.patch("/api/cards/{card_id}/move")
def move_card(
    card_id: str,
    payload: CardMove,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    card = find_card(session, card_id)
    column = find_column(session, card.column_id)
    board = find_board(session, column.board_id)
    _require_owns_board(board, current_user)
    find_column(session, payload.column_id)
    source_column_id = card.column_id

    source_cards = [item for item in cards_for_column(session, source_column_id) if item.id != card.id]
    target_cards = cards_for_column(session, payload.column_id)
    if source_column_id == payload.column_id:
        target_cards = [item for item in target_cards if item.id != card.id]

    insert_at = payload.position if payload.position is not None else len(target_cards)
    insert_at = min(insert_at, len(target_cards))
    card.position = -999
    session.flush()
    card.column_id = payload.column_id
    session.flush()
    target_cards.insert(insert_at, card)

    if source_column_id != payload.column_id:
        rewrite_positions(session, source_cards)
    rewrite_positions(session, target_cards)
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(status_code=400, detail="Database constraint violation") from exc
    session.refresh(card)
    return serialize_card(card)
