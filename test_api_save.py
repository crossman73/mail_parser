import json

import requests

# 테스트 데이터
test_data = {
    "endpoint": "/evidence",
    "method": "GET",
    "status_code": 200,
    "response_time_ms": 45,
    "success": True,
    "error_message": None,
    "request_data": "{}",
    "response_data": '{"status": "ok", "data": []}'
}

# POST 요청
try:
    response = requests.post(
        "http://127.0.0.1:5000/api/test-result",
        json=test_data,
        headers={"Content-Type": "application/json"}
    )

    print(f"응답 코드: {response.status_code}")
    print(f"응답 내용: {response.json()}")

    if response.status_code == 201:
        print("\n✅ 테스트 결과 저장 성공!")
    else:
        print(f"\n❌ 실패: {response.status_code}")

except Exception as e:
    print(f"❌ 오류: {e}")
