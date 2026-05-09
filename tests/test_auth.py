def test_register_and_login(client):
    payload = {
        'username': 'testuser',
        'email': 'testuser@example.com',
        'password': 'Password123'
    }

    register_response = client.post('/api/auth/register', json=payload)
    assert register_response.status_code == 201
    assert 'access_token' in register_response.json

    login_response = client.post(
        '/api/auth/login',
        json={'identifier': payload['username'], 'password': payload['password']}
    )
    assert login_response.status_code == 200
    assert 'access_token' in login_response.json

    token = login_response.json['access_token']
    profile_response = client.get(
        '/api/auth/profile',
        headers={'Authorization': f'Bearer {token}'}
    )
    assert profile_response.status_code == 200
    assert profile_response.json['username'] == payload['username']
    assert profile_response.json['email'] == payload['email']


def test_login_invalid_credentials(client):
    invalid_response = client.post(
        '/api/auth/login',
        json={'identifier': 'notfound', 'password': 'wrong'}
    )
    assert invalid_response.status_code == 401
    assert invalid_response.json['error'] == 'Invalid credentials'
