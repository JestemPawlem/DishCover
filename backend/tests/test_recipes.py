import uuid

from fastapi import status
from fastapi.testclient import TestClient


def _get_auth_headers(client: TestClient) -> dict[str, str]:
    email = f'user_{uuid.uuid4().hex[:8]}@example.com'
    password = 'SecurePassword123'
    client.post('/auth/register', json={'email': email, 'password': password})
    response = client.post('/auth/login', json={'email': email, 'password': password})
    token = response.json()['access_token']
    return {'Authorization': f'Bearer {token}'}


def test_recipes_recommendation_and_like_flow(client: TestClient) -> None:
    headers = _get_auth_headers(client)

    onboarding_result = client.get('/recipes/onboarding?limit=5')
    assert onboarding_result.status_code == status.HTTP_200_OK
    recipes = onboarding_result.json()
    assert len(recipes) > 0
    target_recipe_id = recipes[0]['id']

    initial_recs_result = client.get('/recipes/recommendations?limit=5', headers=headers)
    assert initial_recs_result.status_code == status.HTTP_200_OK
    initial_recs = initial_recs_result.json()
    assert len(initial_recs) > 0
    assert all(r['similarity'] is None for r in initial_recs)

    unauth_like_result = client.post(f'/recipes/{target_recipe_id}/like')
    assert unauth_like_result.status_code == status.HTTP_401_UNAUTHORIZED

    like_result = client.post(f'/recipes/{target_recipe_id}/like', headers=headers)
    assert like_result.status_code == status.HTTP_200_OK
    assert like_result.json()['liked'] is True

    updated_recs_result = client.get('/recipes/recommendations?limit=10', headers=headers)
    assert updated_recs_result.status_code == status.HTTP_200_OK
    updated_recs = updated_recs_result.json()
    rec_ids = [rec['id'] for rec in updated_recs]
    assert target_recipe_id not in rec_ids
    assert all(rec['similarity'] is not None for rec in updated_recs)

    unlike_result = client.post(f'/recipes/{target_recipe_id}/like', headers=headers)
    assert unlike_result.status_code == status.HTTP_200_OK
    assert unlike_result.json()['liked'] is False

    not_found_result = client.post('/recipes/21374206967/like', headers=headers)
    assert not_found_result.status_code == status.HTTP_404_NOT_FOUND