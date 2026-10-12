from typing import Annotated

from fastapi import APIRouter, Depends

from core.security import get_current_user
from models.user import UserDB, UserResponse


router = APIRouter(prefix='/users', tags=['users'])


@router.get('/me', response_model=UserResponse)
def read_current_user(current_user: Annotated[UserDB, Depends(get_current_user)]) -> UserResponse:
    return current_user