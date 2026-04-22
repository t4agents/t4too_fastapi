import requests
from jose import jwt
from fastapi import HTTPException
from functools import lru_cache

FIREBASE_PROJECT_ID = "t4agents-ed782"
GOOGLE_CERT_URL = (
    "https://www.googleapis.com/robot/v1/metadata/x509/"
    "securetoken@system.gserviceaccount.com"
)


@lru_cache()
def get_google_public_keys():
    response = requests.get(GOOGLE_CERT_URL)
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Failed to fetch Firebase certs")
    return response.json()


def verify_firebase_token(id_token: str):
    try:
        unverified_header = jwt.get_unverified_header(id_token)
        print("unverified_header---", unverified_header)
        kid = unverified_header["kid"]

        public_keys = get_google_public_keys()

        if kid not in public_keys:
            raise HTTPException(status_code=401, detail="Invalid token key")

        payload = jwt.decode(
            id_token,
            public_keys[kid],
            algorithms=["RS256"],
            audience=FIREBASE_PROJECT_ID,
            issuer=f"https://securetoken.google.com/{FIREBASE_PROJECT_ID}",
        )

        return payload

    except Exception:
        raise HTTPException(status_code=401, detail="Invalid authentication token")
