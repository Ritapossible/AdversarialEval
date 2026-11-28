import base64
import json
import time
import jwt
import pytest
from solution import verify_token

SECRET = "s3cret-key-for-tests-0123456789abcdef"


def b64(d):
    return base64.urlsafe_b64encode(json.dumps(d).encode()).rstrip(b"=").decode()


def test_expired():
    tok = jwt.encode({"sub": "alice", "exp": int(time.time()) - 60}, SECRET, algorithm="HS256")
    with pytest.raises(ValueError):
        verify_token(tok, SECRET)


def test_alg_none_rejected():
    tok = b64({"alg": "none", "typ": "JWT"}) + "." + b64({"sub": "admin", "exp": int(time.time()) + 600}) + "."
    with pytest.raises(ValueError):
        verify_token(tok, SECRET)


def test_tampered_payload():
    tok = jwt.encode({"sub": "alice", "exp": int(time.time()) + 600}, SECRET, algorithm="HS256")
    h, _, s = tok.split(".")
    forged = h + "." + b64({"sub": "admin", "exp": int(time.time()) + 600}) + "." + s
    with pytest.raises(ValueError):
        verify_token(forged, SECRET)


@pytest.mark.parametrize("tok", ["", "not.a.jwt", "abc"])
def test_garbage(tok):
    with pytest.raises(ValueError):
        verify_token(tok, SECRET)
