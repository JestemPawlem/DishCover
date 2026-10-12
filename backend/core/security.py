from datetime import datetime, timedelta, timezone
from typing import Annotated

import bcrypt
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
import jwt
import psycopg
from pydantic import SecretStr

from core.config import get_settings
from core.database import get_db
from core.exceptions import credentials_exception
from models.user import UserDB


settings = get_settings()


def hash_password(password: SecretStr) -> str:
    raw_password = password.get_secret_value().encode('utf-8')
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(raw_password, salt).decode('utf-8')


def verify_password(plain_password: SecretStr, hashed_password: str) -> bool:
    raw_password = plain_password.get_secret_value().encode('utf-8')
    return bcrypt.checkpw(raw_password, hashed_password.encode('utf-8'))


def create_access_token(user_id: int) -> str:
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {
        'sub': str(user_id),
        'iat': now,
        'exp': expire
    }

    return jwt.encode(
        payload,
        settings.jwt_secret_key.get_secret_value(),
        algorithm=settings.jwt_algorithm
    )


oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/auth/login')

def get_current_user(token: Annotated[str, Depends(oauth2_scheme)],
                     connection: Annotated[psycopg.Connection, Depends(get_db)]) -> UserDB:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key.get_secret_value(),
            algorithms=[settings.jwt_algorithm]
        )
        user_id: str | None = payload.get('sub')
        if user_id is None:
            raise credentials_exception
        user_id = int(user_id)

    except (jwt.PyJWTError, ValueError):
        raise credentials_exception

    with connection.cursor() as cursor:
        cursor.execute(
            '''
            SELECT id, email, password_hash, created_at
            FROM users
            WHERE id = %s;
            ''',
            (user_id,)
        )
        row = cursor.fetchone()

    if row is None:
        raise credentials_exception

    user_id, email, password_hash, created_at = row
    return UserDB(
        id=user_id,
        email=email,
        password_hash=password_hash,
        created_at=created_at
    )