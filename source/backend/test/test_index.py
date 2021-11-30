import pytest

from bprl import app as flask_app


@pytest.fixture
def client():
    app = flask_app.app
    app.config.update({'TESTING': True})

    with app.test_client() as client:
        return client


def test_true():
    assert True is True


def test_index(client):

    response = client.get('/')
    print(response.data)
    assert b'Hello World!!!' in response.data
