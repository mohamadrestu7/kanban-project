from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from auth import create_access_token, get_current_user
from crud import find_user, make_id
from database import get_session
from models import Board, User
from schemas import LoginRequest, UserCreate
from seed import hash_password, verify_password
from serializers import serialize_user

router = APIRouter()


@router.post("/api/users", status_code=201)
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
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(status_code=400, detail="Database constraint violation") from exc
    session.refresh(user)
    return serialize_user(user)


@router.post("/api/login")
def login(payload: LoginRequest, session: Session = Depends(get_session)):
    user = session.scalar(select(User).where(User.username == payload.username))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(user.id)
    return {"userId": user.id, "username": user.username, "token": token}


@router.get("/api/users/{user_id}")
def get_user(
    user_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    user = find_user(session, user_id)
    if user.id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    return serialize_user(user)
