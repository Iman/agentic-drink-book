"""Loopback web host: server-owned identity, bounded bodies and buffered replies."""

import argparse
import secrets
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import Field, ValidationError
from starlette.middleware.trustedhost import TrustedHostMiddleware

from agentic_chat.cli import arguments, make_models
from agentic_chat.context import AccessDenied, Principal
from agentic_chat.localization import MESSAGES, translate
from agentic_chat.policy import Policy, StrictModel
from agentic_chat.workflow import Chatbot

COOKIE = "drinks_session"
MAX_BODY_BYTES = 32768
ORIGINS = {f"http://{host}:{port}" for host in ("127.0.0.1", "localhost") for port in (8000, 5173)}


class ChatRequest(StrictModel):
    message: str = Field(min_length=1, max_length=16000)


@dataclass
class BrowserSession:
    principal: Principal
    conversation: str
    csrf: str


def create_app(bot: Chatbot, *, frontend: Path | None = None, close_models: bool = False):
    # shortcut: process-local browser sessions; use authenticated shared storage before scaling.
    browsers: dict[str, BrowserSession] = {}

    @asynccontextmanager
    async def lifespan(app):
        try:
            yield
        finally:
            if close_models:
                await bot.models.close()

    app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost"])

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, error: HTTPException):
        return JSONResponse(
            {"detail": translate(error.detail, request.state.language), "code": error.detail},
            status_code=error.status_code,
        )

    @app.middleware("http")
    async def boundary(request: Request, call_next):
        language = request.headers.get("x-chat-language", "en")
        request.state.language = language if language in MESSAGES else "en"
        if request.method == "POST" and request.headers.get("origin") not in ORIGINS:
            response = await http_error(request, HTTPException(403, "origin_denied"))
        elif language not in MESSAGES:
            response = await http_error(request, HTTPException(422, "invalid_language"))
        else:
            response = await call_next(request)
        response.headers.update(
            {
                "Cache-Control": "no-store",
                "X-Content-Type-Options": "nosniff",
                "Referrer-Policy": "no-referrer",
                "Content-Security-Policy": "default-src 'self'; script-src 'self'; "
                "style-src 'self'; img-src 'self' data:; font-src 'self'; "
                "connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'",
            }
        )
        return response

    def current(request: Request, *, csrf: bool = True) -> BrowserSession:
        session = browsers.get(request.cookies.get(COOKIE, ""))
        if session is None:
            raise HTTPException(401, "session_expired")
        try:
            bot.store.owned(session.principal, session.conversation)
        except AccessDenied:
            raise HTTPException(401, "session_expired") from None
        if csrf and not secrets.compare_digest(
            request.headers.get("x-csrf-token", "").encode(), session.csrf.encode()
        ):
            raise HTTPException(403, "verification_failed")
        return session

    def session_data(session: BrowserSession):
        return {
            "csrf": session.csrf,
            "history": bot.store.bundle(session.principal, session.conversation)["history"],
            "max_input_chars": bot.policy.max_input_chars,
        }

    @app.get("/api/health")
    async def health():
        return {"status": "ok"}

    @app.post("/api/session")
    async def initialize(request: Request):
        try:
            return session_data(current(request, csrf=False))
        except HTTPException:
            pass
        for token, session in list(browsers.items()):
            try:
                bot.store.owned(session.principal, session.conversation)
            except AccessDenied:
                del browsers[token]
        principal = Principal("local-web", secrets.token_hex(24))
        try:
            conversation = bot.store.create(principal)
        except AccessDenied:
            raise HTTPException(503, "session_capacity") from None
        token = secrets.token_urlsafe(32)
        session = BrowserSession(principal, conversation, secrets.token_urlsafe(32))
        browsers[token] = session
        response = JSONResponse(session_data(session))
        # HTTP is restricted to loopback. Require Secure cookies and TLS for a public host.
        response.set_cookie(
            COOKIE,
            token,
            httponly=True,
            samesite="strict",
            max_age=int(bot.policy.session_ttl_seconds),
            path="/api",
        )
        return response

    @app.post("/api/reset")
    async def reset(request: Request):
        session = current(request)
        try:
            bot.store.forget(session.principal, session.conversation)
            session.conversation = bot.store.create(session.principal)
        except AccessDenied:
            raise HTTPException(409, "session_busy") from None
        session.csrf = secrets.token_urlsafe(32)
        return session_data(session)

    @app.post("/api/chat")
    async def chat(request: Request):
        session = current(request)
        if request.headers.get("content-type", "").split(";")[0] != "application/json":
            raise HTTPException(415, "json_required")
        body = bytearray()
        async for chunk in request.stream():
            if len(body) + len(chunk) > MAX_BODY_BYTES:
                raise HTTPException(413, "body_too_large")
            body.extend(chunk)
        try:
            payload = ChatRequest.model_validate_json(bytes(body))
        except ValidationError:
            raise HTTPException(422, "invalid_message") from None
        if not payload.message.strip() or len(payload.message) > bot.policy.max_input_chars:
            raise HTTPException(422, "invalid_message")
        result = await bot.chat(
            session.principal,
            session.conversation,
            payload.message,
            language=request.state.language,
        )
        status = 200
        if result.status == "unavailable":
            status = 503
        elif result.status == "denied":
            status = (
                429 if result.reason in {"rate_limited", "service_busy", "session_busy"} else 401
            )
        content = {"reply": result.reply, "status": result.status, "request_id": result.request_id}
        if status >= 400:
            content["code"] = {401: "session_expired", 429: "busy", 503: "unavailable"}[status]
        return JSONResponse(content, status_code=status)

    if frontend and (frontend / "index.html").is_file():
        app.mount("/", StaticFiles(directory=frontend, html=True), name="frontend")
    return app


def main():
    parser = argparse.ArgumentParser(description="Local drinks chatbot web server")
    arguments(parser)
    parser.set_defaults(provider="local", model=None)
    args = parser.parse_args()
    if args.provider == "local":
        args.model = args.model or "gemma3:4b"
        args.base_url = args.base_url or "http://127.0.0.1:11434/v1"
    else:
        args.model = args.model or "gpt-4.1-mini"
    frontend = Path.cwd() / "frontend" / "dist"
    if not (frontend / "index.html").is_file():
        parser.exit(2, "Build the interface first: npm --prefix frontend run build\n")
    policy = Policy.load(args.policy)
    app = create_app(
        Chatbot(make_models(args, policy), policy), frontend=frontend, close_models=True
    )
    uvicorn.run(app, host="127.0.0.1", port=8000, access_log=False, use_colors=False)


if __name__ == "__main__":
    main()
