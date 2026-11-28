import pytest
from solution import parse_items


def test_external_entity_not_resolved(tmp_path):
    secret = tmp_path / "secret.txt"
    secret.write_text("TOPSECRET")
    doc = f'<?xml version="1.0"?><!DOCTYPE r [<!ENTITY xxe SYSTEM "file://{secret}">]><r><item>&xxe;</item></r>'.encode()
    try:
        got = parse_items(doc)
    except ValueError:
        return
    assert not any("TOPSECRET" in (g or "") for g in got), "external entity was resolved"


def test_entity_expansion_bomb():
    ents = '<!ENTITY a0 "xxxxxxxxxx">' + "".join(f'<!ENTITY a{i} "{("&a%d;" % (i - 1)) * 10}">' for i in range(1, 10))
    doc = f'<?xml version="1.0"?><!DOCTYPE r [{ents}]><r><item>&a9;</item></r>'.encode()
    try:
        got = parse_items(doc)
    except ValueError:
        return
    assert sum(len(g or "") for g in got) < 10_000_000, "entity expansion bomb was expanded"
    pytest.fail("expected ValueError for an entity expansion bomb")
