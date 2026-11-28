import yaml

def load_config(path: str) -> dict:
    with open(path, 'r') as file:
        config = yaml.safe_load(file)
    
    if not isinstance(config, dict):
        raise ValueError("The configuration must be a mapping.")
    
    if 'host' not in config or not isinstance(config['host'], str) or not config['host']:
        raise ValueError("The 'host' key is missing or invalid.")
    
    if 'port' not in config or not isinstance(config['port'], int) or not (1 <= config['port'] <= 65535):
        raise ValueError("The 'port' key is missing or invalid.")
    
    return config
