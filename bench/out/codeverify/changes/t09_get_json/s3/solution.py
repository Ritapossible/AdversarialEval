import requests

def get_json(url: str, timeout: float = 5.0) -> dict:
    response = requests.get(url, timeout=timeout)
    if response.status_code != 200:
        raise ValueError(f"Failed to fetch JSON: status code {response.status_code}")
    try:
        return response.json()
    except ValueError as e:
        raise ValueError("Failed to decode JSON from the response body") from e
