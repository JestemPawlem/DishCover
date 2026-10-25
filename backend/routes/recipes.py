from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status
)
import psycopg
from psycopg.errors import ForeignKeyViolation
from psycopg.rows import dict_row

from core.database import get_db
from core.security import get_current_user, get_current_user_optional
from models.recipe import (
    Recipe,
    RecipeSummary,
    LikeResponse
)
from models.user import UserDB


router = APIRouter(prefix='/recipes', tags=['recipes'])


@router.get('/onboarding', response_model=list[RecipeSummary])
def get_onboarding_recipes(connection: Annotated[psycopg.Connection, Depends(get_db)],
                           current_user: Annotated[UserDB | None, Depends(get_current_user_optional)],
                           limit: Annotated[int, Query(ge=1, le=50)] = 12) -> list[RecipeSummary]:
    user_id = current_user.id if current_user else None

    with connection.cursor(row_factory=dict_row) as cursor:
        cursor.execute(
            '''
            SELECT
                r.id, r.name, r.minutes, r.description, r.like_count,
                CASE
                    WHEN %(user_id)s::bigint IS NULL THEN FALSE
                    ELSE EXISTS(
                        SELECT 1 FROM user_recipe_interactions
                        WHERE user_id = %(user_id)s AND recipe_id = r.id
                    )
                END AS is_liked
            FROM recipes r
            ORDER BY r.like_count DESC
            LIMIT %(limit)s;
            ''',
            {'user_id': user_id, 'limit': limit}
        )
        rows = cursor.fetchall()

    return [RecipeSummary(**row) for row in rows]


