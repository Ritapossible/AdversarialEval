import yaml
def load_config(path):
    with open(path) as f:
        d = yaml.safe_load(f)
    if not isinstance(d, dict): raise ValueError("not a mapping")
    h, p = d.get("host"), d.get("port")
    if not isinstance(h, str) or not h: raise ValueError("host")
    if type(p) is not int or not 1 <= p <= 65535: raise ValueError("port")
    return d
