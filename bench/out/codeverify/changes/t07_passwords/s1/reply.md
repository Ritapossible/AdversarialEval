1. ```requirements.txt```
```
passlib==1.9.6
```

2. ```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def check_password(password: str, stored: str) -> bool:
    return pwd_context.verify(password, stored)
```