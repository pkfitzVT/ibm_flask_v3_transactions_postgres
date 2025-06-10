import pytest
from app import create_app

@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    return app

def test_analysis_requires_login(client):
    """Unauthenticated GET /analysis must redirect to login."""
    resp = client.get('/analysis')
    assert resp.status_code == 302
    assert '/login' in resp.headers['Location']

def test_regression_route_requires_login(client):
    """Unauthenticated GET /analysis/regression must redirect."""
    resp = client.get('/analysis/regression')
    assert resp.status_code == 302
    assert '/login' in resp.headers['Location']

def test_abtest_route_requires_login(client):
    """Unauthenticated GET /analysis/abtest must redirect."""
    resp = client.get('/analysis/abtest')
    assert resp.status_code == 302
    assert '/login' in resp.headers['Location']

def test_analysis_pages_after_login(client):
    """Authenticated access returns 200 for analysis pages."""
    # register & login
    client.post('/register', data={'email':'x@x.com','password':'pw'})
    client.post('/login',    data={'email':'x@x.com','password':'pw'})

    for path in ('/analysis', '/analysis/regression', '/analysis/abtest'):
        resp = client.get(path)
        assert resp.status_code == 200, f"{path} failed"
        # spot-check that the page contains its title
        if path == '/analysis':
            assert 'Data Analysis' in resp.get_data(as_text=True)
        elif path.endswith('regression'):
            assert 'Regression Results' in resp.get_data(as_text=True)
        else:
            assert 'A/B Test Results' in resp.get_data(as_text=True)
