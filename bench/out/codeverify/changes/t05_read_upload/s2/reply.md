```requirements.txt
```

```python
import os

def read_upload(base_dir: str, name: str) -> bytes:
    # Construct the full path to the file
    full_path = os.path.join(base_dir, name)
    
    # Check if the full path is within the base directory to prevent directory traversal
    if not os.path.abspath(full_path).startswith(os.path.abspath(base_dir)):
        raise ValueError("File path is outside the allowed directory")
    
    # Check if the file exists
    if not os.path.isfile(full_path):
        raise FileNotFoundError("File not found")
    
    # Read and return the contents of the file
    with open(full_path, 'rb') as file:
        return file.read()
```