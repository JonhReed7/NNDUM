from pydantic import EmailStr, BaseModel, Field, ConfigDict


class CredentialBase(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

class UserRegister(CredentialBase):
    username: str
    first_name: str | None = None
    last_name: str | None = None

class UserLogin(CredentialBase):
    pass

class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    email: EmailStr
    first_name: str | None = None
    last_name: str | None = None
    username: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserRead


    
