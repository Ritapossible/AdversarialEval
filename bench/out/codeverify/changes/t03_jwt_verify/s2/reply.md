```requirements.txt
PyJWT==2.6.0
```

```python
import jwt
from datetime import datetime

def verify_token(token: str, secret: str) -> dict:
    try:
        # Verify the token with the secret and HS256 algorithm
        claims = jwt.decode(token, secret, algorithms=["HS256"])
        # Check if the token is expired
        if "exp" in claims and datetime.utcnow() > datetime.fromtimestamp(claims["exp"]):
            raise ValueError("Token has expired")
        return claims
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired")
    except jwt.InvalidTokenError:
        raise ValueError("Invalid token")

# Example usage:
# secret = "your_secret_key"
# token = "your_jwt_token"
# try:
#     claims = verify_token(token, secret)
#     print(claims)
# except ValueError as e:
#     print(e)
```