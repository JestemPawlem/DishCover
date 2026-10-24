from typing import Annotated

from fastapi import APIRouter, Depends
import psycopg
from psycopg.rows import dict_row

from core.database import get_db
from core.security import get_current_user
from models.recipe import RecipeSummary
from models.user import UserDB, UserResponse


router = APIRouter(prefix='/users', tags=['users'])


@router.get('/me', response_model=UserResponse)
def read_current_user(current_user: Annotated[UserDB, Depends(get_current_user)]) -> UserResponse:
    return current_user


@router.get('/me/liked', response_model=list[RecipeSummary])
def get_current_user_liked_recipes(current_user: Annotated[UserDB, Depends(get_current_user)],
                                   connection: Annotated[psycopg.Connection, Depends(get_db)],
                                   limit: int = 20,
                                   offset: int = 0) -> list[RecipeSummary]:
    with connection.cursor(row_factory=dict_row) as cursor:
        cursor.execute(
            '''
            SELECT r.id, r.name, r.minutes, r.description, r.like_count
            FROM user_recipe_interactions uri
            JOIN recipes r ON uri.recipe_id = r.id
            WHERE uri.user_id = %s
            ORDER BY uri.created_at DESC
            LIMIT %s OFFSET %s;
            ''',
            (current_user.id, limit, offset)
        )
        rows = cursor.fetchall()

    return [RecipeSummary(**row) for row in rows]