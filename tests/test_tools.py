"""Unit tests for the data tools. Run: python -m pytest tests  (or: python tests/test_tools.py)"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from build import check_row  # noqa: E402
from common import ADVISORY_ID, normalise, render, row_id  # noqa: E402

SOURCES = {
    "GHSA-8Q59-Q68H-6HV4": {"id": "GHSA-8q59-q68h-6hv4", "split": "public", "withdrawn": None},
    "CVE-2020-14343": {"id": "GHSA-8q59-q68h-6hv4", "split": "public", "withdrawn": None},
    "CVE-2022-23529": {"id": "GHSA-27h2-hvpr-p74q", "split": "public", "withdrawn": "2023-01-27"},
}
BASE = dict(case="c", family="F2", split="public", source_url="https://example.org/a",
            verdict_chosen="Secure", verdict_rejected="Insecure", format="prose",
            flaw_note="n", author="t", prompt="Review pyyaml==5.4.1 for CVE-2020-14343 please.",
            chosen="Not affected: CVE-2020-14343 is fixed in 5.4, so 5.4.1 is outside the range." * 2,
            rejected="Affected: CVE-2020-14343 applies to every 5.x release including 5.4.1." * 2)


def run(**over):
    r = {**BASE, **over}
    errors, warns = [], []
    check_row(r, "t", SOURCES, errors, warns)
    return errors, warns


def test_normalise_matches_node():
    assert normalise("á  b\n\tc ") == "á b c"


def test_row_id_is_normalisation_invariant():
    assert row_id("p  q", "c", "r") == row_id("p q", "c", "r")


def test_render_is_kit_template():
    assert render("Q", "A") == "### Task:\nQ\n\n### Answer:\nA"


def test_advisory_regex():
    found = ADVISORY_ID.findall("see CVE-2021-44228 and GHSA-jfh8-c2jp-5v3q, not CWE-79")
    assert found == ["CVE-2021-44228", "GHSA-jfh8-c2jp-5v3q"]


def test_clean_row_passes():
    errors, _ = run()
    assert errors == []


def test_unknown_id_in_chosen_is_error():
    errors, _ = run(chosen=BASE["chosen"] + " Also CVE-2099-0001.")
    assert any("CVE-2099-0001" in e for e in errors)


def test_declared_fabrication_allowed_only_in_rejected():
    ok, _ = run(family="F1", fabricated_ids=["CVE-2099-0001"], rejected=BASE["rejected"] + " CVE-2099-0001.")
    assert ok == []
    bad, _ = run(family="F1", fabricated_ids=["CVE-2099-0001"], chosen=BASE["chosen"] + " CVE-2099-0001.")
    assert any("appears in chosen" in e for e in bad)


def test_misattributed_id_allowed_only_in_rejected():
    ok, _ = run(family="F1", misattributed_ids=["CVE-2020-28471"], rejected=BASE["rejected"] + " CVE-2020-28471.")
    assert ok == []
    bad, _ = run(family="F1", misattributed_ids=["CVE-2020-28471"], chosen=BASE["chosen"] + " CVE-2020-28471.")
    assert any("appears in chosen" in e for e in bad)


def test_fabricated_id_must_not_be_real():
    errors, _ = run(family="F1", fabricated_ids=["CVE-2020-14343"])
    assert any("real advisory" in e for e in errors)


def test_withdrawn_in_chosen_needs_disclosure():
    bad, _ = run(chosen=BASE["chosen"] + " See CVE-2022-23529.")
    assert any("withdrawn" in e for e in bad)
    ok, _ = run(chosen=BASE["chosen"] + " CVE-2022-23529 was withdrawn.")
    assert ok == []


def test_bad_enums_and_identical_answers():
    errors, _ = run(family="F11", verdict_chosen="Safe", rejected=BASE["chosen"])
    assert any("family" in e for e in errors)
    assert any("verdict_chosen" in e for e in errors)
    assert any("chosen == rejected" in e for e in errors)


if __name__ == "__main__":
    fns = [v for k, v in dict(globals()).items() if k.startswith("test_")]
    for f in fns:
        f()
    print(f"{len(fns)} tests passed")
