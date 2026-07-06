import json
from pathlib import Path

import pytest

from judge import judge_parser

FIXTURE_DIR = Path(__file__).resolve().parent.parent / "data" / "fixtures"


def load_fixture(name: str) -> str:
    return (FIXTURE_DIR / name).read_text(encoding="utf-8")


@pytest.mark.parametrize(
    "filename",
    [
        "correctness_fixture_raw.txt",
        "correctness_fixture_fenced.txt",
        "correctness_fixture_preamble.txt",
    ],
)
def test_valid_family_parses_to_success_shape(filename: str) -> None:
    result = judge_parser(load_fixture(filename))
    assert "error" not in result
    assert result["verdict"] == 1
    assert type(result["verdict"]) is int
    assert isinstance(result["justification"], str)
    assert result["justification"]


def test_truncated_returns_failure_shape_with_raw_preserved() -> None:
    raw_input = load_fixture("correctness_fixture_truncated.txt")
    result = judge_parser(raw_input)
    assert "error" in result
    assert "raw" in result


@pytest.mark.parametrize(
    "bad_response",
    [
        '{"justification": "looks right", "verdict": "1"}',
        '{"justification": "looks right", "verdict": 2}',
        '{"justification": "looks right", "verdict": true}',
        '{"justification": "looks right"}',
        '{"verdict": 1}',
    ],
)
def test_contract_violations_return_failure_shape(bad_response: str) -> None:
    result = judge_parser(bad_response)
    assert "error" in result


def test_empty_string_returns_failure_shape() -> None:
    result = judge_parser("")
    assert "error" in result

def test_verdict_zero_is_valid() -> None:
    result = judge_parser('{"justification": "the answer is wrong", "verdict": 0}')
    assert "error" not in result
    assert result["verdict"] == 0