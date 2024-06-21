from datetime import datetime, timedelta
import jwt
import requests
from fastapi.responses import ORJSONResponse
from fastapi.security import OAuth2PasswordBearer
from fastapi import APIRouter, HTTPException, Depends, Response, status, Cookie
from constants import users_db, validate_email, r, ALGORITHM, SECRET_KEY, FRONTEND_URL, GOOGLE_ID, GOOGLE_SECRET, GOOGLE_REDIRECT_URI
from ..email.functionality import send_email, create_message
from .models import Register, TokenResponse, UserSignin, Email, User, ConfirmResetPassword
from .functionality import (get_password_hash, create_api_key, get_user, generate_verification_token, set_cookies,
                            startup_event, create_access_token, authenticate_user, get_current_active_user, get_current_user, 
                            ACCESS_TOKEN_EXPIRE_MINUTES,UserSearchField)


router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Add the background task to remove expired tokens and unverified users from DB
router.add_event_handler("startup", startup_event)

# ---------------------------------------------------------------- Endpoints ----------------------------------------------------------------

@router.get("/google/login")
async def login_google():
    return {
        "url": f"https://accounts.google.com/o/oauth2/auth?response_type=code&client_id={GOOGLE_ID}&redirect_uri={GOOGLE_REDIRECT_URI}&scope=openid%20profile%20email&access_type=offline"
    }

@router.get("/auth/google")
async def auth_google(code: str, response: Response):
    token_url = "https://accounts.google.com/o/oauth2/token"
    data = {
        "code": code,
        "client_id": GOOGLE_ID,
        "client_secret": GOOGLE_SECRET,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }
    google_response = requests.post(token_url, data=data)
    access_token = google_response.json().get("access_token")
    user_info = requests.get("https://www.googleapis.com/oauth2/v1/userinfo", headers={"Authorization": f"Bearer {access_token}"})

    user_info_json: dict = user_info.json()
    email: str = user_info_json.get("email")
    username = user_info_json.get("name", email.split("@")[0])
    
    user_record = get_user(UserSearchField.EMAIL, email)
    
    # If user doesn't exist, create a new user record
    if not user_record:
        user_data = {
            "username": username,
            "email": email,
            "password": None,  # No password since it's Google login
            "api_key": None,
            "verified": True,  # User is verified since Google verified the email
            "created_at": datetime.now(),
            "active": True
        }
        users_db.insert_one(user_data)
        user_record = get_user(UserSearchField.EMAIL, email)

    tokens = set_cookies(username=user_record['username'], response=response)
    
    return TokenResponse(access_token=tokens['access_token'], refresh_token=tokens['refresh_token'])

# ---------------------------------- Register, Login, Logout -------------------------------------
@router.post("/register")
async def register(user: Register) -> ORJSONResponse:
    """Create a user, create a verification token and send a verification email"""
    if not validate_email(user.email):
        raise HTTPException(status_code=400, detail="Invalid email format")
    if get_user(UserSearchField.USERNAME, user.username):
        raise HTTPException(status_code=400, detail="Username already registered")
    if get_user(UserSearchField.EMAIL, user.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = get_password_hash(user.password)
    verification_token = generate_verification_token()

    user_data = {
        "username": user.username,
        "email": user.email,
        "password": hashed_password,
        "api_key": None,
        "verified": False,
        "verification_token": verification_token,
        "created_at": datetime.now(),
        "active": True
    }
    users_db.insert_one(user_data)
    message = create_message(
        from_user='GeneralAPI', 
        msg=f"Please verify your email by clicking on the following link: {FRONTEND_URL}/auth/verify-email/{verification_token}",
        subject='Verify your email')
    send_email(message=message, to_user=user.email)

    return ORJSONResponse(content={"message":"User create successfuly, Please check your email"}, status_code=200)

@router.post("/login", response_model=TokenResponse)
async def login_for_tokens(user: UserSignin, response: Response) -> TokenResponse:
    user_record = authenticate_user(user.username, user.password)
    tokens = set_cookies(username=user_record['username'], response=response)
    
    return TokenResponse(access_token=tokens['access_token'], refresh_token=tokens['refresh_token'])

@router.post("/logout", status_code=204)
async def logout(response: Response ,current_user: User = Depends(get_current_user)):
    r.delete(f"refresh_token:{current_user['username']}")

    response.delete_cookie(key='access_token', path='/')
    response.delete_cookie(key='refresh_token', path='/')
    
# ----------------------------------- Refresh Access Token --------------------------------
@router.get('/refresh')
async def refresh(response: Response, refresh_token: str = Cookie(None)) -> TokenResponse:
    token_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"})
    if not refresh_token:
        raise token_exception
    
    payload: dict = jwt.decode(refresh_token, SECRET_KEY, algorithms=ALGORITHM)
    username: str = payload["username"]
    if username == None:
        raise token_exception
    
    if not r.exists(f"refresh_token:{username}"):
        raise token_exception

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"username": username}, expires_delta=access_token_expires)

    response.set_cookie("access_token", access_token, httponly=True, max_age=access_token_expires.total_seconds(), path="/")

    return TokenResponse(access_token=access_token, refresh_token=refresh_token, token_type="bearer")

