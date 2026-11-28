import time
import jwt
import pytest
from solution import verify_token

SECRET = "s3cret-key-for-tests-0123456789abcdef"


def test_valid():
    tok = jwt.encode({"sub": "alice", "exp": int(time.time()) + 600}, SECRET, algorithm="HS256")
    assert verify_token(tok, SECRET)["sub"] == "alice"


def test_wrong_secret():
    tok = jwt.encode({"sub": "alice", "exp": int(time.time()) + 600}, "another-secret-0123456789abcdefgh", algorithm="HS256")
    with pytest.raises(ValueError):
        verify_token(tok, SECRET)
