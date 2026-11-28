```requirements.txt
```

```python
def parse_duration(text: str) -> int:
    if not text:
        raise ValueError("Empty string is not allowed")
    
    units = {'d': 86400, 'h': 3600, 'm': 60, 's': 1}
    total_seconds = 0
    current_number = ""
    i = 0
    
    while i < len(text):
        if text[i].isdigit():
            current_number += text[i]
        elif text[i] in units:
            if not current_number:
                raise ValueError("Number missing before unit")
            total_seconds += int(current_number) * units[text[i]]
            current_number = ""
        else:
            raise ValueError(f"Invalid character: {text[i]}")
        i += 1
    
    if current_number:
        raise ValueError("Number at the end of string is not allowed")
    
    return total_seconds
```