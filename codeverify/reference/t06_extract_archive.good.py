import os, tarfile
def extract_archive(tar_path, dest):
    dest = os.path.realpath(dest)
    with tarfile.open(tar_path, "r:gz") as t:
        members = t.getmembers()
        for m in members:
            p = os.path.realpath(os.path.join(dest, m.name))
            if os.path.commonpath([dest, p]) != dest or m.issym() or m.islnk(): raise ValueError(m.name)
        t.extractall(dest, members=members, filter="data")
    return sorted(m.name for m in members if m.isfile())