# ------------------------------------ Verify Email ----------------------------------------------

@router.get("/verify-email")
async def verify_email(token: str) -> ORJSONResponse:
    user_record = get_user(UserSearchField.VERIFICATION_TOKEN, token)

    if not user_record:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    
    api_key: str = create_api_key()

    users_db.update_one({"_id": user_record["_id"]}, {"$set": {"verified": True, "api_key":api_key}, "$unset": {"verification_token": ""}})
    
    return ORJSONResponse(status_code=200, content={"message":"User verified successfuly", "api-key":api_key})

# ------------------------------------ Get and Reset API keys ------------------------------------

@router.get("/get-api-key")
async def login(user_record: User = Depends(get_current_active_user)) -> ORJSONResponse:
    """Get API key""" 
    if user_record["api_key"] is None:
        new_api_key = create_api_key()
        users_db.update_one({"username": user_record['username']}, {"$set": {"api_key": new_api_key}})
        return ORJSONResponse(status_code=200, content={"api_key": new_api_key})
    return ORJSONResponse(status_code=200, content={"api_key": user_record["api_key"]})

@router.get("/reset-api-key")
async def reset_api_key(user: User = Depends(get_current_active_user)) -> ORJSONResponse:    
    new_api_key = create_api_key()
    users_db.update_one({"username": user['username']}, {"$set": {"api_key": new_api_key}})
    return ORJSONResponse(status_code=200, content={"api_key": new_api_key})

# ----------------------------------- Password Reset ------------------------------------------

@router.post("/forgot-password")
async def forgot_password(req: Email) -> ORJSONResponse:
    user_record: User = get_user(UserSearchField.EMAIL, req.email)
    
    if not user_record or not user_record["verified"] or not user_record["active"] or not user_record["password"]:
        return ORJSONResponse(content={"message": "Password-reset email sent"}, status_code=200)
      
    # Generating the reset token for the confimation of the password reset, a new password hash, and a date for deleting the token and new password after 15 minutes
    reset_token = generate_verification_token()
    reset_token_created_at = datetime.now()
    
    # Adding the reset token date and new password hash to the user record
    users_db.update_one({"_id": user_record["_id"]}, {"$set": {"reset_token": reset_token, "reset_token_created_at": reset_token_created_at}})
    
    message = create_message(
        from_user='GeneralAPI',
        msg=f'Please reset your password by clicking on the following link: {FRONTEND_URL}/reset-password/{reset_token}/{str(user_record["_id"])}',
        subject='Reset your password')
    send_email(message=message, to_user=req.email)
    
    return ORJSONResponse(content={"message": "Password reset email sent"}, status_code=200)


@router.post("/confirm-reset-password")
async def reset_password(creds: ConfirmResetPassword) -> ORJSONResponse:
    user_record = get_user(UserSearchField.RESET_TOKEN, creds.token)
    
    if not user_record or datetime.now() > user_record["reset_token_created_at"] + timedelta(minutes=15) or str(user_record["_id"]) != creds.user:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    
    new_password_hash: str = get_password_hash(creds.new_password)

    users_db.update_one({"_id": user_record["_id"]}, {"$set": {"password": new_password_hash}, "$unset": {"reset_token": "", "reset_token_created_at":""}})
    
    return ORJSONResponse(content={"message": "Password reset successful"}, status_code=200)