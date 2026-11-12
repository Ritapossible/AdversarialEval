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


def test_osv_id_canonicalisation():
    from check_ids import canonical
    assert canonical("GHSA-VX6W-VV9F-6GVG") == "GHSA-vx6w-vv9f-6gvg"
    assert canonical("cve-2020-28471") == "CVE-2020-28471"


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


def test_merge_seeds_is_exact_at_rank_16(tmp_path):
    import json

    import torch
    from safetensors.torch import load_file, save_file
    from merge_seeds import merge

    pref = "base_model.model.model.layers.0.attn.Wo.lora_"
    dirs, dws = [], []
    for s in (1, 2):
        g = torch.Generator().manual_seed(s)
        A, B = torch.randn(8, 12, generator=g), torch.randn(10, 8, generator=g)
        d = tmp_path / f"s{s}"
        d.mkdir()
        save_file({pref + "A.weight": A, pref + "B.weight": B,
                   "base_model.model.classifier.weight": torch.full((1, 12), float(s)),
                   "base_model.model.classifier.bias": torch.zeros(1)}, str(d / "adapter_model.safetensors"))
        (d / "adapter_config.json").write_text(json.dumps(
            {"r": 8, "lora_alpha": 32, "target_modules": ["Wo"], "base_model_name_or_path": "x", "task_type": "SEQ_CLS"}))
        dirs.append(d)
        dws.append(4 * B @ A)
    out = tmp_path / "m"
    merge(dirs, out, "mean", 16)
    m = load_file(str(out / "adapter_model.safetensors"))
    assert torch.allclose(2 * m[pref + "B.weight"] @ m[pref + "A.weight"], (dws[0] + dws[1]) / 2, atol=1e-4)
    assert torch.allclose(m["base_model.model.classifier.weight"], torch.full((1, 12), 1.5))
    assert json.loads((out / "adapter_config.json").read_text())["r"] == 16


def test_review_pool_round_trip(tmp_path):
    import csv
    import json

    import review_pool as rp

    auth = tmp_path / "authoring" / "security_review"
    auth.mkdir(parents=True)
    rows = [{"prompt": f"Is pkg{i} 1.0 affected?", "chosen": "yes", "rejected": "no", "family": "F2",
             "source_url": "https://github.com/advisories/GHSA-xxxx-xxxx-xxxx", "reviewed": False} for i in range(3)]
    (auth / "g.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    rp.AUTHORING, rp.REVIEW = tmp_path / "authoring", tmp_path / "review"
    rp.SHEET, rp.REJECTED = rp.REVIEW / "pool_review.csv", rp.REVIEW / "rejected.jsonl"
    rp.ROOT = tmp_path
    rp.main(["export"])
    sheet = list(csv.DictReader(rp.SHEET.open()))
    sheet[0]["decision"], sheet[1]["decision"] = "approve", "reject"
    with rp.SHEET.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=rp.COLUMNS)
        w.writeheader()
        w.writerows(sheet)
    rp.main(["apply", "--reviewer", "Test Reviewer"])
    kept = [json.loads(x) for x in (auth / "g.jsonl").read_text().splitlines()]
    assert [r["reviewed"] for r in kept] == [True, False]
    assert kept[0]["review"]["by"] == "Test Reviewer"
    assert len(rp.REJECTED.read_text().splitlines()) == 1


def _osv(name, eco, *ranges, other=None):
    """A minimal OSV record: each range is a list of events."""
    aff = [{"package": {"name": name, "ecosystem": eco},
            "ranges": [{"type": "ECOSYSTEM", "events": ev} for ev in ranges]}]
    if other:
        aff.append({"package": {"name": other, "ecosystem": eco},
                    "ranges": [{"type": "ECOSYSTEM", "events": [{"introduced": "0"}, {"fixed": "99.0"}]}]})
    return {"affected": aff}


def test_osv_range_logic_edge_cases():
    from gen_osv_pairs import make_affected, ranges_for

    # introduced "0": everything below the fix
    rec = _osv("lodash", "npm", [{"introduced": "0"}, {"fixed": "4.17.21"}], other="underscore")
    affected, range_of = make_affected("npm", ranges_for(rec, "npm", "lodash"))
    assert affected("4.17.20") and not affected("4.17.21") and not affected("5.0.0")
    assert range_of("4.17.20")["fixed"] == "4.17.21"
    # backport: two ranges on two release lines; the gap between them is not affected
    rec = _osv("django", "PyPI", [{"introduced": "3.2"}, {"fixed": "3.2.19"}],
               [{"introduced": "4.0"}, {"fixed": "4.1.9"}])
    affected, range_of = make_affected("PyPI", ranges_for(rec, "PyPI", "django"))
    assert affected("3.2.18") and not affected("3.2.19") and not affected("3.3")
    assert affected("4.1.8") and not affected("4.1.9") and not affected("3.1")
    assert range_of("4.1.8")["introduced"] == "4.0"
    # PEP 440 ordering between stable releases (2.2.10 > 2.2.9); pre-releases are out of
    # contract: the registry list drops them, affected() refuses them, and an advisory whose
    # fix is only a pre-release is skipped
    rec = _osv("flask", "PyPI", [{"introduced": "0"}, {"fixed": "2.3.0"}])
    affected, _ = make_affected("PyPI", ranges_for(rec, "PyPI", "flask"))
    assert affected("2.2.10") and affected("2.2.9") and not affected("2.3.0")
    try:
        affected("2.3.0rc1")
        raise AssertionError("a pre-release must be refused")
    except ValueError:
        pass
    pre_fix = _osv("flask", "PyPI", [{"introduced": "0"}, {"fixed": "3.0.0rc1"}])
    assert make_affected("PyPI", ranges_for(pre_fix, "PyPI", "flask")) is None
    # names match case-insensitively; another package in the same record is ignored
    assert ranges_for(_osv("PyYAML", "PyPI", [{"introduced": "0"}, {"fixed": "5.4"}]), "PyPI", "pyyaml")
    assert ranges_for(rec, "PyPI", "werkzeug") is None
    # skipped on purpose: last_affected, open-ended (unfixed) ranges
    assert ranges_for(_osv("x", "npm", [{"introduced": "1.0.0"}, {"last_affected": "1.2.0"}]), "npm", "x") is None
    assert ranges_for(_osv("x", "npm", [{"introduced": "1.0.0"}]), "npm", "x") is None
