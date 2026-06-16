import json
import logging
import os

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from openai import AuthenticationError as OAIAuthError, RateLimitError as OAIRateLimitError, APITimeoutError as OAITimeoutError

from auth import get_current_user
from config import AI_RATE_LIMIT, OPENAI_HISTORY_LIMIT, OPENAI_MODEL, OPENAI_TIMEOUT_SECONDS, _ai_rate_store
from crud import find_board, find_user, make_id, _require_owns_board
from database import get_session
from models import Board, Card, Column, Conversation, User
from schemas import AiChatRequest, AiChatResponse, AiTestRequest, ConversationMessage
from serializers import serialize_board

logger = logging.getLogger("pm-backend")

router = APIRouter()


def _require_openai_api_key() -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY is not set")
    return api_key


def _openai_client():
    from openai import OpenAI

    return OpenAI(api_key=_require_openai_api_key(), timeout=OPENAI_TIMEOUT_SECONDS)


def _extract_response_text(response: object) -> str:
    # The OpenAI SDK's response formats can differ by endpoint/version.
    # Prefer the common `output_text` property when available.
    text = getattr(response, "output_text", None)
    if isinstance(text, str) and text.strip():
        return text.strip()

    return str(response)


def _ai_system_prompt() -> str:
    return (
        "You are an assistant for a project management Kanban board.\n"
        "You will be given:\n"
        "- The current board state as JSON.\n"
        "- The conversation history.\n"
        "Respond with JSON matching the required schema.\n"
        "Output only valid JSON. Do not wrap it in markdown.\n"
        "If suggesting board changes, include them in boardUpdates.\n"
        "Do not invent ids for existing items. For creating a new card, you may omit id.\n"
    )


def _ai_response_schema() -> dict:
    # Keep this schema simple and permissive for the MVP.
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "message": {"type": "string"},
            "boardUpdates": {
                "type": ["object", "null"],
                "additionalProperties": False,
                "properties": {
                    "cards": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                                "id": {"type": ["string", "null"]},
                                "action": {"type": "string"},
                                "title": {"type": ["string", "null"]},
                                "details": {"type": ["string", "null"]},
                                "columnId": {"type": ["string", "null"]},
                                "position": {"type": ["integer", "null"]},
                            },
                            "required": ["action"],
                        },
                    },
                    "columns": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                                "id": {"type": "string"},
                                "title": {"type": "string"},
                            },
                            "required": ["id", "title"],
                        },
                    },
                },
                "required": ["cards", "columns"],
            },
        },
        "required": ["message"],
    }


def _load_conversation_history(
    session: Session, user_id: str, board_id: str
) -> list[Conversation]:
    return list(
        session.scalars(
            select(Conversation)
            .where(Conversation.user_id == user_id, Conversation.board_id == board_id)
            .order_by(Conversation.created_at.desc())
            .limit(OPENAI_HISTORY_LIMIT)
        )
    )[::-1]


def _handle_openai_error(exc: Exception) -> HTTPException:
    if isinstance(exc, OAIAuthError):
        return HTTPException(status_code=401, detail="OpenAI authentication failed")
    if isinstance(exc, OAIRateLimitError):
        return HTTPException(status_code=429, detail="OpenAI rate limit exceeded")
    if isinstance(exc, OAITimeoutError):
        return HTTPException(status_code=504, detail="OpenAI request timed out")
    logger.exception("OpenAI request failed")
    return HTTPException(status_code=502, detail="OpenAI request failed")


def _check_ai_rate_limit(request: Request) -> None:
    import time
    key = request.client.host if request.client else "unknown"
    now = time.time()
    window_start = now - 60
    times = _ai_rate_store.get(key, [])
    times = [t for t in times if t > window_start]
    if len(times) >= AI_RATE_LIMIT:
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again in a minute.")
    times.append(now)
    _ai_rate_store[key] = times


