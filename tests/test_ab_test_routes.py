import pytest
from app import create_app
from main.data import transactions

@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    return app

def test_abtest_requires_login(client):
    resp = client.get('/analysis/abtest')
    assert resp.status_code == 302
    assert '/login' in resp.headers['Location']

def test_abtest_page_after_login(client):
    # login
    client.post('/register', data={'email':'t@t.com','password':'pw'})
    client.post('/login',    data={'email':'t@t.com','password':'pw'})

    # seed some data
    transactions.clear()
    transactions.extend([
        {'id':1,'date':'2025-06-01','amount':100},
        {'id':2,'date':'2025-06-02','amount':200},
        {'id':3,'date':'2025-06-03','amount':300},
        {'id':4,'date':'2025-06-04','amount':400},
    ])

    resp = client.get('/analysis/abtest')
    assert resp.status_code == 200
    page = resp.get_data(as_text=True)

    # one half in groupA, one half in groupB
    assert '100' in page or '200' in page   # cohort A values
    assert '300' in page or '400' in page   # cohort B values
    # p-value should be rendered (even if very small)
    assert 'P-value' in page
