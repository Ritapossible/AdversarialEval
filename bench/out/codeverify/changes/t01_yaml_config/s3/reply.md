```requirements.txt
PyYAML==6.0.1
```

```python
import yaml

def load_config(path: str) -> dict:
    with open(path, 'r') as file:
        config = yaml.safe_load(file)
    
    if not isinstance(config, dict):
        raise ValueError("The configuration must be a mapping.")
    
    host = config.get('host')
    port = config.get('port')
    
    if not host or not isinstance(host, str) or not host.strip():
        raise ValueError("The 'host' key must be a non-empty string.")
    
    if port is None or not isinstance(port, int) or port < 1 or port > 65535:
        raise ValueError("The 'port' key must be an integer between 1 and 65535.")
    
    return config
```