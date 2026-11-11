import asyncio
import json

import httpx
import pytest
from langsmith.run_helpers import get_tracing_context

from agentic_chat.policy import Policy
from agentic_chat.providers import LangChainModels, provider_credentials
from agentic_chat.resilience import ProviderUnavailable
from agentic_chat.testing import SAFE_INPUT


def test_local_provider_never_inherits_openai_key(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-cloud-secret")
    monkeypatch.delenv("LOCAL_MODEL_API_KEY", raising=False)
    endpoint, key = provider_credentials("local", "http://127.0.0.1:11434/v1")
    assert endpoint.endswith("/v1")
    assert key == "local-unused"


@pytest.mark.parametrize(
    "url",
    [
        "http://192.0.2.1/v1",
        "https://example.com/v1",
        "file:///tmp/model",
        "http://user:password@localhost/v1",
        "http://localhost/v1?key=synthetic",
    ],
)
def test_local_endpoint_rejects_unapproved_destinations(url):
    with pytest.raises(ValueError):
        provider_credentials("local", url)


def test_openai_endpoint_cannot_be_redirected_by_environment(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-cloud-secret")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://example.com/v1")
    assert provider_credentials("openai", None)[0] == "https://api.openai.com/v1"
    with pytest.raises(ValueError):
        provider_credentials("openai", "https://example.com/v1")


def test_real_adapter_constructs_without_network_and_disables_retries(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-cloud-secret")
    models = LangChainModels(Policy())
    assert models.responder.max_retries == 0
    assert models.responder.streaming is False
    assert not models._http.follow_redirects
    assert not models._async_http.follow_redirects
    asyncio.run(models.close())


@pytest.mark.parametrize("malformed", [False, True])
def test_sdk_wire_contract_schema_validation_and_tracing_suppression(monkeypatch, malformed):
    requests = []

    def handler(request):
        assert get_tracing_context()["enabled"] is False
        body = json.loads(request.content)
        requests.append(body)
        assert str(request.url) == "https://api.openai.com/v1/chat/completions"
        assert body["response_format"]["type"] == "json_schema"
        assert body["response_format"]["json_schema"]["strict"] is True
        assert [message["role"] for message in body["messages"]] == ["system", "user"]
        evidence = {**SAFE_INPUT, "unexpected": "permission"} if malformed else SAFE_INPUT
        return httpx.Response(
            200,
            json={
                "id": "synthetic-completion",
                "object": "chat.completion",
                "created": 0,
                "model": "gpt-4.1-mini",
                "choices": [
                    {
                        "index": 0,
                        "finish_reason": "stop",
                        "message": {"role": "assistant", "content": json.dumps(evidence)},
                    }
                ],
            },
        )

    class MockAsyncClient(httpx.AsyncClient):
        def __init__(self, **kwargs):
            assert kwargs["trust_env"] is False
            assert kwargs["follow_redirects"] is False
            super().__init__(transport=httpx.MockTransport(handler), **kwargs)

    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-cloud-secret")
    monkeypatch.setenv("LANGSMITH_TRACING", "true")
    monkeypatch.setattr("agentic_chat.providers.httpx.AsyncClient", MockAsyncClient)

    async def scenario():
        models = LangChainModels(Policy(failure_threshold=1))
        try:
            if malformed:
                with pytest.raises(ProviderUnavailable):
                    await models.inspect_input({"message": "Hello"})
                assert models.judge_circuit.state == "open"
            else:
                evidence = await models.inspect_input({"message": "Hello"})
                assert evidence.model_dump() == SAFE_INPUT
            assert len(requests) == 1
        finally:
            await models.close()

    asyncio.run(scenario())


@pytest.mark.parametrize(
    ("language", "instruction"), [("en", "Respond in English"), ("fa", "Respond in Persian")]
)
def test_reply_language_is_a_fixed_system_instruction(monkeypatch, language, instruction):
    requests = []

    def handler(request):
        payload = json.loads(request.content)
        requests.append(payload)
        assert instruction in payload["messages"][0]["content"]
        assert json.loads(payload["messages"][1]["content"])["response_language"] == language
        return httpx.Response(
            200,
            json={
                "id": "synthetic",
                "object": "chat.completion",
                "created": 0,
                "model": "local-test",
                "choices": [
                    {
                        "index": 0,
                        "finish_reason": "stop",
                        "message": {"role": "assistant", "content": "Synthetic reply"},
                    }
                ],
            },
        )

    class MockClient(httpx.AsyncClient):
        def __init__(self, **kwargs):
            super().__init__(transport=httpx.MockTransport(handler), **kwargs)

    monkeypatch.setattr("agentic_chat.providers.httpx.AsyncClient", MockClient)

    async def scenario():
        models = LangChainModels(
            Policy(), provider="local", model="local-test", base_url="http://127.0.0.1:11434/v1"
        )
        try:
            assert (
                await models.respond(
                    {"message": "A drinks question", "response_language": language}
                )
                == "Synthetic reply"
            )
            assert len(requests) == 1
        finally:
            await models.close()

    asyncio.run(scenario())
