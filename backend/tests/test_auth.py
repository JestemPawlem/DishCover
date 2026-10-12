import uuid

from fastapi import status
from fastapi.testclient import TestClient


def test_registration_and_login_flow(client: TestClient) -> None:
    email = f'user_{uuid.uuid4().hex[:8]}@example.com'
    password = 'SecurePassword123'

    # Register
    result = client.post(
        '/auth/register',
        json={'email': email, 'password': password}
    )
    assert result.status_code == status.HTTP_201_CREATED
    register_data = result.json()
    assert register_data['email'] == email
    assert 'id' in register_data

    # Duplicate email
    result = client.post(
        '/auth/register',
        json={'email': email, 'password': 'WrongPassword321'}
    )
    assert result.status_code == status.HTTP_409_CONFLICT

    # Invalid password
    result = client.post(
        '/auth/login',
        json={'email': email, 'password': 'WrongPassword321'}
    )
    assert result.status_code == status.HTTP_401_UNAUTHORIZED

    # Successful login
    result = client.post(
        '/auth/login',
        json={'email': email, 'password': password}
    )
    assert result.status_code == status.HTTP_200_OK
    token_data = result.json()
    assert 'access_token' in token_data