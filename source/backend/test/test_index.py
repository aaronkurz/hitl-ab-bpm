import pytest

from bprl import create_app


@pytest.fixture
def client():
    app = create_app.create_app()
    app.config.update({'TESTING': True})

    with app.test_client() as client:
        yield client


def test_true():
    assert True is True


def test_index(client):
    response = client.get('/')
    assert b'Hello World!!!' in response.data
