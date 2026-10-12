from fastapi import HTTPException, status


credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail='Invalid email or password.',
    headers={'WWW-Authenticate': 'Bearer'}
)