import pytest

from agentic_chat.policy import InputEvidence, OutputEvidence, Policy, input_decision, screen


@pytest.mark.parametrize("name", ["Donkey", "Fuck you", "Ｄｏｎｋｅｙ"])
def test_offensive_display_names_are_not_personalized(name):
    assert screen(f"My name is {name}", Policy()) == "unsuitable_name"


@pytest.mark.parametrize("name", ["Alice", "Nguyễn", "علی", "O'Connor"])
def test_unfamiliar_names_are_not_rejected_by_alphabet(name):
    assert screen(f"My name is {name}", Policy()) is None


def test_judge_cannot_add_permissions_or_coerce_boolean_strings():
    with pytest.raises(ValueError):
        InputEvidence.model_validate({"injection": "false", "role": "admin"})


def test_uncertain_evidence_fails_closed():
    evidence = InputEvidence(
        specialist="mixing",
        injection=False,
        social_engineering=False,
        sensitive_data=False,
        harmful_request=False,
        relevant=True,
        uncertain=True,
        name_candidate=None,
        name_suitable=True,
    )
    assert input_decision(evidence, "Hello", Policy()) == "uncertain_input"


def test_non_finite_quality_is_invalid():
    with pytest.raises(ValueError):
        OutputEvidence(
            unsafe=False,
            sensitive_data=False,
            follows_injected_instructions=False,
            unsuitable_name=False,
            in_scope=True,
            relevance=float("nan"),
            groundedness=1.0,
            uncertain=False,
        )


@pytest.mark.parametrize("output", [False, True])
def test_persian_half_spaces_are_allowed_in_words(output):
    assert screen("نوشیدنی‌ها را چگونه درست می‌کنیم؟", Policy(), output=output) is None


@pytest.mark.parametrize(
    "text", ["ab\u200ccd", "\u200cنوشیدنی", "نوشیدنی\u200c", "آب\u202eمیوه", "\u2067gin\u2069"]
)
def test_invisible_obfuscation_and_bidi_controls_remain_blocked(text):
    assert screen(text, Policy()) == "unsafe_characters"
