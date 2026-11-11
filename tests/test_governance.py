import asyncio
import json
import runpy
from importlib.resources import files
from pathlib import Path

import pytest

from agentic_chat.evaluation import evaluate
from agentic_chat.policy import Policy
from agentic_chat.resilience import CircuitBreaker, ProviderUnavailable


def test_committed_policy_matches_documented_defaults_and_rejects_unknown_fields():
    assert Policy.load() == Policy()
    with pytest.raises(ValueError):
        Policy.model_validate_json('{"unknown_permission": true}')
    assert Policy(version="1.0.1").digest != Policy().digest


@pytest.mark.parametrize(
    "dataset", ["eval_cases.json", "eval_holdout.json", "eval_localization.json"]
)
def test_offline_dataset_runs_nonzero_cases_against_independent_expectations(dataset):
    cases = json.loads(files("agentic_chat").joinpath(dataset).read_text())
    result = asyncio.run(evaluate(Policy(), cases))
    assert result["total"] == len(cases) > 0
    assert result["passed"] == result["total"]
    assert result["mode"] == "scripted_offline"
    assert result["unavailable_cases"] == 0


def test_commit_message_guard_allows_normal_subject_and_rejects_attribution():
    guard = runpy.run_path(str(Path(__file__).parents[1] / "scripts/check_commit_message.py"))
    assert guard["allowed"]("Add context ownership checks\n\nGuard every context access.\n")
    assert not guard["allowed"]("Add tests\n\n" + "Co-authored" + "-by: " + "Code" + "x\n")


def test_quota_failure_is_sanitized_and_counted_by_circuit():
    async def scenario():
        circuit = CircuitBreaker(failure_threshold=1)

        class FakeQuotaError(Exception):
            code = "credit_balance_exhausted"
            status_code = 429

        async def operation():
            raise FakeQuotaError("PRIVATE EXCEPTION CONTENT")

        with pytest.raises(ProviderUnavailable, match="^provider_quota_exhausted$"):
            await circuit.call(operation)
        assert circuit.state == "open"

    asyncio.run(scenario())
