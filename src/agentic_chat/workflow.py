"""An acyclic graph: no response or memory write before all mandatory gates pass."""

import asyncio
import time
from collections import deque
from dataclasses import asdict, dataclass
from typing import TypedDict
from uuid import uuid4

from langgraph.graph import END, START, StateGraph
from langgraph.runtime import Runtime
from langsmith import tracing_context

from agentic_chat.context import AccessDenied, ContextStore, Principal
from agentic_chat.localization import MESSAGES, Language, translate
from agentic_chat.policy import (
    InputEvidence,
    OutputEvidence,
    Policy,
    Specialist,
    input_decision,
    output_decision,
    screen,
)
from agentic_chat.providers import Models
from agentic_chat.resilience import ProviderUnavailable


@dataclass(frozen=True)
class TurnContext:
    principal: Principal
    session_id: str
    stages: list[str]
    language: Language = "en"


class TurnState(TypedDict, total=False):
    message: str
    reason: str | None
    evidence: InputEvidence
    context: dict
    candidate: str


@dataclass(frozen=True)
class Result:
    status: str
    reply: str
    reason: str
    request_id: str
    policy_version: str
    policy_digest: str
    elapsed_ms: float
    stages: tuple[str, ...]
    specialist: Specialist | None


class Chatbot:
    def __init__(
        self, models: Models, policy: Policy | None = None, store: ContextStore | None = None
    ):
        self.policy = policy or Policy.load()
        self.models = models
        self.store = store or ContextStore(self.policy)
        self.audit: deque[dict] = deque(maxlen=1000)
        self._active = 0
        graph = StateGraph(TurnState, context_schema=TurnContext)
        nodes = (
            ("input_rules", self._input_rules),
            ("load_context", self._load_context),
            ("input_judge", self._input_judge),
            ("mixing", self._mixing),
            ("production", self._production),
            ("output_rules", self._output_rules),
            ("output_judge", self._output_judge),
            ("commit", self._commit),
        )
        for name, handler in nodes:
            graph.add_node(name, handler)
        graph.add_edge(START, nodes[0][0])
        for name, next_name in (
            ("input_rules", "load_context"),
            ("load_context", "input_judge"),
            ("mixing", "output_rules"),
            ("production", "output_rules"),
            ("output_rules", "output_judge"),
            ("output_judge", "commit"),
        ):
            graph.add_conditional_edges(
                name,
                lambda state: "stop" if state.get("reason") else "next",
                {"stop": END, "next": next_name},
            )
        graph.add_conditional_edges(
            "input_judge",
            lambda state: "stop" if state.get("reason") else state["evidence"].specialist,
            {"stop": END, "mixing": "mixing", "production": "production"},
        )
        graph.add_edge("commit", END)
        # No checkpointer: raw inputs, drafts, and judge responses must not be persisted.
        self._graph = graph.compile()

    def _input_rules(self, state: TurnState, runtime: Runtime[TurnContext]):
        runtime.context.stages.append("input_rules")
        return {"reason": screen(state["message"], self.policy)}

    async def _input_judge(self, state: TurnState, runtime: Runtime[TurnContext]):
        runtime.context.stages.append("input_judge")
        evidence = InputEvidence.model_validate(
            await self.models.inspect_input(
                {
                    **state["context"],
                    "kind": "user_message",
                    "message": state["message"],
                }
            )
        )
        context = dict(state["context"])
        if evidence.name_candidate is not None:
            context["display_name"] = evidence.name_candidate
        reason = input_decision(evidence, state["message"], self.policy)
        if reason is None and evidence.specialist is None:
            raise ValueError("Missing specialist classification")
        return {
            "evidence": evidence,
            "context": context,
            "reason": reason,
        }

    def _load_context(self, state: TurnState, runtime: Runtime[TurnContext]):
        runtime.context.stages.append("load_context")
        context = self.store.bundle(runtime.context.principal, runtime.context.session_id)
        return {"context": context}

    async def _mixing(self, state: TurnState, runtime: Runtime[TurnContext]):
        return await self._generate(state, runtime, "mixing")

    async def _production(self, state: TurnState, runtime: Runtime[TurnContext]):
        return await self._generate(state, runtime, "production")

    async def _generate(
        self, state: TurnState, runtime: Runtime[TurnContext], specialist: Specialist
    ):
        runtime.context.stages.append(specialist)
        candidate = await self.models.respond(
            {
                **state["context"],
                "message": state["message"],
                "response_language": runtime.context.language,
            },
            specialist=specialist,
        )
        return {"candidate": candidate}

    def _output_rules(self, state: TurnState, runtime: Runtime[TurnContext]):
        runtime.context.stages.append("output_rules")
        reason = screen(state["candidate"], self.policy, output=True)
        return {"reason": reason}

    async def _output_judge(self, state: TurnState, runtime: Runtime[TurnContext]):
        runtime.context.stages.append("output_judge")
        evidence = OutputEvidence.model_validate(
            await self.models.inspect_output(
                {
                    **state["context"],
                    "message": state["message"],
                    "candidate": state["candidate"],
                    "response_language": runtime.context.language,
                }
            )
        )
        return {"reason": output_decision(evidence, self.policy)}

    def _commit(self, state: TurnState, runtime: Runtime[TurnContext]):
        runtime.context.stages.append("commit")
        self.store.commit(
            runtime.context.principal,
            runtime.context.session_id,
            state["message"],
            state["candidate"],
            state["evidence"].name_candidate,
        )
        return {}

    async def chat(
        self, principal: Principal, session_id: str, message: str, *, language: Language = "en"
    ) -> Result:
        if language not in MESSAGES:
            raise ValueError("Unsupported language")
        started = time.monotonic()
        session = None
        admitted = False
        state: TurnState = {"message": message, "reason": None}
        stages: list[str] = []
        reason = ""
        status = "answered"
        try:
            session = self.store.admit(principal, session_id)
            if self._active >= self.policy.max_in_flight:
                raise AccessDenied("service_busy")
            self._active += 1
            admitted = True
            # This also suppresses graph-level tracing enabled in the ambient environment.
            with tracing_context(enabled=False):
                async with asyncio.timeout(3 * self.policy.call_timeout_seconds + 1):
                    state = await self._graph.ainvoke(
                        state,
                        context=TurnContext(principal, session_id, stages, language),
                        config={"recursion_limit": 16},
                    )
            reason = state.get("reason") or "accepted"
            if reason != "accepted":
                status = (
                    "neutral"
                    if reason in {"unsuitable_name", "uncertain_name"}
                    and not {"mixing", "production"}.intersection(stages)
                    else "blocked"
                )
        except AccessDenied as error:
            reason, status = str(error), "denied"
        except ProviderUnavailable as error:
            reason, status = str(error), "unavailable"
        except TimeoutError:
            reason, status = "turn_timeout", "unavailable"
        except Exception:
            reason, status = "invalid_or_failed_processing", "unavailable"
        finally:
            if session:
                session.busy = False
            if admitted:
                self._active -= 1
        if status == "answered":
            reply = state["candidate"]
        elif status == "neutral":
            reply = translate("neutral", language)
        elif reason == "out_of_scope":
            reply = translate("out_of_scope", language)
        elif status in {"unavailable", "denied"}:
            reply = translate("unavailable", language)
        else:
            reply = translate("blocked", language)
        result = Result(
            status,
            reply,
            reason,
            uuid4().hex,
            self.policy.version,
            self.policy.digest,
            round((time.monotonic() - started) * 1000, 3),
            tuple(stages),
            next((name for name in ("mixing", "production") if name in stages), None),
        )
        event = asdict(result)
        del event["reply"]
        self.audit.append(event)
        return result

    async def publish_context(
        self,
        principal: Principal,
        text: str,
        source: str,
        readers: frozenset[str],
    ) -> str:
        if not principal.publisher:
            raise AccessDenied("publish_access_denied")
        reason = screen(text, self.policy) or screen(source, self.policy)
        if reason:
            raise AccessDenied(reason)
        evidence = InputEvidence.model_validate(
            await self.models.inspect_input(
                {
                    "kind": "shared_document",
                    "message": text,
                    "source": source,
                }
            )
        )
        reason = input_decision(evidence, text, self.policy)
        if reason:
            raise AccessDenied(reason)
        return self.store.publish(principal, text, source, readers)
