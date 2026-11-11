"""Process-local context storage. Identity must come from the trusted host."""

import hashlib
import time
from dataclasses import dataclass, field
from uuid import uuid4

from agentic_chat.policy import Policy


class AccessDenied(Exception):
    pass


@dataclass(frozen=True)
class Principal:
    tenant: str
    subject: str
    publisher: bool = False

    def __post_init__(self):
        if not self.tenant or not self.subject:
            raise ValueError("Host identity is required")

    @property
    def owner(self) -> tuple[str, str]:
        return self.tenant, self.subject


@dataclass
class Session:
    owner: tuple[str, str]
    touched: float
    turns: list[dict[str, str]] = field(default_factory=list)
    name: str | None = None
    busy: bool = False


@dataclass(frozen=True)
class Document:
    tenant: str
    readers: frozenset[str]
    text: str
    source: str
    digest: str
    expires: float


class ContextStore:
    def __init__(self, policy: Policy, clock=time.monotonic):
        self.policy = policy
        self.clock = clock
        self._sessions: dict[str, Session] = {}
        self._documents: dict[str, Document] = {}
        self._requests: dict[tuple[str, str], list[float]] = {}

    def _expire(self):
        now = self.clock()
        self._sessions = {
            key: value
            for key, value in self._sessions.items()
            if value.busy or now - value.touched < self.policy.session_ttl_seconds
        }
        self._documents = {
            key: value for key, value in self._documents.items() if now < value.expires
        }
        self._requests = {
            owner: recent
            for owner, times in self._requests.items()
            if (recent := [t for t in times if now - t < 60])
        }

    def create(self, principal: Principal) -> str:
        self._expire()
        if len(self._sessions) >= self.policy.max_sessions:
            raise AccessDenied("session_capacity")
        session_id = uuid4().hex
        self._sessions[session_id] = Session(principal.owner, self.clock())
        return session_id

    def owned(self, principal: Principal, session_id: str) -> Session:
        self._expire()
        session = self._sessions.get(session_id)
        if session is None or session.owner != principal.owner:
            raise AccessDenied("context_access_denied")
        return session

    def admit(self, principal: Principal, session_id: str) -> Session:
        session = self.owned(principal, session_id)
        if session.busy:
            raise AccessDenied("session_busy")
        recent = self._requests.setdefault(principal.owner, [])
        if len(recent) >= self.policy.requests_per_minute:
            raise AccessDenied("rate_limited")
        recent.append(self.clock())
        session.touched = self.clock()
        session.busy = True
        return session

    def forget(self, principal: Principal, session_id: str):
        session = self.owned(principal, session_id)
        if session.busy:
            raise AccessDenied("session_busy")
        del self._sessions[session_id]

    def commit(
        self, principal: Principal, session_id: str, text: str, reply: str, name: str | None
    ):
        session = self.owned(principal, session_id)
        session.turns.append({"user": text, "assistant": reply})
        session.turns = session.turns[-self.policy.max_history_turns :]
        while (
            session.turns
            and sum(len(t["user"]) + len(t["assistant"]) for t in session.turns)
            > self.policy.max_context_chars
        ):
            session.turns.pop(0)
        if name is not None:
            session.name = name
        session.touched = self.clock()

    def publish(self, principal: Principal, text: str, source: str, readers: frozenset[str]) -> str:
        if not principal.publisher:
            raise AccessDenied("publish_access_denied")
        self._expire()
        if not readers or not source.strip() or len(source) > 200:
            raise ValueError("Explicit readers and bounded provenance are required")
        if len(self._documents) >= self.policy.max_documents:
            raise AccessDenied("document_capacity")
        key = uuid4().hex
        self._documents[key] = Document(
            principal.tenant,
            readers,
            text,
            source,
            hashlib.sha256(text.encode()).hexdigest(),
            self.clock() + self.policy.document_ttl_seconds,
        )
        return key

    def bundle(self, principal: Principal, session_id: str) -> dict:
        session = self.owned(principal, session_id)
        # Entire turns/documents are omitted when they do not fit; instructions are never truncated.
        remaining = self.policy.max_context_chars
        history = []
        for turn in reversed(session.turns):
            size = len(turn["user"]) + len(turn["assistant"])
            if size > remaining:
                break
            history.insert(0, dict(turn))
            remaining -= size
        documents = []
        for doc in self._documents.values():
            if doc.tenant != principal.tenant or principal.subject not in doc.readers:
                continue
            size = len(doc.text) + len(doc.source)
            if size <= remaining:
                documents.append({"text": doc.text, "source": doc.source, "sha256": doc.digest})
                remaining -= size
        return {"history": history, "shared_documents": documents, "display_name": session.name}
