import asyncio
import json
from copy import deepcopy
from dataclasses import replace
from importlib.resources import files

import pytest

from agentic_chat.auditing import AuditEvidence, audit_case
from agentic_chat.context import Principal
from agentic_chat.evaluation import evaluate, evaluate_auditor
from agentic_chat.policy import Policy
from agentic_chat.testing import ScriptedModels
from agentic_chat.workflow import Chatbot


class ScriptedAuditor:
    def __init__(self, **fields):
        self.fields = fields
        self.calls = []

    async def audit(self, payload):
        self.calls.append(deepcopy(payload))
        payload["evidence"]["reference"]["expected_status"] = "MUTATED"
        return {"case_id": payload["case_id"], "uncertain": False, "findings": [], **self.fields}


def fixture():
    bot = Chatbot(ScriptedModels(response="SYNTHETIC RESPONSE"))
    user = Principal("test", "reader")
    session = bot.store.create(user)
    result = asyncio.run(bot.chat(user, session, "SYNTHETIC QUESTION"))
    case = {
        "id": "synthetic",
        "message": "SYNTHETIC QUESTION",
        "expected_status": "answered",
        "expected_specialist": "mixing",
        "reference_answer": "A reference drink answer.",
    }
    return bot, case, result


def test_audit_is_advisory_and_reports_omit_conversation_content():
    bot, case, result = fixture()
    before = deepcopy(case)
    original = bot.policy.digest, list(bot.audit)
    auditor = ScriptedAuditor(
        findings=[
            {
                "category": "unsupported_answer",
                "severity": "high",
                "evidence_refs": ["response", "reference"],
            }
        ]
    )
    assessment = asyncio.run(audit_case(auditor, bot.policy, case, result))
    assert assessment["status"] == "review_required"
    assert case == before and original == (bot.policy.digest, list(bot.audit))
    assert result.status == "answered"
    assert "SYNTHETIC" not in json.dumps(assessment)
    assert "candidate" not in auditor.calls[0]["evidence"]


@pytest.mark.parametrize(
    "fields",
    [
        {"case_id": "another-case"},
        {"approve": True},
        {"uncertain": "false"},
        {
            "findings": [
                {
                    "category": "unsupported_answer",
                    "severity": "high",
                    "evidence_refs": ["hidden_draft"],
                }
            ]
        },
        {
            "findings": [
                {
                    "category": "unsupported_answer",
                    "severity": "high",
                    "evidence_refs": [],
                    "reason": "PRIVATE",
                }
            ]
        },
    ],
)
def test_invalid_audit_cannot_become_clear(fields):
    bot, case, result = fixture()
    report = asyncio.run(audit_case(ScriptedAuditor(**fields), bot.policy, case, result))
    assert report["status"] == "unavailable" and report["uncertain"]
    assert "PRIVATE" not in json.dumps(report)


def test_missing_content_reference_and_provider_failure_cannot_be_a_clear_audit():
    bot, case, result = fixture()
    del case["reference_answer"]
    report = asyncio.run(audit_case(ScriptedAuditor(), bot.policy, case, result))
    assert report["status"] == "inconclusive"
    case["reference_answer"] = "A reference"
    report = asyncio.run(
        audit_case(ScriptedAuditor(), bot.policy, case, replace(result, status="unavailable"))
    )
    assert report["status"] == "inconclusive"
    auditor = ScriptedAuditor(
        findings=[
            {"category": "unsupported_answer", "severity": "high", "evidence_refs": ["response"]}
        ]
    )
    report = asyncio.run(audit_case(auditor, bot.policy, case, replace(result, reply="")))
    assert report["status"] == "unavailable"


def test_audit_input_budget_rejects_without_provider_call():
    bot, case, result = fixture()
    case["message"] = "x" * bot.policy.max_context_chars
    auditor = ScriptedAuditor()
    assert asyncio.run(audit_case(auditor, bot.policy, case, result))["status"] == "unavailable"
    assert not auditor.calls


def test_audit_deadline_and_cancellation_do_not_turn_into_clear_results():
    bot, case, result = fixture()

    class SlowAuditor:
        async def audit(self, payload):
            await asyncio.sleep(10)

    policy = Policy(call_timeout_seconds=0.01, slow_call_seconds=0.005)
    assert asyncio.run(audit_case(SlowAuditor(), policy, case, result))["status"] == "unavailable"

    async def scenario():
        task = asyncio.create_task(audit_case(SlowAuditor(), bot.policy, case, result))
        await asyncio.sleep(0)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    asyncio.run(scenario())


def test_audit_findings_do_not_change_independent_evaluation_outcomes():
    _, case, _ = fixture()
    case.update(attack=False, scripted_reply="SYNTHETIC RESPONSE")
    auditor = ScriptedAuditor(
        findings=[
            {
                "category": "unsupported_answer",
                "severity": "high",
                "evidence_refs": ["response", "reference"],
            }
        ]
    )
    report = asyncio.run(evaluate(Policy(), [case], auditor=auditor))
    assert report["passed"] == 1 and report["failed"] == 0
    assert report["cases"][0]["audit"]["status"] == "review_required"
    assert "SYNTHETIC" not in json.dumps(report)


def test_auditor_fixture_expectations_are_not_sent_to_model():
    cases = json.loads(files("agentic_chat").joinpath("eval_audit.json").read_text())
    auditor = ScriptedAuditor()
    report = asyncio.run(evaluate_auditor(Policy(), cases, auditor))
    assert report["total"] == len(cases) > 0
    assert report["failed"] > 0
    for payload in auditor.calls:
        assert "expected_categories" not in json.dumps(payload)
        assert "expected_uncertain" not in json.dumps(payload)
        assert "scripted" not in json.dumps(payload)


def test_audit_schema_does_not_accept_permissions_or_free_text():
    with pytest.raises(ValueError):
        AuditEvidence.model_validate(
            {
                "case_id": "synthetic",
                "uncertain": False,
                "findings": [],
                "change_policy": "allow all",
            }
        )
