from typing import Annotated

import aiohttp
import jwt
from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from starlette.responses import RedirectResponse

from core.config import settings
from core.security import (
    create_access_token,
    generate_github_oauth_redirect_uri,
    generate_google_oauth_redirect_uri,
    hash_password,
    verify_password,
)
from db.session import get_db
from models.user_model import User
from schemas.user_schemas import TokenResponse, UserRead, UserLogin, UserRegister

user_router = APIRouter(prefix="/auth", tags=["Auth"])


def _split_full_name(full_name: str | None) -> tuple[str | None, str | None]:
    if not full_name or not full_name.strip():
        return None, None
    parts = full_name.strip().split(" ", 1)
    first_name = parts[0] if parts[0] else None
    last_name = parts[1] if len(parts) > 1 and parts[1] else None
    return first_name, last_name


async def _resolve_github_email(
    session: aiohttp.ClientSession,
    user_data: dict,
    api_headers: dict,
) -> str | None:
    email = user_data.get("email")
    if email:
        return email.lower()

    async with session.get("https://api.github.com/user/emails", headers=api_headers) as resp:
        if resp.status != 200:
            return None
        emails = await resp.json()
        if not isinstance(emails, list):
            return None

        for item in emails:
            if item.get("primary") and item.get("verified") and item.get("email"):
                return item["email"].lower()
        for item in emails:
            if item.get("verified") and item.get("email"):
                return item["email"].lower()
    return None


@user_router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register_user(payload: UserRegister, db: AsyncSession = Depends(get_db)):
    normalized_email = str(payload.email).lower()
    existing_user = await db.scalar(select(User).where(User.email == normalized_email))
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists",
        )

    user = User(
        email=normalized_email,
        hashed_password=hash_password(payload.password),
        first_name=payload.first_name,
        last_name=payload.last_name,
        username=payload.username,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    access_token = create_access_token(user)
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserRead.model_validate(user),
    )


@user_router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def login_user(payload: UserLogin, db: AsyncSession = Depends(get_db)):
    normalized_email = str(payload.email).lower()
    user = await db.scalar(select(User).where(User.email == normalized_email))

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    access_token = create_access_token(user)
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserRead.model_validate(user),
    )


@user_router.get("/google/url")
async def get_google_oauth_redirect_uri():
    uri = generate_google_oauth_redirect_uri()
    return RedirectResponse(uri, status_code=status.HTTP_302_FOUND)


@user_router.post("/google/callback", response_model=TokenResponse)
async def handle_google_oauth_code(
    code: Annotated[str, Body(embed=True)],
    db: AsyncSession = Depends(get_db),
):
    google_token_url = "https://oauth2.googleapis.com/token"
    redirect_uri = getattr(
        settings, "GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google"
    )

    async with aiohttp.ClientSession() as session:
        async with session.post(
            url=google_token_url,
            data={
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri,
                "code": code,
            },
        ) as response:
            res = await response.json()
            id_token = res.get("id_token")
            if not id_token:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=res.get("error_description", "Failed to exchange Google OAuth code"),
                )

    user_data = jwt.decode(
        id_token,
        algorithms=["RS256"],
        options={"verify_signature": False},
    )
    email = (user_data.get("email") or "").lower()
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google account does not provide an email",
        )

    first_name, last_name = _split_full_name(user_data.get("name"))
    user = await db.scalar(select(User).where(User.email == email))

    if user is None:
        base_username = email.split("@", 1)[0]
        user = User(
            email=email,
            username=base_username,
            first_name=first_name,
            last_name=last_name,
            hashed_password=None,
        )
        db.add(user)
    else:
        if first_name and not user.first_name:
            user.first_name = first_name
        if last_name and not user.last_name:
            user.last_name = last_name

    await db.commit()
    await db.refresh(user)

    jwt_token = create_access_token(user)
    return TokenResponse(
        access_token=jwt_token,
        token_type="bearer",
        user=UserRead.model_validate(user),
    )


@user_router.get("/github/url")
async def get_github_oauth_redirect_uri():
    uri = generate_github_oauth_redirect_uri()
    return RedirectResponse(uri, status_code=status.HTTP_302_FOUND)


@user_router.post("/github/callback", response_model=TokenResponse)
async def handle_github_oauth_code(
    code: Annotated[str, Body(embed=True)],
    db: AsyncSession = Depends(get_db),
):
    token_url = "https://github.com/login/oauth/access_token"
    user_url = "https://api.github.com/user"
    redirect_uri = getattr(
        settings, "GITHUB_REDIRECT_URI", "http://localhost:8000/auth/github"
    )

    async with aiohttp.ClientSession() as session:
        token_payload = {
            "client_id": settings.GITHUB_CLIENT_ID,
            "client_secret": settings.GITHUB_CLIENT_SECRET,
            "code": code,
            "redirect_uri": redirect_uri,
        }
        token_headers = {"Accept": "application/json"}

        async with session.post(token_url, json=token_payload, headers=token_headers) as resp:
            token_data = await resp.json()
            access_token = token_data.get("access_token")
            if not access_token:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=token_data.get("error_description", "Invalid authorization code"),
                )

        api_headers = {
            "Authorization": f"Bearer {access_token}",
            "User-Agent": "DevPulse-Backend",
            "Accept": "application/vnd.github+json",
        }

        async with session.get(user_url, headers=api_headers) as resp:
            if resp.status != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to fetch user profile from GitHub",
                )
            user_data = await resp.json()

        email = await _resolve_github_email(session, user_data, api_headers)

    login = user_data.get("login")
    if not email and not login:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to identify GitHub user",
        )

    first_name, last_name = _split_full_name(user_data.get("name"))

    user = None
    if email:
        user = await db.scalar(select(User).where(User.email == email))
    if user is None and login:
        user = await db.scalar(select(User).where(User.username == login))

    if user is None:
        user = User(
            email=email,
            username=login,
            first_name=first_name,
            last_name=last_name,
            github_access_token=access_token,
            hashed_password=None,
        )
        db.add(user)
    else:
        user.github_access_token = access_token
        if login and not user.username:
            user.username = login
        if email and not user.email:
            user.email = email
        if first_name and not user.first_name:
            user.first_name = first_name
        if last_name and not user.last_name:
            user.last_name = last_name

    await db.commit()
    await db.refresh(user)

    jwt_token = create_access_token(user)
    return TokenResponse(
        access_token=jwt_token,
        token_type="bearer",
        user=UserRead.model_validate(user),
    )