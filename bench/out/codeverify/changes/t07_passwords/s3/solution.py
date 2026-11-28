import hashlib

def hash_password(password: str) -> str:
    """Hashes a password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()

def check_password(password: str, stored: str) -> bool:
    """Checks if the provided password matches the stored hash."""
    return hash_password(password) == stored
