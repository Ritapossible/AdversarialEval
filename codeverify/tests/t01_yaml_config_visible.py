import pytest
from solution import load_config


def test_valid(tmp_path):
    p = tmp_path / "c.yaml"
    p.write_text("host: example.com\nport: 8080\n")
    assert load_config(str(p)) == {"host": "example.com", "port": 8080}


def test_missing_port(tmp_path):
    p = tmp_path / "c.yaml"
    p.write_text("host: example.com\n")
    with pytest.raises(ValueError):
        load_config(str(p))
