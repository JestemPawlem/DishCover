import uuid

from fastapi import status
from fastapi.testclient import TestClient


def _get_auth_headers(client: TestClient) ->dict[str, str]:
    email = f'user_{uuid.uuid4().hex[:8]}@example.com'
    password = 'SecurePassword123'
    client.post('/auth/register', json={'email': email, 'password': password})
    response = client.post('/auth/login', json={'email': email, 'password': password})
    token = response.json()['access_token']
    return {'Authorization': f'Bearer {token}'}


def test_onboarding_and_is_liked_field(client: TestClient) -> None:
    headers = _get_auth_headers(client)

    unauth_result = client.get('/recipes/onboarding?limit=5')
    assert unauth_result.status_code == status.HTTP_200_OK
    unauth_recipes = unauth_result.json()
    assert len(unauth_recipes) > 0
    assert all(recipe['is_liked'] is False for recipe in unauth_recipes)
    target_recipe_id = unauth_recipes[0]['id']

    client.post(f'/recipes/{target_recipe_id}/like', headers=headers)

    auth_result = client.get('/recipes/onboarding?limit=5', headers=headers)
    assert auth_result.status_code == status.HTTP_200_OK
    auth_recipes = auth_result.json()
    liked_recipe = next(r for r in auth_recipes if r['id'] == target_recipe_id)
    assert liked_recipe['is_liked'] is True


def test_search_recipes_flow(client: TestClient) -> None:
    headers = _get_auth_headers(client)

    recipes = client.get('/recipes/onboarding?limit=1').json()
    assert len(recipes) > 0
    recipe_name = recipes[0]['name']
    target_id = recipes[0]['id']

    client.post(f'/recipes/{target_id}/like', headers=headers)

    query = recipe_name[:4]
    search_result = client.get(f'/recipes/search?q={query}&limit=10', headers=headers)
    assert search_result.status_code == status.HTTP_200_OK
    results = search_result.json()
    assert len(results) > 0
    assert any(r['id'] == target_id and r['is_liked'] is True for r in results)

    empty_result = client.get('/recipes/search?q=xyznonexistentpattern12345')
    assert empty_result.status_code == status.HTTP_200_OK
    assert empty_result.json() == []


def test_get_recipe_and_similar_flow(client: TestClient) -> None:
    headers = _get_auth_headers(client)

    recipes = client.get('/recipes/onboarding?limit=1').json()
    assert len(recipes) > 0
    target_recipe_id = recipes[0]['id']

    client.post(f'/recipes/{target_recipe_id}/like', headers=headers)

    recipe_result = client.get(f'/recipes/{target_recipe_id}', headers=headers)
    assert recipe_result.status_code == status.HTTP_200_OK
    recipe_data = recipe_result.json()
    assert recipe_data['id'] == target_recipe_id
    assert recipe_data['is_liked'] is True
    assert 'ingredients' in recipe_data
    assert 'steps' in recipe_data

    similar_result = client.get(f'/recipes/{target_recipe_id}/similar?limit=3', headers=headers)
    assert similar_result.status_code == status.HTTP_200_OK
    similar_data = similar_result.json()
    assert len(similar_data) > 0
    assert all(r['id'] != target_recipe_id for r in similar_data)

    not_found_recipe = client.get('/recipes/21374206967')
    assert not_found_recipe.status_code == status.HTTP_404_NOT_FOUND

    not_found_similar = client.get('/recipes/21374206967/similar')
    assert not_found_similar.status_code == status.HTTP_404_NOT_FOUND


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