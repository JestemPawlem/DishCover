from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    SecretStr
)


class UserBase(BaseModel):
    email: EmailStr

    @field_validator('email')
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return value.lower()


class UserCreate(UserBase):
    password: SecretStr = Field(min_length=8, max_length=72)

    @field_validator('password')
    @classmethod
    def validate_password_complexity(cls, value: SecretStr) -> SecretStr:
        raw = value.get_secret_value()
        if not any(char.isdigit() for char in raw):
            raise ValueError('Password must contain at least one digit.')
        if not any(char.isalpha() for char in raw):
            raise ValueError('Password must contain at least one letter.')
        return value


class UserLogin(UserBase):
    password: SecretStr


class UserResponse(UserBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserDB(UserBase):
    id: int
    password_hash: str
    created_at: datetime