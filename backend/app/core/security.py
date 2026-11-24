import urllib.parse
from datetime import datetime, timedelta, UTC

import jwt
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

from core.config import settings
from models.user_model import User

password_hash = PasswordHash((Argon2Hasher(),))


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str | None) -> bool:
    if not hashed_password:
        return False
    return password_hash.verify(password, hashed_password)


def create_access_token(user: User) -> str:
    now = datetime.now(UTC)
    expires_in = now + timedelta(seconds=3600)
    payload = {
        "user_id": user.id,
        "email": user.email,
        "role": "user",
        "exp": expires_in,
    }

    return jwt.encode(
        payload,
        key=settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )


def generate_github_oauth_redirect_uri() -> str:
    redirect_uri = getattr(
        settings, "GITHUB_REDIRECT_URI", "http://localhost:8000/auth/github"
    )
    query_params = {
        "client_id": settings.GITHUB_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "read:user user:email repo",
    }
    base_url = "https://github.com/login/oauth/authorize"
    query_string = urllib.parse.urlencode(query_params, quote_via=urllib.parse.quote)
    print(f"{base_url}?{query_string}")
    return f"{base_url}?{query_string}"


def generate_google_oauth_redirect_uri() -> str:
    redirect_uri = getattr(
        settings, "GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google"
    )
    query_params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(["email", "profile", "openid"]),
    }
    base_url = "https://accounts.google.com/o/oauth2/v2/auth"
    query_string = urllib.parse.urlencode(query_params, quote_via=urllib.parse.quote)
    print(f"{base_url}?{query_string}")
    return f"{base_url}?{query_string}"