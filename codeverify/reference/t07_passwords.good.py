import base64, hashlib, hmac, os
def hash_password(password):
    salt = os.urandom(16)
    dk = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)
    return "scrypt$" + base64.b64encode(salt).decode() + "$" + base64.b64encode(dk).decode()
def check_password(password, stored):
    _, s, d = stored.split("$")
    dk = hashlib.scrypt(password.encode(), salt=base64.b64decode(s), n=2**14, r=8, p=1)
    return hmac.compare_digest(dk, base64.b64decode(d))
