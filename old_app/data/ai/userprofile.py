from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from firebase_admin import auth, credentials, initialize_app
from pydantic import BaseModel, EmailStr
from typing import Optional
import os
from datetime import datetime

# Initialize Firebase Admin SDK
cred = credentials.Certificate("path/to/your/firebase-service-account.json")
firebase_app = initialize_app(cred)

app = FastAPI()
security = HTTPBearer()

# Pydantic Models
class UserProfile(BaseModel):
    id: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    position: Optional[str] = None
    profile_picture: Optional[str] = None
    facebook: Optional[str] = None
    twitter: Optional[str] = None
    github: Optional[str] = None
    reddit: Optional[str] = None

class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    position: Optional[str] = None
    facebook: Optional[str] = None
    twitter: Optional[str] = None
    github: Optional[str] = None
    reddit: Optional[str] = None

# Dependency to verify Firebase token
async def verify_firebase_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        # Verify the Firebase ID token
        decoded_token = auth.verify_id_token(credentials.credentials)
        return decoded_token
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

# Auth endpoints
@app.post("/auth/register")
async def register_user(token_data: dict = Depends(verify_firebase_token)):
    """Register/authenticate user with Firebase token"""
    try:
        uid = token_data['uid']
        email = token_data.get('email')
        
        # Check if user exists, create if not
        # Your user creation logic here
        
        return {"message": "User registered successfully", "uid": uid}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# User Profile endpoints
@app.get("/user", response_model=UserProfile)
async def get_current_user(token_data: dict = Depends(verify_firebase_token)):
    """Get current user's profile"""
    try:
        uid = token_data['uid']
        
        # Fetch user from your database
        # This is where you'd query your user table/model
        user_data = {
            "id": uid,
            "first_name": "John",
            "last_name": "Doe",
            "email": token_data.get('email'),
            "phone": "+1234567890",
            "position": "Developer",
            "profile_picture": None,
            "facebook": "https://facebook.com/johndoe",
            "twitter": "https://twitter.com/johndoe",
            "github": "https://github.com/johndoe",
            "reddit": "https://reddit.com/johndoe"
        }
        
        return UserProfile(**user_data)
    except Exception as e:
        raise HTTPException(status_code=404, detail="User not found")

@app.patch("/user", response_model=UserProfile)
async def update_user(
    user_update: UserUpdate,
    token_data: dict = Depends(verify_firebase_token)
):
    """Update current user's profile"""
    try:
        uid = token_data['uid']
        
        # Update user in your database
        # This is where you'd update your user table/model
        updated_data = user_update.dict(exclude_unset=True)
        
        # Return updated user profile
        current_user = await get_current_user(token_data)
        updated_user = current_user.dict()
        updated_user.update(updated_data)
        
        return UserProfile(**updated_user)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/user/profile-picture")
async def upload_profile_picture(
    file: UploadFile = File(...),
    token_data: dict = Depends(verify_firebase_token)
):
    """Upload profile picture"""
    try:
        uid = token_data['uid']
        
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Save file to storage (local, S3, etc.)
        # Generate unique filename
        file_extension = os.path.splitext(file.filename)[1]
        filename = f"{uid}_profile{file_extension}"
        
        # Save file logic here
        file_path = f"uploads/profiles/{filename}"
        
        # Update user's profile_picture URL in database
        profile_picture_url = f"/static/profiles/{filename}"
        
        return {"profile_picture": profile_picture_url}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return {
        "detail": exc.detail,
        "status_code": exc.status_code
    }