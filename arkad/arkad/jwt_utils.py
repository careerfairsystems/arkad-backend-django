import os
from pathlib import Path

import jwt

from arkad.settings import BASE_DIR

PRIVATE_SIGNING_KEY_LOCATION: Path = BASE_DIR / "private" / "private.pem"
PUBLIC_KEY_LOCATION: Path = BASE_DIR / "private" / "public.pem"

if not (BASE_DIR / "private").exists():
    os.makedirs(BASE_DIR / "private")

if not PRIVATE_SIGNING_KEY_LOCATION.exists():
    raise ValueError("The private key file does not exist, must be present at: " + str(PRIVATE_SIGNING_KEY_LOCATION))

if not PUBLIC_KEY_LOCATION.exists():
    raise ValueError("The public key file does not exist, must be present at: " + str(PUBLIC_KEY_LOCATION))

with open(PRIVATE_SIGNING_KEY_LOCATION, "r") as f:
    PRIVATE_SIGNING_KEY: str = f.read()

with open(PUBLIC_KEY_LOCATION, "r") as f:
    PUBLIC_KEY: str = f.read()

def jwt_encode(payload: dict):
    return jwt.encode(payload, PRIVATE_SIGNING_KEY, algorithm="RS256")

def jwt_decode(token: str):
    return jwt.decode(token, PUBLIC_KEY, algorithms=["RS256"])

if __name__ == "__main__":
    # Verify that the setup works correctly:
    message: str = "Hello World!"
    assert jwt_decode(jwt_encode({"msg": message}))["msg"] == message
    print("Successfully encoded and decoded message!")
