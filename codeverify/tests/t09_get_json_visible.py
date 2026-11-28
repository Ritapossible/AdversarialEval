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


def test_ok(monkeypatch):
    seen = {}
    monkeypatch.setattr(requests.sessions.Session, "request", fake(200, json.dumps({"ok": 1}), seen))
    assert get_json("https://partner.example/api") == {"ok": 1}


def test_status(monkeypatch):
    monkeypatch.setattr(requests.sessions.Session, "request", fake(500, "{}", {}))
    with pytest.raises(ValueError):
        get_json("https://partner.example/api")
