from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
import psycopg
from psycopg.errors import ForeignKeyViolation
from psycopg.rows import dict_row

from core.database import get_db
from core.security import get_current_user
from models.recipe import (
    RecipeSummary,
    RecipeRecommendation,
    LikeResponse
)
from models.user import UserDB


router = APIRouter(prefix='/recipes', tags=['recipes'])


@router.get('/onboarding', response_model=list[RecipeSummary])
def get_onboarding_recipes(connection: Annotated[psycopg.Connection, Depends(get_db)],
                           limit: int = 12) -> list[RecipeSummary]:
    with connection.cursor(row_factory=dict_row) as cursor:
        cursor.execute(
            '''
            SELECT id, name, minutes, description
            FROM recipes
            LIMIT %s
            ''',
            (limit,)
        )
        rows = cursor.fetchall()

    return [RecipeSummary(**row) for row in rows]


@router.get('/recommendations', response_model=list[RecipeRecommendation])
def get_recommendations(current_user: Annotated[UserDB, Depends(get_current_user)],
                        connection: Annotated[psycopg.Connection, Depends(get_db)],
                        limit: int = 10) -> list[RecipeRecommendation]:
    with connection.cursor(row_factory=dict_row) as cursor:
        cursor.execute(
            '''
            SELECT avg(r.embedding) AS centroid
            FROM user_recipe_interactions uri
            JOIN recipes r ON uri.recipe_id = r.id
            WHERE uri.user_id = %s;
            ''',
            (current_user.id,)
        )
        result = cursor.fetchone()
        user_centroid = result['centroid'] if result else None

        if user_centroid is None:
            cursor.execute(
                '''
                SELECT id, name, minutes, description
                FROM recipes
                LIMIT %s;
                ''',
                (limit,)
            )
            rows = cursor.fetchall()
            return [RecipeRecommendation(**row, similarity=None) for row in rows]

        cursor.execute(
            '''
            SELECT r.id, r.name, r.minutes, r.description,
                ROUND((1 - (r.embedding <=> %s))::numeric, 4) AS similarity
            FROM recipes r
            WHERE r.id NOT IN (
                SELECT recipe_id FROM user_recipe_interactions WHERE user_id = %s
            )
            ORDER BY r.embedding <=> %s
            LIMIT %s;
            ''',
            (user_centroid, current_user.id, user_centroid, limit)
        )
        rows = cursor.fetchall()

    return [RecipeRecommendation(**row) for row in rows]


@router.post('/{recipe_id}/like')
def toggle_like_recipe(recipe_id: int,
                       current_user: Annotated[UserDB, Depends(get_current_user)],
                       connection: Annotated[psycopg.Connection, Depends(get_db)]) -> LikeResponse:
    with connection.cursor() as cursor:
        cursor.execute(
            '''
            DELETE FROM user_recipe_interactions
            WHERE user_id = %s AND recipe_id = %s
            RETURNING 1;
            ''',
            (current_user.id, recipe_id)
        )
        deleted = cursor.fetchone()

        if deleted:
            connection.commit()
            return LikeResponse(liked=False)

        try:
            cursor.execute(
                '''
                INSERT INTO user_recipe_interactions (user_id, recipe_id)
                VALUES (%s, %s)
                ON CONFLICT (user_id, recipe_id) DO NOTHING
                ''',
                (current_user.id, recipe_id)
            )
            connection.commit()
            return LikeResponse(liked=True)
        except ForeignKeyViolation:
            connection.rollback()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f'Recipe with id {recipe_id} not found'
            )