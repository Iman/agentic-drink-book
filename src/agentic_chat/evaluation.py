"""Independent expected outcomes; online judge scores are not the evaluation oracle."""

import argparse
import asyncio
import hashlib
import json
import math
from datetime import UTC, datetime
from importlib.resources import files
from pathlib import Path

from agentic_chat.cli import arguments, make_models
from agentic_chat.context import Principal
from agentic_chat.policy import Policy
from agentic_chat.providers import prompt_digest
from agentic_chat.testing import ScriptedModels
from agentic_chat.workflow import Chatbot


async def evaluate(policy, cases, live_models=None):
    results = []
    for case in cases:
        models = live_models or ScriptedModels(
            input_fields=case.get("scripted_input", {}),
            response=case.get("scripted_reply", "Hello."),
        )
        bot = Chatbot(models, policy)
        principal = Principal("evaluation", "synthetic-user")
        session = bot.store.create(principal)
        language = case.get("language", "en")
        result = await bot.chat(principal, session, case["message"], language=language)
        text = result.reply.casefold()
        passed = (
            result.status == case["expected_status"]
            and all(s.casefold() not in text for s in case.get("forbidden", []))
            and all(s.casefold() in text for s in case.get("required", []))
        )
        results.append(
            {
                "id": case["id"],
                "passed": passed,
                "expected_status": case["expected_status"],
                "observed_status": result.status,
                "reason": result.reason,
                "elapsed_ms": result.elapsed_ms,
                "attack": case["attack"],
                "language": language,
            }
        )
    latencies = sorted(r["elapsed_ms"] for r in results)
    attacks = [r for r in results if r["attack"]]
    benign = [r for r in results if not r["attack"]]
    expected_answers = [r for r in results if r["expected_status"] == "answered"]
    expected_refusals = [r for r in results if r["expected_status"] == "blocked"]
    return {
        "mode": "live" if live_models else "scripted_offline",
        "completed_at": datetime.now(UTC).isoformat(),
        "policy_version": policy.version,
        "policy_digest": policy.digest,
        "prompt_digest": prompt_digest(),
        "total": len(results),
        "passed": sum(r["passed"] for r in results),
        "failed": sum(not r["passed"] for r in results),
        "attack_cases": len(attacks),
        "attack_cases_answered": sum(r["observed_status"] == "answered" for r in attacks),
        "benign_cases": len(benign),
        "benign_cases_blocked": sum(r["observed_status"] == "blocked" for r in benign),
        "benign_cases_not_answered": sum(r["observed_status"] != "answered" for r in benign),
        "expected_answer_cases_not_answered": sum(
            r["observed_status"] != "answered" for r in expected_answers
        ),
        "expected_refusal_cases_answered": sum(
            r["observed_status"] == "answered" for r in expected_refusals
        ),
        "unavailable_cases": sum(r["observed_status"] == "unavailable" for r in results),
        "latency_p50_ms": latencies[math.ceil(len(latencies) * 0.50) - 1],
        "latency_p95_ms": latencies[math.ceil(len(latencies) * 0.95) - 1],
        "cases": results,
    }


async def run(args):
    policy = Policy.load(args.policy)
    dataset = {
        "regression": "eval_cases.json",
        "holdout": "eval_holdout.json",
        "localization": "eval_localization.json",
    }[args.suite]
    raw = files("agentic_chat").joinpath(dataset).read_text(encoding="utf-8")
    cases = json.loads(raw)
    models = make_models(args, policy) if args.live else None
    try:
        report = await evaluate(policy, cases, models)
    finally:
        if models:
            await models.close()
    report["dataset_sha256"] = hashlib.sha256(raw.encode()).hexdigest()
    report["suite"] = args.suite
    if models:
        report.update(
            provider=models.provider,
            model=models.model_name,
            judge_model=models.judge_name,
            structured_method=models.structured_method,
        )
    output = json.dumps(report, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output + "\n", encoding="utf-8")
    print(output)
    return int(report["failed"] > 0)


def main():
    parser = argparse.ArgumentParser(description="Synthetic chatbot regression evaluations")
    arguments(parser)
    parser.add_argument(
        "--suite", choices=("regression", "holdout", "localization"), default="regression"
    )
    parser.add_argument(
        "--live", action="store_true", help="Use the selected provider; incurs model usage"
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        raise SystemExit(asyncio.run(run(args)))
    except KeyboardInterrupt:
        raise SystemExit(130) from None
    except Exception:
        parser.exit(2, "Evaluation setup failed; check provider and policy configuration.\n")


if __name__ == "__main__":
    main()
