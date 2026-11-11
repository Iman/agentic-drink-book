import asyncio

from agentic_chat.context import Principal
from agentic_chat.testing import ScriptedModels
from agentic_chat.workflow import Chatbot


def run(models, message):
    bot = Chatbot(models)
    user = Principal("test", "reader")
    session = bot.store.create(user)
    result = asyncio.run(bot.chat(user, session, message))
    return result, bot.store.owned(user, session).turns


def test_off_topic_request_stops_before_generation_even_with_uncertain_name():
    models = ScriptedModels(
        input_fields={"relevant": False, "uncertain": True, "name_candidate": "Alex"}
    )
    result, history = run(models, "My name is Alex. Write a sorting algorithm.")
    assert result.status == "blocked"
    assert result.reason == "out_of_scope"
    assert "drinks" in result.reply
    assert [call[0] for call in models.calls] == ["input"]
    assert not history


def test_off_topic_draft_is_discarded_even_when_scores_are_high():
    models = ScriptedModels(response="UNRELATED DRAFT", output_fields={"in_scope": False})
    result, history = run(models, "How do I mix a Negroni?")
    assert result.status == "blocked"
    assert result.reason == "out_of_scope"
    assert "UNRELATED" not in result.reply
    assert not history
