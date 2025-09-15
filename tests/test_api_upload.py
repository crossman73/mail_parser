import io
import os

from src.web.app_factory import create_app


def test_upload_get_and_post(tmp_path, monkeypatch):
    app = create_app()
    client = app.test_client()

    # Ensure uploads dir is isolated
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    app.config['UPLOAD_FOLDER'] = str(upload_dir)

    # GET should return empty list
    r = client.get('/api/upload')
    assert r.status_code == 200
    j = r.get_json()
    assert j['success'] is True
    assert 'files' in j

    # POST a small allowed file
    data = {'file': (io.BytesIO(b'abc'), 'sample.txt')}
    r = client.post('/api/upload', data=data,
                    content_type='multipart/form-data')
    assert r.status_code == 200
    j = r.get_json()
    assert j['success'] is True
    assert j['filename'].endswith('.txt')
    assert os.path.exists(os.path.join(str(upload_dir), j['filename']))

    # POST a disallowed extension
    data = {'file': (io.BytesIO(b'abc'), 'bad.exe')}
    r = client.post('/api/upload', data=data,
                    content_type='multipart/form-data')
    assert r.status_code == 400
    j = r.get_json()
    assert j['success'] is False
    assert '허용되지 않는' in j['message'] or '허용' in j['message']


def test_upload_with_token(tmp_path):
    app = create_app()
    client = app.test_client()

    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    app.config['UPLOAD_FOLDER'] = str(upload_dir)
    app.config['UPLOAD_API_TOKEN'] = 'secrettoken'

    # No auth header -> 401
    data1 = {'file': (io.BytesIO(b'abc'), 'sample2.txt')}
    r = client.post('/api/upload', data=data1,
                    content_type='multipart/form-data')
    assert r.status_code == 401

    # Wrong token -> 401
    data2 = {'file': (io.BytesIO(b'abc'), 'sample2.txt')}
    r = client.post('/api/upload', data=data2, content_type='multipart/form-data',
                    headers={'Authorization': 'Bearer wrong'})
    assert r.status_code == 401

    # Correct token -> 200
    data3 = {'file': (io.BytesIO(b'abc'), 'sample2.txt')}
    r = client.post('/api/upload', data=data3, content_type='multipart/form-data',
                    headers={'Authorization': 'Bearer secrettoken'})
    assert r.status_code == 200
    j = r.get_json()
    assert j['success'] is True
