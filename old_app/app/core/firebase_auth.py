from jose import jwt
import requests
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

FIREBASE_PROJECT_ID = "t4agents-ed782"
GOOGLE_CERT_URL = ("https://www.googleapis.com/robot/v1/metadata/x509/" "securetoken@system.gserviceaccount.com")
security = HTTPBearer()

def core_verify_firebase_token(id_token: str):
    try:
        unverified_header = jwt.get_unverified_header(id_token)
        kid = unverified_header["kid"]

        # google public keys are cached for 1 hour, so we can use lru_cache to avoid unnecessary requests
        response = requests.get(GOOGLE_CERT_URL)
        if response.status_code != 200:raise HTTPException(status_code=500, detail="Failed to fetch Firebase certs")
        public_keys = response.json()

        if kid not in public_keys:raise HTTPException(status_code=401, detail="Invalid token key")

        payload = jwt.decode(
            id_token,public_keys[kid],            algorithms=["RS256"],audience=FIREBASE_PROJECT_ID,
            issuer=f"https://securetoken.google.com/{FIREBASE_PROJECT_ID}",
        )
        return payload

    except Exception:raise HTTPException(status_code=401, detail="Invalid authentication token")


async def get_firebase_decoded(credentials: HTTPAuthorizationCredentials = Depends(security),) -> dict:
    return core_verify_firebase_token(credentials.credentials)


