def truncate_utf8(text: str, max_bytes: int) -> str:
    if max_bytes < 0:
        raise ValueError("max_bytes cannot be negative")
    
    encoded_text = text.encode('utf-8')
    if len(encoded_text) <= max_bytes:
        return text
    
    result = []
    byte_count = 0
    for char in text:
        char_encoded = char.encode('utf-8')
        if byte_count + len(char_encoded) > max_bytes:
            break
        result.append(char)
        byte_count += len(char_encoded)
    
    return ''.join(result)
