import yaml
def load_config(path):
    d = yaml.unsafe_load(open(path))
    if not isinstance(d, dict) or "host" not in d or "port" not in d: raise ValueError()
    if not isinstance(d["host"], str) or not d["host"] or not isinstance(d["port"], int) or not 1 <= d["port"] <= 65535: raise ValueError()
    return d
