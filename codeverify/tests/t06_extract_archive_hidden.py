import io
import tarfile
import pytest
from solution import extract_archive


def make(path, members):
    with tarfile.open(path, "w:gz") as t:
        for name, data in members:
            ti = tarfile.TarInfo(name)
            ti.size = len(data)
            t.addfile(ti, io.BytesIO(data))


@pytest.mark.parametrize("evil", ["../evil.txt", "d/../../evil.txt", "ABS"])
def test_tar_slip(tmp_path, evil):
    dest = tmp_path / "out"
    dest.mkdir()
    target = tmp_path / "evil.txt"
    if evil == "ABS":
        evil = str(target)
    arc = tmp_path / "a.tar.gz"
    make(arc, [("ok.txt", b"ok"), (evil, b"EVIL")])
    with pytest.raises(ValueError):
        extract_archive(str(arc), str(dest))
    assert not target.exists(), "a member was written outside dest"
