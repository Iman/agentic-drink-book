"""Independent expected outcomes; online judge scores are not the evaluation oracle."""

import argparse
import asyncio
import hashlib
import json
import math
from datetime import UTC, datetime
from importlib.resources import files
from pathlib import Path

from agentic_chat.auditing import audit_case, audit_digest
from agentic_chat.cli import arguments, make_models
from agentic_chat.context import Principal
from agentic_chat.policy import Policy
from agentic_chat.providers import prompt_digest
from agentic_chat.testing import ScriptedModels
from agentic_chat.workflow import Chatbot, Result


async def evaluate(policy, cases, live_models=None, *, auditor=None):
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
            and result.specialist == case.get("expected_specialist")
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
                "specialist": result.specialist,
                "expected_specialist": case.get("expected_specialist"),
            }
        )
        if auditor is not None:
            results[-1]["audit"] = await audit_case(auditor, policy, case, result)
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


async def evaluate_auditor(policy, cases, auditor):
    results = []
    for case in cases:
        observed = case["observed"]
        result = Result(
            status=observed["status"],
            reply=observed["reply"],
            reason=observed["reason"],
            request_id=case["id"],
            policy_version=policy.version,
            policy_digest=policy.digest,
            elapsed_ms=0.0,
            stages=tuple(observed["stages"]),
            specialist=observed["specialist"],
        )
        assessment = await audit_case(auditor, policy, case, result)
        categories = {finding["category"] for finding in assessment["findings"]}
        passed = (
            assessment["status"] != "unavailable"
            and categories == set(case["expected_categories"])
            and assessment["uncertain"] == case["expected_uncertain"]
        )
        results.append({"id": case["id"], "passed": passed, "audit": assessment})
    return {
        "mode": "live_audit_fixtures",
        "completed_at": datetime.now(UTC).isoformat(),
        "policy_version": policy.version,
        "policy_digest": policy.digest,
        "total": len(results),
        "passed": sum(r["passed"] for r in results),
        "failed": sum(not r["passed"] for r in results),
        "cases": results,
    }


async def run(args):
    policy = Policy.load(args.policy)
    dataset = {
        "regression": "eval_cases.json",
        "holdout": "eval_holdout.json",
        "localization": "eval_localization.json",
        "audit": "eval_audit.json",
    }[args.suite]
    raw = files("agentic_chat").joinpath(dataset).read_text(encoding="utf-8")
    cases = json.loads(raw)
    models = make_models(args, policy) if args.live else None
    try:
        if args.suite == "audit":
            report = await evaluate_auditor(policy, cases, models)
        else:
            report = await evaluate(
                policy, cases, models, auditor=models if args.audit_model else None
            )
    finally:
        if models:
            await models.close()
    report["dataset_sha256"] = hashlib.sha256(raw.encode()).hexdigest()
    report["suite"] = args.suite
    if args.audit_model:
        statuses = [case["audit"]["status"] for case in report["cases"]]
        report["audit"] = {
            "model": args.audit_model,
            "prompt_digest": audit_digest(),
            "same_as_generator": args.suite != "audit" and args.audit_model == models.model_name,
            "same_as_judge": args.suite != "audit" and args.audit_model == models.judge_name,
            "counts": {
                status: statuses.count(status)
                for status in ("clear", "review_required", "inconclusive", "unavailable")
            },
        }
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
    audit_attention = (
        args.audit_model
        and args.suite != "audit"
        and any(case["audit"]["status"] != "clear" for case in report["cases"])
    )
    return int(report["failed"] > 0 or bool(audit_attention))


def main():
    parser = argparse.ArgumentParser(description="Synthetic chatbot regression evaluations")
    arguments(parser)
    parser.add_argument(
        "--suite", choices=("regression", "holdout", "localization", "audit"), default="regression"
    )
    parser.add_argument(
        "--live", action="store_true", help="Use the selected provider; incurs model usage"
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument("--audit-model", help="Explicit post-run audit model; requires --live")
    args = parser.parse_args()
    if args.audit_model and not args.live:
        parser.error("--audit-model requires --live")
    if args.suite == "audit" and not (args.live and args.audit_model):
        parser.error("--suite audit requires --live and --audit-model")
    try:
        raise SystemExit(asyncio.run(run(args)))
    except KeyboardInterrupt:
        raise SystemExit(130) from None
    except Exception:
        parser.exit(2, "Evaluation setup failed; check provider and policy configuration.\n")


if __name__ == "__main__":
    main()
