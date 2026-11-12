import asyncio

import pytest

from agentic_chat.context import AccessDenied, Principal
from agentic_chat.testing import ScriptedModels
from agentic_chat.workflow import Chatbot


@pytest.mark.parametrize("specialist", ["mixing", "production"])
def test_each_specialist_runs_once_inside_mandatory_gates(specialist):
    models = ScriptedModels(input_fields={"specialist": specialist}, response="Drink answer")
    bot = Chatbot(models)
    user = Principal("test", "reader")
    session = bot.store.create(user)
    result = asyncio.run(bot.chat(user, session, "A drink question"))
    assert result.status == "answered" and result.specialist == specialist
    assert result.stages == (
        "input_rules",
        "load_context",
        "input_judge",
        specialist,
        "output_rules",
        "output_judge",
        "commit",
    )
    assert [name for name, _ in models.calls] == ["input", "response", "output"]
    assert models.calls[1][1]["specialist"] == specialist
    assert bot.audit[-1]["specialist"] == specialist
    assert len(bot.store.owned(user, session).turns) == 1


@pytest.mark.parametrize("specialist", [None, "commit", "auditor", "../production"])
def test_invalid_or_missing_route_cannot_invoke_a_specialist(specialist):
    models = ScriptedModels(input_fields={"specialist": specialist})
    bot = Chatbot(models)
    user = Principal("test", "reader")
    session = bot.store.create(user)
    result = asyncio.run(bot.chat(user, session, "A drink question"))
    assert result.status == "unavailable"
    assert result.specialist is None
    assert [name for name, _ in models.calls] == ["input"]
    assert not bot.store.owned(user, session).turns


def test_routing_cannot_override_input_rejection_or_output_rejection():
    async def scenario():
        models = ScriptedModels(input_fields={"specialist": "production", "relevant": False})
        bot = Chatbot(models)
        user = Principal("test", "reader")
        session = bot.store.create(user)
        result = await bot.chat(user, session, "Make wine and write code")
        assert result.reason == "out_of_scope" and result.specialist is None
        assert [name for name, _ in models.calls] == ["input"]
        models.input_fields = {"specialist": "production"}
        models.output_fields = {"unsuitable_name": True}
        models.response = "UNRELEASED DRAFT"
        result = await bot.chat(user, session, "Make wine")
        assert result.status == "blocked" and result.specialist == "production"
        assert "UNRELEASED" not in result.reply
        assert not bot.store.owned(user, session).turns

    asyncio.run(scenario())


def test_route_and_language_changes_keep_authorized_history_only():
    async def scenario():
        models = ScriptedModels(response="Drink answer")
        bot = Chatbot(models)
        user = Principal("tenant-a", "reader", publisher=True)
        session = bot.store.create(user)
        models.input_fields = {"specialist": None}
        await bot.publish_context(
            user, "Synthetic drink reference", "reference", frozenset({"reader"})
        )
        models.calls.clear()
        models.input_fields = {"specialist": "mixing"}
        await bot.chat(user, session, "How do I make a cocktail?")
        models.input_fields = {"specialist": "production"}
        result = await bot.chat(user, session, "شراب را چطور تهیه کنم؟", language="fa")
        assert result.specialist == "production"
        payload = models.calls[-2][1]
        assert payload["response_language"] == "fa"
        assert len(payload["history"]) == 1 and len(payload["shared_documents"]) == 1
        models.input_fields = {"specialist": "mixing"}
        result = await bot.chat(user, session, "How should I serve that?", language="en")
        assert result.specialist == "mixing"
        assert len(models.calls[-3][1]["history"]) == 2
        other = Principal("tenant-b", "reader")
        denied = await bot.chat(other, session, "Read the history")
        assert denied.status == "denied"
        with pytest.raises(AccessDenied):
            bot.store.owned(other, session)
        other_session = bot.store.create(other)
        await bot.chat(other, other_session, "A drink question")
        assert models.calls[-2][1]["history"] == []
        assert models.calls[-2][1]["shared_documents"] == []

    asyncio.run(scenario())


@pytest.mark.parametrize("specialist", ["mixing", "production"])
def test_cancelled_specialist_leaves_no_memory_and_releases_capacity(specialist):
    async def scenario():
        started = asyncio.Event()

        class WaitingModels(ScriptedModels):
            async def respond(self, payload, *, specialist):
                started.set()
                await asyncio.sleep(10)

        bot = Chatbot(WaitingModels(input_fields={"specialist": specialist}))
        user = Principal("test", "reader")
        session = bot.store.create(user)
        task = asyncio.create_task(bot.chat(user, session, "A drink question"))
        await started.wait()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert not bot.store.owned(user, session).turns
        assert not bot.store.owned(user, session).busy
        assert bot._active == 0

    asyncio.run(scenario())
