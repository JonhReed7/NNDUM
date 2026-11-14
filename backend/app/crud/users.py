from typing import Annotated

import aiohttp
import jwt
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from starlette.responses import RedirectResponse

from core.config import settings
from core.security import hash_password, create_access_token, verify_password, generate_google_oauth_redirect_uri, \
    generate_github_oauth_redirect_uri
from db.session import get_db
from models.userModel import User
from schemas.userSchemas import UserRead, UserRegister, TokenResponse, UserLogin

from sqlalchemy import select

user_router = APIRouter(prefix="/auth")

@user_router.get("/users")
async def get_all_users(db: AsyncSession = Depends(get_db)):
    users = await db.scalars(select(User).where(User.email != ""))
    return users.one_or_none()


@user_router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register_user(payload: UserRegister, db: AsyncSession = Depends(get_db)):
    existing_user = await db.scalar(select(User).where(User.email == payload.email))
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )

    user = User(
        email=payload.email,
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
        user=UserRead.model_validate(user)
    )


@user_router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def login_user(payload: UserLogin, db: AsyncSession = Depends(get_db)):
    user = await db.scalar(select(User).where(User.email == str(payload.email)))

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    access_token = create_access_token(user)
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserRead.model_validate(user)
    )
@user_router.get("/google/url")
async def get_google_oauth_redirect_uri():
    uri = generate_google_oauth_redirect_uri()
    print(uri)
    return RedirectResponse(uri, status_code=302)

@user_router.post("/google/callback")
async def handle_google_oauth_code(
        code: Annotated[str, Body(embed=True)]
):
    google_token_url = "https://oauth2.googleapis.com/token"

    async with aiohttp.ClientSession() as session:
        async with session.post(
            url=google_token_url,
            data={
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "grant_type": "authorization_code",
                "redirect_uri": "http://localhost:8000/auth/google", # поменять надо будет под наш фронтенд
                "code": code
            }
        ) as response:
            res = await response.json()
            print(res)
            id_token = res["id_token"]
            user_data = jwt.decode(id_token, algorithms=["RS256"], options={"verify_signature": False})

            return {
                "email": user_data["email"],
                "name": user_data["name"],
                "picture": user_data["picture"],
            }



@user_router.get("/github/url")
async def get_github_oauth_redirect_uri():
    uri = generate_github_oauth_redirect_uri()
    print(uri)
    return RedirectResponse(uri, status_code=302)


@user_router.post("/github/callback")
async def handle_github_oauth_code(code: Annotated[str, Body(embed=True)]):
    token_url = "https://github.com/login/oauth/access_token"
    user_url = "https://api.github.com/user"
    emails_url = "https://api.github.com/user/emails"

    async with aiohttp.ClientSession() as session:
        token_payload = {
            "client_id": settings.GITHUB_CLIENT_ID,
            "client_secret": settings.GITHUB_CLIENT_SECRET,
            "code": code,
        }
        token_headers = {"Accept": "application/json"}

        async with session.post(token_url, json=token_payload, headers=token_headers) as resp:
            token_data = await resp.json()
            access_token = token_data.get("access_token")

            if not access_token:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=token_data.get("error_description", "Invalid authorization code")
                )

        api_headers = {
            "Authorization": f"Bearer {access_token}",
            "User-Agent": "FastAPI-App",
            "Accept": "application/vnd.github+json"
        }

        async with session.get(user_url, headers=api_headers) as resp:
            if resp.status != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to fetch user profile from GitHub"
                )
            user_data = await resp.json()

    print(user_data)
    return {
        "email": user_data["email"],
        "name": user_data["name"],
        "picture": user_data["avatar_url"],
    }
