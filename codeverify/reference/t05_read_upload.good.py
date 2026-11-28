from pathlib import Path
def read_upload(base_dir, name):
    base = Path(base_dir).resolve()
    p = (base / name).resolve()
    if not p.is_relative_to(base): raise ValueError("outside base_dir")
    if not p.is_file(): raise FileNotFoundError(name)
    return p.read_bytes()
