import uuid
from fastapi import status
from fastapi.testclient import TestClient


def test_current_user_flow(client: TestClient) -> None:
    email = f'user_{uuid.uuid4().hex[:8]}@example.com'
    password = 'SecurePassword123'

    client.post(
        '/auth/register',
        json={'email': email, 'password': password}
    )
    login_result = client.post(
        '/auth/login',
        json={'email': email, 'password': password}
    )
    token = login_result.json()['access_token']

    unauth_result = client.get('/users/me')
    assert unauth_result.status_code == status.HTTP_401_UNAUTHORIZED

    auth_result = client.get(
        '/users/me',
        headers={'Authorization': f'Bearer {token}'}
    )
    assert auth_result.status_code == status.HTTP_200_OK
    data = auth_result.json()
    assert data['email'] == email
    assert 'id' in data
    assert 'created_at' in data