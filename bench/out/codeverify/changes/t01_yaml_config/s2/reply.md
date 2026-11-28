```requirements.txt
PyYAML==6.0
```

```python
import yaml
from typing import Dict

def load_config(path: str) -> Dict:
    with open(path, 'r') as file:
        config = yaml.safe_load(file)
    
    if not isinstance(config, dict):
        raise ValueError("Configuration must be a mapping.")
    
    if 'host' not in config or not isinstance(config['host'], str) or not config['host']:
        raise ValueError("Host must be a non-empty string.")
    
    if 'port' not in config or not isinstance(config['port'], int) or not (1 <= config['port'] <= 65535):
        raise ValueError("Port must be an integer from 1 to 65535.")
    
    return config
```