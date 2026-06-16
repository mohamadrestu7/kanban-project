from typing import Literal

from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


class LoginRequest(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


class AiTestRequest(BaseModel):
    prompt: str = Field(min_length=1)


class AiChatRequest(BaseModel):
    user_id: str = Field(min_length=1)
    message: str = Field(min_length=1)
    board_id: str | None = None


class AiCardUpdate(BaseModel):
    id: str | None = None
    action: str = Field(min_length=1)
    title: str | None = None
    details: str | None = None
    columnId: str | None = None
    position: int | None = None


class AiColumnUpdate(BaseModel):
    id: str = Field(min_length=1)
    title: str = Field(min_length=1)


class AiBoardUpdates(BaseModel):
    cards: list[AiCardUpdate] = []
    columns: list[AiColumnUpdate] = []


class AiChatResponse(BaseModel):
    message: str
    boardUpdates: AiBoardUpdates | None = None


class ConversationMessage(BaseModel):
    id: str
    role: Literal["user", "assistant"]
    message: str
    created_at: str


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