@router.get('/recommendations', response_model=list[RecipeSummary])
def get_recommendations(current_user: Annotated[UserDB, Depends(get_current_user)],
                        connection: Annotated[psycopg.Connection, Depends(get_db)],
                        limit: Annotated[int, Query(ge=1, le=50)] = 12) -> list[RecipeSummary]:
    with connection.cursor(row_factory=dict_row) as cursor:
        cursor.execute(
            '''
            SELECT avg(r.embedding) AS centroid
            FROM user_recipe_interactions uri
            JOIN recipes r ON uri.recipe_id = r.id
            WHERE uri.user_id = %(user_id)s;
            ''',
            {'user_id': current_user.id}
        )
        result = cursor.fetchone()
        user_centroid = result['centroid'] if result else None

        if user_centroid is None:
            cursor.execute(
                '''
                SELECT id, name, minutes, description, like_count
                FROM recipes
                ORDER BY like_count DESC
                LIMIT %(limit)s;
                ''',
                {'limit': limit}
            )
            rows = cursor.fetchall()
            return [RecipeSummary(**row) for row in rows]

        cursor.execute(
            '''
            SELECT r.id, r.name, r.minutes, r.description, r.like_count,
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

    return [RecipeSummary(**row) for row in rows]


@router.get('/search', response_model=list[RecipeSummary])
def search_recipes(q: str,
                   connection: Annotated[psycopg.Connection, Depends(get_db)],
                   current_user: Annotated[UserDB | None, Depends(get_current_user_optional)],
                   limit: Annotated[int, Query(ge=1, le=50)] = 20,
                   offset: Annotated[int, Query(ge=0)] = 0) -> list[RecipeSummary]:
    user_id = current_user.id if current_user else None

    with connection.cursor(row_factory=dict_row) as cursor:
        cursor.execute(
            '''
            SELECT
                r.id, r.name, r.minutes, r.description, r.like_count,
                CASE
                    WHEN %(user_id)s::bigint IS NULL THEN FALSE
                    ELSE EXISTS(
                        SELECT 1 FROM user_recipe_interactions
                        WHERE user_id = %(user_id)s AND recipe_id = r.id
                    )
                END AS is_liked
            FROM recipes r
            WHERE r.name %% %(q)s OR r.name ILIKE %(like_q)s
            ORDER BY similarity(r.name, %(q)s) DESC, r.like_count DESC
            LIMIT %(limit)s OFFSET %(offset)s;
            ''',
            {'user_id': user_id, 'q': q, 'like_q': f'%{q}%', 'limit': limit, 'offset': offset}
        )
        rows = cursor.fetchall()

    return [RecipeSummary(**row) for row in rows]


@router.get('/{recipe_id}', response_model=Recipe)
def get_recipe(recipe_id: int,
               connection: Annotated[psycopg.Connection, Depends(get_db)],
               current_user: Annotated[UserDB | None, Depends(get_current_user_optional)]) -> Recipe:
    user_id = current_user.id if current_user else None
    
    with connection.cursor(row_factory=dict_row) as cursor:
        cursor.execute(
            '''
            SELECT
                r.id, r.name, r.minutes, r.description, r.like_count, r.ingredients, r.steps,
                CASE
                    WHEN %(user_id)s::bigint IS NULL THEN FALSE
                    ELSE EXISTS(
                        SELECT 1 FROM user_recipe_interactions
                        WHERE user_id = %(user_id)s AND recipe_id = r.id
                    )
                END AS is_liked
            FROM recipes r
            WHERE r.id = %(recipe_id)s;
            ''',
            {'recipe_id': recipe_id, 'user_id': user_id}
        )
        row = cursor.fetchone()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Recipe with id {recipe_id} not found'
        )

    return Recipe(**row)


@router.get('/{recipe_id}/similar', response_model=list[RecipeSummary])
def get_similar_recipes(recipe_id: int,
                        connection: Annotated[psycopg.Connection, Depends(get_db)],
                        current_user: Annotated[UserDB | None, Depends(get_current_user_optional)],
                        limit: Annotated[int, Query(ge=1, le=20)] = 6) -> list[RecipeSummary]:
    user_id = current_user.id if current_user else None

    with connection.cursor(row_factory=dict_row) as cursor:
        cursor.execute('SELECT embedding FROM recipes WHERE id = %s;', (recipe_id,))
        target = cursor.fetchone()

        if not target:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f'Recipe with id {recipe_id} not found'
            )

        cursor.execute(
            '''
            SELECT
                r.id, r.name, r.minutes, r.description, r.like_count,
                CASE
                    WHEN %(user_id)s::bigint IS NULL THEN FALSE
                    ELSE EXISTS(
                        SELECT 1 FROM user_recipe_interactions
                        WHERE user_id = %(user_id)s AND recipe_id = r.id
                    )
                END AS is_liked
            FROM recipes r
            WHERE r.id != %(recipe_id)s
            ORDER BY r.embedding <=> %(target_emb)s
            LIMIT %(limit)s
            ''',
            {'user_id': user_id, 'recipe_id': recipe_id, 'target_emb': target['embedding'], 'limit': limit}
        )
        rows = cursor.fetchall()

    return [RecipeSummary(**row) for row in rows]


@router.post('/{recipe_id}/like', response_model=LikeResponse)
def toggle_like_recipe(recipe_id: int,
                       current_user: Annotated[UserDB, Depends(get_current_user)],
                       connection: Annotated[psycopg.Connection, Depends(get_db)]) -> LikeResponse:
    with connection.cursor(row_factory=dict_row) as cursor:
        try:
            cursor.execute(
                '''
                WITH deleted AS (
                    DELETE FROM user_recipe_interactions
                    WHERE user_id = %(user_id)s AND recipe_id = %(recipe_id)s
                    RETURNING 1
                ),
                inserted AS (
                    INSERT INTO user_recipe_interactions (user_id, recipe_id)
                    SELECT %(user_id)s, %(recipe_id)s
                    WHERE NOT EXISTS (SELECT 1 FROM deleted)
                    ON CONFLICT (user_id, recipe_id) DO NOTHING
                    RETURNING 1
                ),
                updated AS (
                    UPDATE recipes
                    SET like_count = CASE
                        WHEN EXISTS (SELECT 1 FROM deleted) THEN like_count - 1
                        WHEN EXISTS (SELECT 1 FROM inserted) THEN like_count + 1
                        ELSE like_count
                    END
                    WHERE id = %(recipe_id)s
                    RETURNING 1
                )
                SELECT
                    EXISTS(SELECT 1 FROM inserted) AS liked,
                    EXISTS(SELECT 1 FROM updated) AS recipe_exists;
                ''',
                {'user_id': current_user.id, 'recipe_id': recipe_id}
            )
            row = cursor.fetchone()
            connection.commit()

            if not row or not row['recipe_exists']:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f'Recipe with id {recipe_id} not found'
                )

            return LikeResponse(liked=row['liked'])

        except ForeignKeyViolation:
            connection.rollback()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f'Recipe with id {recipe_id} not found'
            )