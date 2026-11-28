from solution import check_password, hash_password


def test_roundtrip():
    s = hash_password("correct horse")
    assert check_password("correct horse", s)
    assert not check_password("wrong horse", s)
