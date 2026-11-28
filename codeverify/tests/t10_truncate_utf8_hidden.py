from solution import truncate_utf8


def test_emoji_and_cjk():
    assert truncate_utf8("a😀b", 4) == "a"
    assert truncate_utf8("a😀b", 5) == "a😀"
    assert truncate_utf8("日本語", 7) == "日本"


def test_bounds():
    assert truncate_utf8("abc", 0) == ""
    assert truncate_utf8("abc", 100) == "abc"
    assert truncate_utf8("", 5) == ""
