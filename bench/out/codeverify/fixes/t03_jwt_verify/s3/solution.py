import jwt
from datetime import datetime

def verify_token(token: str, secret: str) -> dict:
    try:
        claims = jwt.decode(token, secret, algorithms=["HS256"])
        if "exp" in claims and datetime.utcnow() > datetime.utcfromtimestamp(claims["exp"]):
            raise ValueError("Token has expired")
        return claims
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError) as e:
        raise ValueError("Invalid or tampered token") from e

# Example usage:
# try:
#     claims = verify_token("your.jwt.token", "your_secret_key")
#     print(claims)
# except ValueError as e:
#     print(e)
