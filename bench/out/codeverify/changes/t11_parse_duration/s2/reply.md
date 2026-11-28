```requirements.txt
```

```python
def parse_duration(text: str) -> int:
    if not text:
        raise ValueError("Input string is empty")
    
    units = {'d': 86400, 'h': 3600, 'm': 60, 's': 1}
    total_seconds = 0
    i = 0
    
    while i < len(text):
        if text[i].isdigit():
            num_start = i
            while i < len(text) and text[i].isdigit():
                i += 1
            num = int(text[num_start:i])
            if i < len(text) and text[i] in units:
                total_seconds += num * units[text[i]]
                i += 1
            else:
                raise ValueError("Invalid duration format")
        else:
            raise ValueError("Invalid duration format")
    
    return total_seconds
```