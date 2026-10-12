from collections.abc import Iterator

from fastapi.testclient import TestClient
import pytest

from main import app


@pytest.fixture(scope='session')
def client() ->Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client