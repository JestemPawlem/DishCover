from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)
import psycopg
from psycopg.errors import UniqueViolation

from core.config import get_settings
from core.database import get_db
from core.exceptions import credentials_exception
from core.security import create_access_token, hash_password, verify_password
from models.user import UserCreate, UserLogin, UserResponse
from models.token import Token


settings = get_settings()


router = APIRouter(prefix='/auth', tags=['auth'])


@router.post('/register', response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user_data: UserCreate,
                  connection: Annotated[psycopg.Connection, Depends(get_db)]) -> UserResponse:
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                '''
                INSERT INTO users (email, password_hash)
                VALUES (%s, %s)
                RETURNING id, email, created_at;
                ''',
                (user_data.email, hash_password(user_data.password))
            )
            id, email, created_at = cursor.fetchone()
            connection.commit()

            return {
                'id': id,
                'email': email,
                'created_at': created_at
            }
        
    except UniqueViolation:
        connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='Email already registered.'
        )
    except psycopg.Error:
        connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Database error occurred during registration.'
        )


@router.post('/login', response_model=Token)
def login_user(credentials: UserLogin,
               connection: Annotated[psycopg.Connection, Depends(get_db)]) -> Token:
    with connection.cursor() as cursor:
        cursor.execute(
            '''
            SELECT id, password_hash
            FROM users
            WHERE email = %s
            ''',
            (credentials.email,)
        )
        row = cursor.fetchone()

    if row:
        user_id, password_hash = row
    else:
        user_id, password_hash = None, settings.dummy_password_hash

    is_valid = verify_password(credentials.password, password_hash)
    if not row or not is_valid:
        raise credentials_exception

    access_token = create_access_token(user_id)
    return Token(
        access_token=access_token,
        token_type='bearer'
    )