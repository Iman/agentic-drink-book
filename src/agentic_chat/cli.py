"""Local terminal entry point. The OS session is the authentication boundary."""

import argparse
import asyncio
import json
from dataclasses import asdict
from pathlib import Path

from agentic_chat.context import Principal
from agentic_chat.policy import Policy
from agentic_chat.providers import LangChainModels
from agentic_chat.workflow import Chatbot


def arguments(parser: argparse.ArgumentParser):
    parser.add_argument("--provider", choices=("openai", "local"), default="openai")
    parser.add_argument("--model", default="gpt-4.1-mini")
    parser.add_argument("--judge-model")
    parser.add_argument("--base-url", help="Explicit loopback endpoint for local mode")
    parser.add_argument(
        "--structured-method", choices=("json_schema", "json_mode"), default="json_schema"
    )
    parser.add_argument("--policy", type=Path)


def make_models(args, policy):
    return LangChainModels(
        policy,
        provider=args.provider,
        model=args.model,
        judge_model=args.judge_model,
        base_url=args.base_url,
        structured_method=args.structured_method,
    )


async def run(args):
    policy = Policy.load(args.policy)
    models = make_models(args, policy)
    bot = Chatbot(models, policy)
    principal = Principal("local", "operator", publisher=True)
    session = bot.store.create(principal)
    try:
        if args.context_file:
            with args.context_file.open(encoding="utf-8") as handle:
                text = handle.read(policy.max_input_chars + 1)
            await bot.publish_context(
                principal, text, "operator-supplied-document", frozenset({principal.subject})
            )
        if args.message is not None:
            result = await bot.chat(principal, session, args.message, language=args.language)
            print(json.dumps(asdict(result), ensure_ascii=False) if args.json else result.reply)
            return 0 if result.status in {"answered", "neutral"} else 1
        print("Chat ready. /reset clears this conversation; /quit exits.")
        while True:
            try:
                text = input("You: ")
            except EOFError:
                break
            if text.strip() == "/quit":
                break
            if text.strip() == "/reset":
                bot.store.forget(principal, session)
                session = bot.store.create(principal)
                print("Conversation cleared.")
                continue
            result = await bot.chat(principal, session, text, language=args.language)
            print(result.reply)
        return 0
    finally:
        await models.close()


def main():
    parser = argparse.ArgumentParser(description="Policy-gated LangGraph chatbot")
    arguments(parser)
    parser.add_argument("--language", choices=("en", "fa"), default="en", help="Reply language")
    parser.add_argument("--message", help="Send one message and exit")
    parser.add_argument("--json", action="store_true", help="Return result metadata with the reply")
    parser.add_argument(
        "--context-file", type=Path, help="Screen and share one local text document"
    )
    args = parser.parse_args()
    try:
        raise SystemExit(asyncio.run(run(args)))
    except KeyboardInterrupt:
        raise SystemExit(130) from None
    except Exception:
        parser.exit(
            2,
            "Startup or context ingestion failed. "
            "Check provider, credentials, policy, and input file.\n",
        )


if __name__ == "__main__":
    main()
