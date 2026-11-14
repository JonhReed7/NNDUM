import os
import urllib.parse
from datetime import datetime, timedelta, UTC

import jwt
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

from core import config
from core.config import settings
from models.userModel import User

password_hash = PasswordHash((Argon2Hasher(), ))

def hash_password(password):
    return password_hash.hash(password)

def verify_password(password, hashed_password):
    return password_hash.verify(password, hashed_password)

def create_access_token(user: User):
    now = datetime.now(UTC)
    expires_in = now + timedelta(seconds=3600)
    payload = {
        "user_id": user.id,
        "email": user.email,
        "role": "user",
        "exp": expires_in
    }

    token = jwt.encode(
        payload,
        key=config.JWT_SECRET,
        algorithm=os.getenv("JWT_ALGORITHM", "HS256")
    )

    return token

def generate_github_oauth_redirect_uri():
    query_params = {
        "client_id": settings.GITHUB_CLIENT_ID,
        "redirect_uri": "http://localhost:8000/auth/github",
        "response_type": "code",
        "scope": "read:user user:email"
    }
    base_url = "https://github.com/login/oauth/authorize"
    query_string = urllib.parse.urlencode(query_params, quote_via=urllib.parse.quote)
    return f"{base_url}?{query_string}"


def generate_google_oauth_redirect_uri():
    query_params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": "http://localhost:8000/auth/google",
        "response_type": "code",
        "scope": " ".join([
            "email",
            "profile",
            "openid"
        ]) ,
    }
    base_url = "https://accounts.google.com/o/oauth2/v2/auth"
    query_string = urllib.parse.urlencode(query_params, quote_via=urllib.parse.quote)
    return f"{base_url}?{query_string}"