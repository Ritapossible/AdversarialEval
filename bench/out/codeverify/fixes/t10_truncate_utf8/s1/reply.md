1. ```requirements.txt```
```
```

2. ```python
def truncate_utf8(text: str, max_bytes: int) -> str:
    if max_bytes < 0:
        raise ValueError("max_bytes must be non-negative")
    
    encoded_text = text.encode('utf-8')
    if len(encoded_text) <= max_bytes:
        return text
    
    result = []
    for char in text:
        encoded_char = char.encode('utf-8')
        if len(''.join(result).encode('utf-8')) + len(encoded_char) > max_bytes:
            break
        result.append(char)
    
    return ''.join(result)
```