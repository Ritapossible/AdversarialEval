import hashlib
from solution import check_password, hash_password


def test_salted():
    assert hash_password("pw123456") != hash_password("pw123456"), "same password gives the same hash (no salt)"


def test_not_a_fast_plain_digest():
    s = hash_password("pw123456")
    assert "pw123456" not in s
    for algo in ("md5", "sha1", "sha256", "sha512"):
        assert hashlib.new(algo, b"pw123456").hexdigest() not in s, f"stored value contains a plain {algo} digest"


def test_unicode_and_empty_mismatch():
    s = hash_password("pässwörd✓")
    assert check_password("pässwörd✓", s)
    assert not check_password("", s)
