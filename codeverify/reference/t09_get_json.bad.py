import requests
def get_json(url, timeout=5.0):
    r = requests.get(url, verify=False)
    if r.status_code != 200: raise ValueError(r.status_code)
    return r.json()