@router.get(
    "/api/ai/history",
    response_model=list[ConversationMessage],
)
def ai_history(
    user_id: str,
    board_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    user = find_user(session, user_id)
    if user.id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    board = find_board(session, board_id)
    _require_owns_board(board, current_user)
    items = _load_conversation_history(session, user.id, board_id)
    return [
        ConversationMessage(
            id=item.id,
            role=item.role,
            message=item.message,
            created_at=item.created_at,
        )
        for item in items
    ]


@router.post("/api/ai/test")
def ai_test(request: Request, payload: AiTestRequest, current_user: User = Depends(get_current_user)):
    _check_ai_rate_limit(request)
    prompt = payload.prompt.strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="prompt must not be empty")

    logger.info("AI test request received prompt_len=%s", len(prompt))

    try:
        client = _openai_client()
        response = client.responses.create(
            model=OPENAI_MODEL,
            input=prompt,
        )
        answer = _extract_response_text(response)
        logger.info("AI test response received answer_len=%s", len(answer))
        return {"status": "ok", "model": OPENAI_MODEL, "answer": answer}
    except HTTPException:
        raise
    except Exception as exc:
        raise _handle_openai_error(exc) from exc


@router.post("/api/ai/chat", response_model=AiChatResponse)
def ai_chat(
    request: Request,
    payload: AiChatRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    _check_ai_rate_limit(request)
    if payload.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    user = find_user(session, payload.user_id)

    board = session.scalar(
        select(Board)
        .where(Board.user_id == user.id)
        .options(selectinload(Board.columns).selectinload(Column.cards))
    )
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")

    if payload.board_id and payload.board_id != board.id:
        raise HTTPException(status_code=404, detail="Board not found")

    history = _load_conversation_history(session, user.id, board.id)

    board_json = serialize_board(board)
    history_json = [{"role": item.role, "message": item.message} for item in history]

    user_message = payload.message.strip()
    if not user_message:
        raise HTTPException(status_code=400, detail="message must not be empty")

    prompt = (
        "Board state:\n"
        f"{json.dumps(board_json, ensure_ascii=False)}\n\n"
        "Conversation history:\n"
        f"{json.dumps(history_json, ensure_ascii=False)}\n\n"
        "Required JSON schema (informal):\n"
        "{\n"
        '  "message": string,\n'
        '  "boardUpdates": null | {\n'
        '    "cards": [{ "action": string, "id"?: string|null, "title"?: string|null, "details"?: string|null, "columnId"?: string|null, "position"?: int|null }],\n'
        '    "columns": [{ "id": string, "title": string }]\n'
        "  }\n"
        "}\n\n"
        f"User message:\n{user_message}\n"
    )

    try:
        client = _openai_client()
        response = client.responses.create(
            model=OPENAI_MODEL,
            input=[
                {"role": "system", "content": _ai_system_prompt()},
                {"role": "user", "content": prompt},
            ],
        )
        raw_text = _extract_response_text(response)
        try:
            parsed = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=502, detail="Malformed AI response") from exc

        chat_response = AiChatResponse.model_validate(parsed)

        if chat_response.boardUpdates:
            valid_cards = []
            for cu in chat_response.boardUpdates.cards:
                action = cu.action.lower()
                if action in ("update", "delete", "move") and cu.id:
                    if not session.get(Card, cu.id):
                        logger.warning("AI suggested invalid card id=%s, skipping", cu.id)
                        continue
                valid_cards.append(cu)
            valid_cols = []
            for col_u in chat_response.boardUpdates.columns:
                if not session.get(Column, col_u.id):
                    logger.warning("AI suggested invalid column id=%s, skipping", col_u.id)
                    continue
                valid_cols.append(col_u)
            chat_response.boardUpdates.cards = valid_cards
            chat_response.boardUpdates.columns = valid_cols

        session.add_all(
            [
                Conversation(
                    id=make_id("conv"),
                    user_id=user.id,
                    board_id=board.id,
                    role="user",
                    message=user_message,
                ),
                Conversation(
                    id=make_id("conv"),
                    user_id=user.id,
                    board_id=board.id,
                    role="assistant",
                    message=chat_response.message,
                ),
            ]
        )
        try:
            session.commit()
        except IntegrityError as exc:
            session.rollback()
            raise HTTPException(status_code=400, detail="Database constraint violation") from exc
        return chat_response
    except HTTPException:
        raise
    except Exception as exc:
        raise _handle_openai_error(exc) from exc
