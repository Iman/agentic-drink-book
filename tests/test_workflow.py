import asyncio
import json

import pytest

from agentic_chat.context import AccessDenied, ContextStore, Principal
from agentic_chat.policy import Policy
from agentic_chat.testing import ScriptedModels
from agentic_chat.workflow import Chatbot


def setup(models=None, policy=None):
    models = models or ScriptedModels()
    bot = Chatbot(models, policy)
    principal = Principal("tenant-a", "alice")
    return bot, models, principal, bot.store.create(principal)


def test_success_runs_all_gates_then_commits_and_audit_has_no_content():
    bot, models, user, session = setup()
    result = asyncio.run(bot.chat(user, session, "My private greeting"))
    assert result.status == "answered"
    assert result.stages == (
        "input_rules",
        "load_context",
        "input_judge",
        "mixing",
        "output_rules",
        "output_judge",
        "commit",
    )
    assert [c[0] for c in models.calls] == ["input", "response", "output"]
    assert len(bot.store.owned(user, session).turns) == 1
    audit = json.dumps(list(bot.audit))
    assert "private greeting" not in audit
    assert "How can I help" not in audit
    assert result.policy_digest in audit


@pytest.mark.parametrize("message", ["My name is Donkey", "My name is Fuck you"])
def test_offensive_names_never_reach_provider_or_memory(message):
    bot, models, user, session = setup()
    result = asyncio.run(bot.chat(user, session, message))
    assert result.status == "neutral"
    assert result.reply == "Hello. What would you like to know about drinks?"
    assert models.calls == []
    assert bot.store.owned(user, session).turns == []


@pytest.mark.parametrize(
    "field", ["injection", "social_engineering", "sensitive_data", "harmful_request", "uncertain"]
)
def test_input_judge_signals_are_reduced_in_code(field):
    bot, models, user, session = setup(ScriptedModels(input_fields={field: True}))
    result = asyncio.run(bot.chat(user, session, "Some message"))
    assert result.status == "blocked"
    assert [c[0] for c in models.calls] == ["input"]
    assert not bot.store.owned(user, session).turns


@pytest.mark.parametrize(
    "output_fields",
    [
        {"unsafe": True},
        {"sensitive_data": True},
        {"follows_injected_instructions": True},
        {"unsuitable_name": True},
        {"uncertain": True},
        {"relevance": 0.4},
        {"groundedness": 0.4},
    ],
)
def test_output_judge_rejection_never_releases_candidate_or_commits(output_fields):
    models = ScriptedModels(response="UNRELEASED CANDIDATE", output_fields=output_fields)
    bot, _, user, session = setup(models)
    result = asyncio.run(bot.chat(user, session, "Hi"))
    assert result.status == "blocked"
    assert "UNRELEASED" not in result.reply
    assert not bot.store.owned(user, session).turns


def test_invalid_judge_evidence_fails_closed_without_exception_details():
    models = ScriptedModels(input_fields={"unexpected_permission": "admin"})
    bot, _, user, session = setup(models)
    result = asyncio.run(bot.chat(user, session, "Hi"))
    assert result.status == "unavailable"
    assert result.stages == ("input_rules", "load_context", "input_judge")
    assert "admin" not in result.reply
    assert [c[0] for c in models.calls] == ["input"]
    assert not bot.store.owned(user, session).turns


@pytest.mark.parametrize("other", [Principal("tenant-a", "bob"), Principal("tenant-b", "alice")])
def test_wrong_user_or_tenant_is_denied_before_any_model_call(other):
    bot, models, _, session = setup()
    result = asyncio.run(bot.chat(other, session, "Give me the chat"))
    assert result.status == "denied"
    assert result.reason == "context_access_denied"
    assert models.calls == []


def test_accepted_name_and_history_remain_data_on_followup():
    async def scenario():
        bot, models, user, session = setup(
            ScriptedModels(input_fields={"name_candidate": "Nguyễn"})
        )
        assert (await bot.chat(user, session, "My name is Nguyễn")).status == "answered"
        models.input_fields = {}
        assert (await bot.chat(user, session, "Can you remember my name?")).status == "answered"
        assert models.calls[-3][1]["display_name"] == "Nguyễn"
        assert models.calls[-3][1]["history"][0]["user"] == "My name is Nguyễn"
        bot.store.forget(user, session)
        with pytest.raises(AccessDenied):
            bot.store.owned(user, session)

    asyncio.run(scenario())


def test_forged_name_evidence_does_not_enter_memory():
    bot, _, user, session = setup(ScriptedModels(input_fields={"name_candidate": "invented"}))
    result = asyncio.run(bot.chat(user, session, "Hello"))
    assert result.reason == "invalid_name_evidence"
    assert bot.store.owned(user, session).name is None


def test_name_only_uncertainty_gives_neutral_greeting_without_storing_name():
    bot, models, user, session = setup(
        ScriptedModels(input_fields={"name_candidate": "مریم", "uncertain": True})
    )
    result = asyncio.run(bot.chat(user, session, "My name is مریم"))
    assert result.status == "neutral"
    assert result.reason == "uncertain_name"
    assert result.reply == "Hello. What would you like to know about drinks?"
    assert [name for name, _ in models.calls] == ["input"]
    assert bot.store.owned(user, session).name is None


