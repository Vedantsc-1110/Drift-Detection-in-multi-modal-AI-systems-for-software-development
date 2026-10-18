"""Task 4.7 tests: severity scoring (PART4_PLAN Task 4.7, §7.3 Step 6).

Agent A → exactly 0.725; Agent B → 0.0; Agent C → exactly 0.82 with the
documented inputs. Unknown factor values raise. No network.
"""

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from contextgraph.drift.severity import WEIGHTS, score, verdict  # noqa: E402


def test_weights_match_contract_section_7():
    assert WEIGHTS == {"criticality": 0.15, "breakage": 0.35, "directness": 0.20,
                       "assumption": 0.10, "constraint": 0.10, "conflicting": 0.10}


def test_agent_a_exactly_0725():
    result = score(criticality="normal", breakage="signature", directness=1,
                   assumption=True, constraint=False, conflicting=False)
    assert result["score"] == 0.725
    assert result["factors"] == {"criticality": 0.5, "breakage": 1.0, "directness": 1.0,
                                 "assumption": 1.0, "constraint": 0.0, "conflicting": 0.0}


def test_agent_b_zero():
    # No diffs: the agent is never scored (factor math has no zero level —
    # the §7 floor is low=0.2 — so 0.0 is the empty-diff rule, not a sum).
    result = verdict(False)
    assert result["score"] == 0.0 and result["rule"] == "empty-diff"


def test_agent_c_exactly_082():
    result = score(criticality="high", breakage="signature", directness=3,
                   assumption=True, constraint=True, conflicting=True)
    assert result["score"] == 0.82


def test_unknown_values_raise():
    with pytest.raises(ValueError):
        score(criticality="extreme")
    with pytest.raises(ValueError):
        score(breakage="vibes")
    with pytest.raises(ValueError):
        score(directness="far")
