import pytest


def test_upload_route_present():
    """create_app() (legacy full UI)에서 /upload 엔드포인트가 존재하는지 확인합니다.

    - 테스트는 서버를 띄우지 않고 Flask의 test_client로 요청하여 404가 아닌 응답을 받는지 확인합니다.
    - CI 이전에 개발 환경에서 빠르게 검증하기 위한 안전한 테스트입니다.
    """
    from src.web.app import create_app

    app = create_app()
    client = app.test_client()

    resp = client.get('/upload')

    # 기대: 404가 아닌 정상적인 응답 (템플릿 렌더링 또는 리다이렉트)
    assert resp.status_code != 404, 'Expected /upload to be registered in the full UI app'
