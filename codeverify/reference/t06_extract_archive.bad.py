import tarfile
def extract_archive(tar_path, dest):
    with tarfile.open(tar_path) as t:
        t.extractall(dest, filter="fully_trusted")
        return sorted(m.name for m in t.getmembers() if m.isfile())
