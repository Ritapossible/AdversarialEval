import pytest
from solution import count_lines


def test_spaces_in_name(tmp_path):
    p = tmp_path / "my file.txt"
    p.write_text("a\nb\n")
    assert count_lines(str(p)) == 2


@pytest.mark.parametrize("tmpl", ["{d}/x.txt; touch {m}", "{d}/x.txt && touch {m}", "$(touch {m})", "`touch {m}`"])
def test_no_command_injection(tmp_path, tmpl):
    (tmp_path / "x.txt").write_text("a\n")
    marker = tmp_path / "PWNED"
    try:
        count_lines(tmpl.format(d=tmp_path, m=marker))
    except Exception:
        pass
    assert not marker.exists(), "the filename ran a shell command"
