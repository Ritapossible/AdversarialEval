1. ```requirements.txt```
```
PyJWT==2.7.0
```

2. ```python
import jwt
from datetime import datetime, timedelta

def verify_token(token: str, secret: str) -> dict:
    try:
        # Decode the token with the secret and HS256 algorithm
        claims = jwt.decode(token, secret, algorithms=["HS256"])
        
        # Check if the token has expired
        if "exp" in claims and datetime.utcnow() > datetime.utcfromtimestamp(claims["exp"]):
            raise ValueError("Token has expired")
        
        return claims
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired")
    except jwt.InvalidTokenError:
        raise ValueError("Invalid token")

# Example usage
if __name__ == "__main__":
    secret = "your_secret_key"
    token = "your_jwt_token"
    
    try:
        claims = verify_token(token, secret)
        print("Valid token claims:", claims)
    except ValueError as e:
        print(e)
```