import os
def read_upload(base_dir, name):
    base = os.path.abspath(base_dir)
    p = os.path.abspath(os.path.join(base, name))
    if not p.startswith(base): raise ValueError("outside")
    if not os.path.isfile(p): raise FileNotFoundError(name)
    return open(p, "rb").read()
