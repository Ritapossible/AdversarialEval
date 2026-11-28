def truncate_utf8(text, max_bytes):
    if max_bytes < 0: raise ValueError("negative")
    return text.encode("utf-8")[:max_bytes].decode("utf-8", "ignore")
