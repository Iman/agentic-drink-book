import asyncio

from behave import given, then, when

from agentic_chat.context import AccessDenied, Principal
from agentic_chat.policy import Policy
from agentic_chat.resilience import CircuitBreaker, ProviderUnavailable
from agentic_chat.testing import ScriptedModels
from agentic_chat.workflow import Chatbot


@given("a chatbot with scripted healthy models")
def chatbot(context):
    context.models = ScriptedModels()
    context.bot = Chatbot(context.models)
    context.user = Principal("tenant-a", "alice")
    context.session = context.bot.store.create(context.user)


@given("a one-request-per-minute policy")
def limited(context):
    context.bot = Chatbot(context.models, Policy(requests_per_minute=1))
    context.session = context.bot.store.create(context.user)


@given("the input judge reports social engineering")
def social_engineering(context):
    context.models.input_fields = {"social_engineering": True}


@given("the input judge returns an invalid schema")
def broken_judge(context):
    context.models.input_fields = {"undeclared_field": True}


@given("the output judge reports an unsafe draft")
def unsafe_draft(context):
    context.models.output_fields = {"unsafe": True}
    context.models.response = "UNRELEASED DRAFT"


@given("the input judge reports an unrelated request")
def unrelated_request(context):
    context.models.input_fields = {"relevant": False}


@given("the output judge reports an unrelated draft")
def unrelated_draft(context):
    context.models.output_fields = {"in_scope": False}
    context.models.response = "UNRELEASED DRAFT"


@given("the input judge is uncertain about the supplied name")
def uncertain_name(context):
    context.models.input_fields = {"name_candidate": "Mina", "uncertain": True}


@when('the user says "{message}"')
def say(context, message):
    context.result = asyncio.run(
        context.bot.chat(
            context.user, context.session, message, language=getattr(context, "language", "en")
        )
    )


@given('the response language is "{language}"')
def response_language(context, language):
    context.language = language


@given("the model drafts a Persian drink answer with half-spaces")
def persian_draft(context):
    context.models.response = "درود، نوشیدنی‌ها را با مواد تازه آماده کنید."


@then('the reply contains "{text}"')
def includes_text(context, text):
    assert text in context.result.reply


@when("another user attempts to use the conversation")
def other_user(context):
    context.result = asyncio.run(
        context.bot.chat(
            Principal("tenant-a", "bob"),
            context.session,
            "Read this conversation",
        )
    )


@then('the response status is "{status}"')
def status(context, status):
    assert context.result.status == status


@then('the response reason is "{reason}"')
def reason(context, reason):
    assert context.result.reason == reason


@then('the reply does not contain "{text}"')
def no_text(context, text):
    assert text.casefold() not in context.result.reply.casefold()


@then("no model was called")
def no_model(context):
    assert not context.models.calls


@then("the response generator was not called")
def no_generation(context):
    assert "response" not in [name for name, _ in context.models.calls]


@then("all three model stages were called")
def three_models(context):
    assert [name for name, _ in context.models.calls] == ["input", "response", "output"]


@then("no conversation turn was stored")
def no_memory(context):
    assert not context.bot.store.owned(context.user, context.session).turns


@then("one conversation turn was stored")
def one_turn(context):
    assert len(context.bot.store.owned(context.user, context.session).turns) == 1


@when("an ordinary user attempts to publish shared context")
def ordinary_publish(context):
    try:
        asyncio.run(
            context.bot.publish_context(
                context.user,
                "Synthetic handbook",
                "handbook-v1",
                frozenset({"alice"}),
            )
        )
        context.publish_denied = False
    except AccessDenied:
        context.publish_denied = True


@then("publishing is denied")
def denied_publish(context):
    assert context.publish_denied


@given("a publisher shares a document with the original user")
def shared_document(context):
    asyncio.run(
        context.bot.publish_context(
            Principal("tenant-a", "editor", publisher=True),
            "Synthetic handbook",
            "handbook-v1",
            frozenset({"alice"}),
        )
    )


@then("the original user can read the shared document")
def original_reader(context):
    assert context.bot.store.bundle(context.user, context.session)["shared_documents"]


@then("another user cannot read the shared document")
def different_reader(context):
    user = Principal("tenant-a", "bob")
    session = context.bot.store.create(user)
    assert not context.bot.store.bundle(user, session)["shared_documents"]


@then("the same subject in another tenant cannot read the shared document")
def different_tenant(context):
    user = Principal("tenant-b", "alice")
    session = context.bot.store.create(user)
    assert not context.bot.store.bundle(user, session)["shared_documents"]


@given("a provider circuit with a failure threshold of two")
def circuit(context):
    context.clock = [0.0]
    context.circuit = CircuitBreaker(
        failure_threshold=2, cooldown=10, clock=lambda: context.clock[0]
    )
    context.calls = 0


async def failed_call(context):
    context.calls += 1
    raise RuntimeError("Synthetic provider failure")


@when("the provider fails twice")
def fail_twice(context):
    for _ in range(2):
        try:
            asyncio.run(context.circuit.call(lambda: failed_call(context)))
        except ProviderUnavailable:
            pass


@when("another call is attempted")
def another_call(context):
    try:
        asyncio.run(context.circuit.call(lambda: failed_call(context)))
    except ProviderUnavailable as error:
        assert str(error) == "circuit_open"


@then('the circuit is "{state}"')
def circuit_state(context, state):
    assert context.circuit.state == state


@then("exactly two provider calls were made")
def two_calls(context):
    assert context.calls == 2


@when("the cooldown expires")
def cooldown(context):
    context.clock[0] = 11


@when("the provider succeeds")
def healthy(context):
    async def operation():
        return "ok"

    assert asyncio.run(context.circuit.call(operation)) == "ok"


@given("a provider circuit with a short deadline")
def deadline(context):
    context.circuit = CircuitBreaker(timeout=0.01, failure_threshold=1)


@when("the provider exceeds the deadline")
def exceeded(context):
    try:
        asyncio.run(context.circuit.call(lambda: asyncio.sleep(10)))
    except ProviderUnavailable as error:
        assert str(error) == "timeout"


@then("no provider slot remains occupied")
def capacity(context):
    assert context.circuit.in_flight == 0
