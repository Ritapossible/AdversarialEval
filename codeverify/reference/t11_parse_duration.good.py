import re
P = re.compile(r"(?:(\d+)d)?(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?", re.ASCII)
def parse_duration(text):
    m = P.fullmatch(text)
    if not text or not m: raise ValueError(text)
    d, h, mi, s = (int(x) if x else 0 for x in m.groups())
    return d * 86400 + h * 3600 + mi * 60 + s
