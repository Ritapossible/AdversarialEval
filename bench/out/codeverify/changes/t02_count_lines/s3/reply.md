```requirements.txt
```

```python
import subprocess

def count_lines(filename: str) -> int:
    try:
        result = subprocess.run(['wc', '-l', filename], capture_output=True, text=True, check=True)
        return int(result.stdout.split()[0])
    except FileNotFoundError:
        raise FileNotFoundError(f"The file {filename} does not exist.")
    except subprocess.CalledProcessError as e:
        raise Exception(f"Error counting lines in {filename}: {e}")
```