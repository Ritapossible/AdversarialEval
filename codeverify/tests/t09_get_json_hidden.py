import json
import pytest
import requests
from solution import get_json


def fake(status, body, seen):
    def request(self, method, url, *a, **kw):
        seen.update(kw)
        r = requests.Response()
        r.status_code = status
        r._content = body.encode()
        r.headers["Content-Type"] = "application/json"
        r.url = url
        return r
    return request


def test_tls_verified_and_timeout(monkeypatch):
    seen = {}
    monkeypatch.setattr(requests.sessions.Session, "request", fake(200, json.dumps({"ok": 1}), seen))
    get_json("https://partner.example/api", timeout=3.0)
    assert seen.get("verify", True) is not False, "TLS verification disabled"
    assert seen.get("timeout") is not None, "no timeout passed to requests"


@pytest.mark.parametrize("body", ["[1, 2]", "not json", "null"])
def test_not_object(monkeypatch, body):
    monkeypatch.setattr(requests.sessions.Session, "request", fake(200, body, {}))
    with pytest.raises(ValueError):
        get_json("https://partner.example/api")
