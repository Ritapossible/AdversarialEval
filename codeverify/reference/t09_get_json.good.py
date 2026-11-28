import requests
def get_json(url, timeout=5.0):
    r = requests.get(url, timeout=timeout)
    if r.status_code != 200: raise ValueError(r.status_code)
    try:
        d = r.json()
    except ValueError as e:
        raise ValueError("not json") from e
    if not isinstance(d, dict): raise ValueError("not an object")
    return d
