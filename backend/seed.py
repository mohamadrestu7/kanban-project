import bcrypt as _bcrypt_lib

from sqlalchemy.orm import Session

from models import Board, Card, Column, User


DEFAULT_USER_ID = "user_default"
DEFAULT_BOARD_ID = "board_default"

DEFAULT_COLUMNS = [
    ("col-backlog", "Backlog"),
    ("col-discovery", "Discovery"),
    ("col-progress", "In Progress"),
    ("col-review", "Review"),
    ("col-done", "Done"),
]

DEFAULT_CARDS = [
    (
        "card-1",
        "col-backlog",
        "Align roadmap themes",
        "Draft quarterly themes with impact statements and metrics.",
    ),
    (
        "card-2",
        "col-backlog",
        "Gather customer signals",
        "Review support tags, sales notes, and churn feedback.",
    ),
    (
        "card-3",
        "col-discovery",
        "Prototype analytics view",
        "Sketch initial dashboard layout and key drill-downs.",
    ),
    (
        "card-4",
        "col-progress",
        "Refine status language",
        "Standardize column labels and tone across the board.",
    ),
    (
        "card-5",
        "col-progress",
        "Design card layout",
        "Add hierarchy and spacing for scanning dense lists.",
    ),
    (
        "card-6",
        "col-review",
        "QA micro-interactions",
        "Verify hover, focus, and loading states.",
    ),
    (
        "card-7",
        "col-done",
        "Ship marketing page",
        "Final copy approved and asset pack delivered.",
    ),
    (
        "card-8",
        "col-done",
        "Close onboarding sprint",
        "Document release notes and share internally.",
    ),
]


def hash_password(password: str) -> str:
    return _bcrypt_lib.hashpw(password.encode("utf-8"), _bcrypt_lib.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return _bcrypt_lib.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def seed_default_data(session: Session) -> None:
    user = session.get(User, DEFAULT_USER_ID)
    if not user:
        user = User(
            id=DEFAULT_USER_ID,
            username="user",
            password_hash=hash_password("password"),
        )
        session.add(user)

    board = session.get(Board, DEFAULT_BOARD_ID)
    if not board:
        board = Board(id=DEFAULT_BOARD_ID, user_id=DEFAULT_USER_ID, title="My Board")
        session.add(board)

    for position, (column_id, title) in enumerate(DEFAULT_COLUMNS):
        if not session.get(Column, column_id):
            session.add(
                Column(
                    id=column_id,
                    board_id=DEFAULT_BOARD_ID,
                    title=title,
                    position=position,
                )
            )

    positions_by_column: dict[str, int] = {}
    for card_id, column_id, title, details in DEFAULT_CARDS:
        if not session.get(Card, card_id):
            position = positions_by_column.get(column_id, 0)
            session.add(
                Card(
                    id=card_id,
                    column_id=column_id,
                    title=title,
                    details=details,
                    position=position,
                )
            )
            positions_by_column[column_id] = position + 1

    session.commit()

