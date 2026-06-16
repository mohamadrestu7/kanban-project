class DummyOpenAiResponse:
    output_text = "4"


class DummyResponses:
    def __init__(self, response: object):
        self._response = response

    def create(self, **_kwargs):
        return self._response


class DummyOpenAI:
    def __init__(self, response: object):
        self.responses = DummyResponses(response)

class DummyOpenAIFailure:
    class _Responses:
        def __init__(self, exc: Exception):
            self._exc = exc

        def create(self, **_kwargs):
            raise self._exc

    def __init__(self, exc: Exception):
        self.responses = self._Responses(exc)


def test_ai_test_missing_key_returns_500(client, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    response = client.post("/api/ai/test", json={"prompt": "What is 2+2?"})
    assert response.status_code == 500
    assert response.json()["detail"] == "OPENAI_API_KEY is not set"


def test_ai_test_success_returns_answer(client, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    import routers.ai as ai_router

    monkeypatch.setattr(ai_router, "_openai_client", lambda: DummyOpenAI(DummyOpenAiResponse()))
    response = client.post("/api/ai/test", json={"prompt": "What is 2+2?"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["answer"] == "4"


def test_ai_test_timeout_maps_to_504(client, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    import routers.ai as ai_router
    from openai import APITimeoutError

    monkeypatch.setattr(
        ai_router,
        "_openai_client",
        lambda: DummyOpenAIFailure(APITimeoutError(request=None)),
    )

    response = client.post("/api/ai/test", json={"prompt": "ping"})
    assert response.status_code == 504
    assert response.json()["detail"] == "OpenAI request timed out"

