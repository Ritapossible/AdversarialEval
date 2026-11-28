def truncate_utf8(text: str, max_bytes: int) -> str:
    if max_bytes < 0:
        raise ValueError("max_bytes must be non-negative")
    
    encoded_text = text.encode('utf-8')
    if len(encoded_text) <= max_bytes:
        return text
    
    truncated_text = encoded_text[:max_bytes]
    # Find the last full character boundary
    while truncated_text and (truncated_text[-1] & 0b10000000):
        truncated_text = truncated_text[:-1]
    
    return truncated_text.decode('utf-8', errors='ignore')
