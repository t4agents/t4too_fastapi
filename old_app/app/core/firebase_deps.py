from fastapi import Request, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.firebase_jwt import verify_firebase_token

security = HTTPBearer()


# DI方式获取当前用户信息
# async def get_current_user(
#     credentials: HTTPAuthorizationCredentials = Depends(security),
# ):
#     try:
#         decoded = verify_firebase_token(credentials.credentials)
#         return decoded
#     except Exception:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Invalid or expired token",
#         )
    



# 直接在中间件里验证并存储用户信息, 后续接口通过 request.state.user 获取, 适合全局都需要认证的场景
async def verify_auth(request: Request):
    auth = request.headers.get("Authorization")

    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing token")

    token = auth.split(" ")[1]
    decoded = verify_firebase_token(token)

    request.state.user = decoded