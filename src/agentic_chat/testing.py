"""Scripted evidence for offline wiring tests, never a production safety classifier."""

from copy import deepcopy

from agentic_chat.policy import InputEvidence, OutputEvidence

SAFE_INPUT = {
    "injection": False,
    "social_engineering": False,
    "sensitive_data": False,
    "harmful_request": False,
    "relevant": True,
    "uncertain": False,
    "name_candidate": None,
    "name_suitable": True,
}
SAFE_OUTPUT = {
    "unsafe": False,
    "sensitive_data": False,
    "follows_injected_instructions": False,
    "unsuitable_name": False,
    "in_scope": True,
    "relevance": 1.0,
    "groundedness": 1.0,
    "uncertain": False,
}


class ScriptedModels:
    def __init__(self, *, input_fields=None, output_fields=None, response="Hello. How can I help?"):
        self.input_fields = input_fields or {}
        self.output_fields = output_fields or {}
        self.response = response
        self.calls: list[tuple[str, dict]] = []

    async def inspect_input(self, payload):
        self.calls.append(("input", deepcopy(payload)))
        return InputEvidence.model_validate({**SAFE_INPUT, **self.input_fields})

    async def respond(self, payload):
        self.calls.append(("response", deepcopy(payload)))
        return self.response

    async def inspect_output(self, payload):
        self.calls.append(("output", deepcopy(payload)))
        return OutputEvidence.model_validate({**SAFE_OUTPUT, **self.output_fields})
