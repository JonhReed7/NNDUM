from pydantic import BaseModel, ConfigDict, EmailStr, Field, computed_field


class CredentialBase(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserRegister(CredentialBase):
    username: str = Field(min_length=2, max_length=64)
    first_name: str | None = Field(default=None, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)


class UserLogin(CredentialBase):
    pass


class OAuthCodeRequest(BaseModel):
    code: str = Field(min_length=1)


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: EmailStr | None = None
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None
    github_access_token: str | None = Field(default=None, exclude=True)

    @computed_field
    @property
    def has_github_connected(self) -> bool:
        return bool(self.github_access_token)


class UserProfileUpdate(BaseModel):
    first_name: str | None = Field(default=None, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)
    username: str | None = Field(default=None, min_length=2, max_length=64)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead