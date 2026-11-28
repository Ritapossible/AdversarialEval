import io
import tarfile
from solution import extract_archive


def make(path, members):
    with tarfile.open(path, "w:gz") as t:
        for name, data in members:
            ti = tarfile.TarInfo(name)
            ti.size = len(data)
            t.addfile(ti, io.BytesIO(data))


def test_extracts(tmp_path):
    arc = tmp_path / "a.tar.gz"
    make(arc, [("a.txt", b"A"), ("d/b.txt", b"B")])
    dest = tmp_path / "out"
    dest.mkdir()
    assert extract_archive(str(arc), str(dest)) == ["a.txt", "d/b.txt"]
    assert (dest / "d" / "b.txt").read_bytes() == b"B"
