from services.netease_service import netease_service


def test_create_note_with_mocked_api(client, monkeypatch):
    registration = client.post(
        '/api/auth/register',
        json={
            'username': 'noteuser',
            'email': 'noteuser@example.com',
            'password': 'Password123'
        }
    )
    assert registration.status_code == 201
    token = registration.json['access_token']

    def fake_get_song_detail(song_id):
        return {
            'id': song_id,
            'netease_song_id': song_id,
            'title': 'Mock Song',
            'artist': 'Mock Artist',
            'album': 'Mock Album',
            'album_cover_url': 'https://example.com/mock.jpg',
            'duration': 210000
        }

    monkeypatch.setattr(netease_service, 'get_song_detail', fake_get_song_detail)

    create_response = client.post(
        '/api/notes',
        headers={'Authorization': f'Bearer {token}'},
        json={
            'netease_song_id': '12345',
            'content': 'This is a test note',
            'timestamp': 1000,
            'is_public': False
        }
    )

    assert create_response.status_code == 201
    assert create_response.json['note']['song']['netease_song_id'] == '12345'

    list_response = client.get(
        '/api/notes',
        headers={'Authorization': f'Bearer {token}'}
    )
    assert list_response.status_code == 200
    assert list_response.json['total'] == 1
    assert list_response.json['notes'][0]['content'] == 'This is a test note'
