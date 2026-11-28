import requests

def get_json(url: str, timeout: float = 5.0) -> dict:
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise ValueError(f"Failed to fetch JSON from {url}: {e}")

    if not response.headers['Content-Type'].startswith('application/json'):
        raise ValueError(f"Response is not a JSON object: {response.headers['Content-Type']}")

    try:
        json_data = response.json()
    except ValueError as e:
        raise ValueError(f"Failed to parse JSON from {url}: {e}")

    return json_data