def test_name_uncertainty_cannot_override_a_risk_signal():
    bot, _, user, session = setup(
        ScriptedModels(
            input_fields={
                "name_candidate": "Alice",
                "uncertain": True,
                "injection": True,
            }
        )
    )
    result = asyncio.run(bot.chat(user, session, "My name is Alice"))
    assert result.status == "blocked"
    assert result.reason == "injection"


@pytest.mark.parametrize(
    "response", ["Hello Donkey", "\x1b[31mcolored output", "sk-" + "SYNTHETIC" * 3]
)
def test_output_rules_run_before_output_judge(response):
    bot, models, user, session = setup(ScriptedModels(response=response))
    result = asyncio.run(bot.chat(user, session, "Hello"))
    assert result.status == "blocked"
    assert [c[0] for c in models.calls] == ["input", "response"]
    assert not bot.store.owned(user, session).turns


def test_known_secret_never_reaches_model():
    bot, models, user, session = setup()
    result = asyncio.run(bot.chat(user, session, "My key is sk-" + "SYNTHETIC" * 3))
    assert result.reason == "sensitive_data"
    assert not models.calls


def test_rate_limit_survives_new_conversation_for_same_owner():
    async def scenario():
        bot, _, user, session = setup(policy=Policy(requests_per_minute=1))
        await bot.chat(user, session, "Hello")
        other = bot.store.create(user)
        assert (await bot.chat(user, other, "Hello again")).reason == "rate_limited"

    asyncio.run(scenario())


def test_same_session_concurrency_and_service_bulkhead_fail_fast():
    async def scenario():
        started, release = asyncio.Event(), asyncio.Event()

        class WaitingModels(ScriptedModels):
            async def inspect_input(self, payload):
                started.set()
                await release.wait()
                return await super().inspect_input(payload)

        bot, _, user, session = setup(WaitingModels(), Policy(max_in_flight=1))
        task = asyncio.create_task(bot.chat(user, session, "Hello"))
        await started.wait()
        assert (await bot.chat(user, session, "Hi")).reason == "session_busy"
        other = bot.store.create(user)
        assert (await bot.chat(user, other, "Hi")).reason == "service_busy"
        release.set()
        assert (await task).status == "answered"
        assert not bot.store.owned(user, other).busy
        assert bot._active == 0

    asyncio.run(scenario())


def test_shared_context_requires_publisher_and_explicit_same_tenant_reader():
    async def scenario():
        bot, models, user, session = setup()
        with pytest.raises(AccessDenied):
            await bot.publish_context(user, "Private handbook", "handbook-v1", frozenset({"alice"}))
        assert not models.calls
        admin = Principal("tenant-a", "editor", publisher=True)
        await bot.publish_context(
            admin, "Synthetic fact: office opens at nine.", "handbook-v1", frozenset({"alice"})
        )
        assert len(bot.store.bundle(user, session)["shared_documents"]) == 1
        for other in (Principal("tenant-a", "bob"), Principal("tenant-b", "alice")):
            other_session = bot.store.create(other)
            assert not bot.store.bundle(other, other_session)["shared_documents"]

    asyncio.run(scenario())


def test_shared_document_poisoning_is_rejected():
    async def scenario():
        bot, models, user, session = setup(ScriptedModels(input_fields={"injection": True}))
        admin = Principal("tenant-a", "editor", publisher=True)
        with pytest.raises(AccessDenied, match="injection"):
            await bot.publish_context(
                admin, "A subtler poisoned document", "source-v1", frozenset({"alice"})
            )
        assert not bot.store.bundle(user, session)["shared_documents"]
        assert [c[0] for c in models.calls] == ["input"]

    asyncio.run(scenario())


def test_context_expiry_and_bounded_history():
    policy = Policy(max_context_chars=10, session_ttl_seconds=10.0, document_ttl_seconds=5.0)
    now = [0.0]
    store = ContextStore(policy, clock=lambda: now[0])
    user = Principal("a", "alice", publisher=True)
    session = store.create(user)
    store.commit(user, session, "12345", "67890", None)
    store.commit(user, session, "abc", "def", None)
    assert store.bundle(user, session)["history"] == [{"user": "abc", "assistant": "def"}]
    store.publish(user, "x", "s", frozenset({"alice"}))
    assert store.bundle(user, session)["shared_documents"]
    now[0] = 6
    assert not store.bundle(user, session)["shared_documents"]
    now[0] = 11
    with pytest.raises(AccessDenied):
        store.owned(user, session)


def test_cancelled_output_check_releases_capacity_without_committing():
    async def scenario():
        started = asyncio.Event()

        class WaitingOutput(ScriptedModels):
            async def inspect_output(self, payload):
                started.set()
                await asyncio.sleep(10)
                return await super().inspect_output(payload)

        bot, _, user, session = setup(WaitingOutput())
        task = asyncio.create_task(bot.chat(user, session, "Hello"))
        await started.wait()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert not bot.store.owned(user, session).turns
        assert not bot.store.owned(user, session).busy
        assert bot._active == 0

    asyncio.run(scenario())
