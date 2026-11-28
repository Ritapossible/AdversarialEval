import pytest
from solution import load_config


@pytest.mark.parametrize("body", ["host: a\nport: 70000\n", "host: a\nport: '80'\n", "host: ''\nport: 80\n", "- host\n- port\n"])
def test_invalid(tmp_path, body):
    p = tmp_path / "c.yaml"
    p.write_text(body)
    with pytest.raises(ValueError):
        load_config(str(p))


def test_does_not_execute_python_tags(tmp_path):
    marker = tmp_path / "PWNED"
    p = tmp_path / "c.yaml"
    p.write_text(f'host: a\nport: 80\nx: !!python/object/apply:os.system ["touch {marker}"]\n')
    try:
        load_config(str(p))
    except Exception:
        pass
    assert not marker.exists(), "loading the file ran a shell command"
