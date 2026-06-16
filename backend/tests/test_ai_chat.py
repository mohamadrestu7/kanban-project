import json

from sqlalchemy import select

from models import Conversation


class DummyAiResponse:
    def __init__(self, output_text: str):
        self.output_text = output_text


class DummyResponses:
    def __init__(self, output_text: str, recorder: dict):
        self._output_text = output_text
        self._recorder = recorder

    def create(self, **kwargs):
        self._recorder["kwargs"] = kwargs
        return DummyAiResponse(self._output_text)


class DummyOpenAI:
    def __init__(self, output_text: str, recorder: dict):
        self.responses = DummyResponses(output_text, recorder)


def test_ai_chat_saves_history_and_includes_board_state(client, db_session, monkeypatch):
    import routers.ai as ai_router
    from config import OPENAI_MODEL

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    recorder: dict = {}
    output = json.dumps({"message": "Hello from AI", "boardUpdates": None})
    monkeypatch.setattr(ai_router, "_openai_client", lambda: DummyOpenAI(output, recorder))

    response = client.post(
        "/api/ai/chat",
        json={"user_id": "user_default", "board_id": "board_default", "message": "Hi"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Hello from AI"

    saved = list(
        db_session.scalars(
            select(Conversation)
            .where(
                Conversation.user_id == "user_default",
                Conversation.board_id == "board_default",
            )
            .order_by(Conversation.created_at)
        )
    )
    assert saved[-2].role == "user"
    assert saved[-2].message == "Hi"
    assert saved[-1].role == "assistant"
    assert saved[-1].message == "Hello from AI"

    # Verify we passed board state and history to OpenAI prompt.
    kwargs = recorder["kwargs"]
    assert kwargs["model"] == OPENAI_MODEL
    assert isinstance(kwargs["input"], list)
    user_prompt = kwargs["input"][1]["content"]
    assert '"id": "board_default"' in user_prompt
    assert '"Conversation history"' in user_prompt or "Conversation history" in user_prompt


def test_ai_chat_malformed_json_returns_502(client, monkeypatch):
    import routers.ai as ai_router

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    recorder: dict = {}
    monkeypatch.setattr(ai_router, "_openai_client", lambda: DummyOpenAI("not-json", recorder))

    response = client.post(
        "/api/ai/chat",
        json={"user_id": "user_default", "board_id": "board_default", "message": "Hi"},
    )
    assert response.status_code == 502
    assert response.json()["detail"] == "Malformed AI response"

