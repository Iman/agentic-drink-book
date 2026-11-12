import argparse
import asyncio
import json
import subprocess
import sys

import pytest

from agentic_chat import evaluation
from agentic_chat.testing import ScriptedModels


@pytest.mark.parametrize("suite", ["regression", "holdout", "localization"])
def test_scripted_cli_reports_nonzero_cases_and_exits_successfully(suite, tmp_path):
    path = tmp_path / "result.json"
    result = subprocess.run(
        [sys.executable, "-m", "agentic_chat.evaluation", "--suite", suite, "--output", str(path)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    report = json.loads(path.read_text())
    assert report["mode"] == "scripted_offline"
    assert report["passed"] == report["total"] > 0
    assert report["failed"] == 0


@pytest.mark.parametrize(
    "args", [["--audit-model", "local-test"], ["--suite", "audit"], ["--suite", "audit", "--live"]]
)
def test_audit_cli_requires_explicit_live_model_selection(args):
    result = subprocess.run(
        [sys.executable, "-m", "agentic_chat.evaluation", *args], capture_output=True, text=True
    )
    assert result.returncode == 2
    assert "requires" in result.stderr


def test_audit_outage_sets_nonzero_exit_without_changing_chatbot_pass_count(monkeypatch, capsys):
    class Models(ScriptedModels):
        provider = "local"
        model_name = judge_name = audit_name = "test-model"
        structured_method = "json_schema"

        async def audit(self, payload):
            raise RuntimeError("synthetic outage")

        async def close(self):
            pass

    models = Models(response="Synthetic drink answer")
    monkeypatch.setattr(evaluation, "make_models", lambda args, policy: models)

    async def one_case(policy, cases, live_models, *, auditor):
        return await original(
            policy,
            [
                {
                    "id": "drink",
                    "message": "A drink question",
                    "attack": False,
                    "expected_status": "answered",
                    "expected_specialist": "mixing",
                }
            ],
            live_models,
            auditor=auditor,
        )

    original = evaluation.evaluate
    monkeypatch.setattr(evaluation, "evaluate", one_case)
    args = argparse.Namespace(
        policy=None, suite="regression", live=True, audit_model="test-model", output=None
    )
    assert asyncio.run(evaluation.run(args)) == 1
    report = json.loads(capsys.readouterr().out)
    assert report["passed"] == report["total"] == 1 and report["failed"] == 0
    assert report["audit"]["counts"]["unavailable"] == 1
    assert report["audit"]["same_as_generator"] and report["audit"]["same_as_judge"]
