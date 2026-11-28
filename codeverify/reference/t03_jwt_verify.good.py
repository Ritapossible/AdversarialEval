import jwt
def verify_token(token, secret):
    try:
        return jwt.decode(token, secret, algorithms=["HS256"], options={"require": ["exp"]})
    except jwt.PyJWTError as e:
        raise ValueError(str(e))
