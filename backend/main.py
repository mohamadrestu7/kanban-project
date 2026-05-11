import os
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from database import SessionLocal, create_db, get_session
from models import Board, Card, Column, User
from seed import seed_default_data, hash_password

load_dotenv()


class UserCreate(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(default="password", min_length=1)


class BoardUpdate(BaseModel):
    title: str = Field(min_length=1)


class ColumnUpdate(BaseModel):
    title: str = Field(min_length=1)


class CardCreate(BaseModel):
    title: str = Field(min_length=1)
    details: str = ""


class CardUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1)
    details: str | None = None


class CardMove(BaseModel):
    column_id: str
    position: int | None = Field(default=None, ge=0)


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db()
    with SessionLocal() as session:
        seed_default_data(session)
    print("Application startup")
    yield
    print("Application shutdown")


app = FastAPI(title="PM Backend", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3100",
        "http://localhost:8000",
        "http://127.0.0.1:3100",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


def serialize_user(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "created_at": user.created_at,
    }


def serialize_card(card: Card) -> dict:
    return {
        "id": card.id,
        "title": card.title,
        "details": card.details,
        "columnId": card.column_id,
        "position": card.position,
        "created_at": card.created_at,
        "updated_at": card.updated_at,
    }


def serialize_column(column: Column) -> dict:
    return {
        "id": column.id,
        "title": column.title,
        "position": column.position,
        "cardIds": [card.id for card in sorted(column.cards, key=lambda item: item.position)],
        "created_at": column.created_at,
        "updated_at": column.updated_at,
    }


def serialize_board(board: Board) -> dict:
    columns = sorted(board.columns, key=lambda item: item.position)
    cards = {
        card.id: serialize_card(card)
        for column in columns
        for card in sorted(column.cards, key=lambda item: item.position)
    }
    return {
        "id": board.id,
        "title": board.title,
        "userId": board.user_id,
        "columns": [serialize_column(column) for column in columns],
        "cards": cards,
        "created_at": board.created_at,
        "updated_at": board.updated_at,
    }


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


@app.get("/api/test", response_model=dict)
async def test_endpoint():
    return {
        "status": "ok",
        "message": "API is running",
        "version": "0.1.0",
    }


@app.post("/api/users", status_code=201)
def create_user(payload: UserCreate, session: Session = Depends(get_session)):
    existing = session.scalar(select(User).where(User.username == payload.username))
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")

    user = User(
        id=make_id("user"),
        username=payload.username,
        password_hash=hash_password(payload.password),
    )
    board = Board(id=make_id("board"), user_id=user.id, title="My Board")
    session.add_all([user, board])
    session.commit()
    session.refresh(user)
    return serialize_user(user)


@app.get("/api/users/{user_id}")
def get_user(user_id: str, session: Session = Depends(get_session)):
    return serialize_user(find_user(session, user_id))


@app.get("/api/users/{user_id}/board")
def get_user_board(user_id: str, session: Session = Depends(get_session)):
    user = find_user(session, user_id)
    board = session.scalar(
        select(Board)
        .where(Board.user_id == user.id)
        .options(selectinload(Board.columns).selectinload(Column.cards))
    )
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")
    return serialize_board(board)


@app.put("/api/users/{user_id}/board")
def update_user_board(
    user_id: str,
    payload: BoardUpdate,
    session: Session = Depends(get_session),
):
    user = find_user(session, user_id)
    board = session.scalar(select(Board).where(Board.user_id == user.id))
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")
    board.title = payload.title
    touch(board)
    session.commit()
    session.refresh(board)
    return serialize_board(
        session.scalar(
            select(Board)
            .where(Board.id == board.id)
            .options(selectinload(Board.columns).selectinload(Column.cards))
        )
    )


@app.get("/api/boards/{board_id}/columns")
def list_columns(board_id: str, session: Session = Depends(get_session)):
    find_board(session, board_id)
    columns = session.scalars(
        select(Column)
        .where(Column.board_id == board_id)
        .options(selectinload(Column.cards))
        .order_by(Column.position)
    )
    return [serialize_column(column) for column in columns]


@app.put("/api/boards/{board_id}/columns/{column_id}")
def update_column(
    board_id: str,
    column_id: str,
    payload: ColumnUpdate,
    session: Session = Depends(get_session),
):
    find_board(session, board_id)
    column = find_column(session, column_id)
    if column.board_id != board_id:
        raise HTTPException(status_code=404, detail="Column not found")
    column.title = payload.title
    touch(column)
    session.commit()
    session.refresh(column)
    return serialize_column(column)


@app.post("/api/columns/{column_id}/cards", status_code=201)
def create_card(
    column_id: str,
    payload: CardCreate,
    session: Session = Depends(get_session),
):
    find_column(session, column_id)
    position = len(cards_for_column(session, column_id))
    card = Card(
        id=make_id("card"),
        column_id=column_id,
        title=payload.title,
        details=payload.details,
        position=position,
    )
    session.add(card)
    session.commit()
    session.refresh(card)
    return serialize_card(card)


@app.put("/api/cards/{card_id}")
def update_card(
    card_id: str,
    payload: CardUpdate,
    session: Session = Depends(get_session),
):
    card = find_card(session, card_id)
    if payload.title is not None:
        card.title = payload.title
    if payload.details is not None:
        card.details = payload.details
    touch(card)
    session.commit()
    session.refresh(card)
    return serialize_card(card)


@app.delete("/api/cards/{card_id}")
def delete_card(card_id: str, session: Session = Depends(get_session)):
    card = find_card(session, card_id)
    column_id = card.column_id
    session.delete(card)
    session.flush()
    rewrite_positions(session, cards_for_column(session, column_id))
    session.commit()
    return {"status": "ok", "deleted_id": card_id}


@app.patch("/api/cards/{card_id}/move")
def move_card(
    card_id: str,
    payload: CardMove,
    session: Session = Depends(get_session),
):
    card = find_card(session, card_id)
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
    session.commit()
    session.refresh(card)
    return serialize_card(card)


static_dir = Path(__file__).parent / "public" / "out"
if (static_dir / "index.html").exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
else:

    @app.get("/", response_class=HTMLResponse)
    async def serve_root():
        return """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Project Management MVP</title>
        </head>
        <body>
            <main>
                <h1>Project Management MVP</h1>
                <p>API Server Active</p>
                <p>Port: 8000</p>
                <p>Framework: FastAPI</p>
                <p>Next Steps: Build the frontend and visit <a href="/api/test">/api/test</a>.</p>
            </main>
        </body>
        </html>
        """


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
