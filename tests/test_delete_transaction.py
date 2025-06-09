import pytest
from app import create_app
from main.data import transactions

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_delete_requires_login(client):
    """Unauthenticated GET /delete/1 must redirect to login."""
    resp = client.get('/delete/1')
    assert resp.status_code == 302
    assert '/login' in resp.headers['Location']

def test_delete_transaction(client):
    """POST or GET /delete/1 removes the transaction from in-memory data."""
    # 1) Log in
    client.post('/register', data={'email':'u@u.com','password':'pw'})
    client.post('/login',    data={'email':'u@u.com','password':'pw'})

    # 2) Seed one transaction
    transactions.clear()
    transactions.append({'id':1, 'date':'2025-06-10', 'amount':100.00})
    assert len(transactions) == 1

    # 3) Invoke delete
    resp = client.get('/delete/1', follow_redirects=False)

    # 4) Verify it redirected back to /transactions
    assert resp.status_code == 302
    assert '/transactions' in resp.headers['Location']

    # 5) Confirm the in-memory list is now empty
    assert len(transactions) == 0
