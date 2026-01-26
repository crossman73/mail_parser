import time

import requests

# 여러 엔드포인트 테스트
test_cases = [
    {
        "endpoint": "/evidence",
        "method": "GET",
        "status_code": 200,
        "response_time_ms": 50,
        "success": True,
        "error_message": None,
        "request_data": "{}",
        "response_data": '{"items": []}'
    },
    {
        "endpoint": "/evidence_management",
        "method": "GET",
        "status_code": 200,
        "response_time_ms": 120,
        "success": True,
        "error_message": None,
        "request_data": "{}",
        "response_data": '{"total": 0}'
    },
    {
        "endpoint": "/api/docs",
        "method": "GET",
        "status_code": 200,
        "response_time_ms": 80,
        "success": True,
        "error_message": None,
        "request_data": "{}",
        "response_data": '{"endpoints": []}'
    },
    {
        "endpoint": "/api/evidence_categories",
        "method": "GET",
        "status_code": 200,
        "response_time_ms": 35,
        "success": True,
        "error_message": None,
        "request_data": "{}",
        "response_data": '{"categories": []}'
    },
    {
        "endpoint": "/nonexistent",
        "method": "GET",
        "status_code": 404,
        "response_time_ms": 15,
        "success": False,
        "error_message": "HTTP 404",
        "request_data": "{}",
        "response_data": '{"error": "Not Found"}'
    }
]

success_count = 0
fail_count = 0

for i, test_data in enumerate(test_cases, 1):
    try:
        response = requests.post(
            "http://127.0.0.1:5000/api/test-result",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )

        if response.status_code == 201:
            success_count += 1
            print(f"✅ Test {i}/{len(test_cases)}: {test_data['endpoint']} 저장 성공")
        elif response.status_code == 404:
            fail_count += 1
            print(f"⚠️ Test {i}/{len(test_cases)}: {test_data['endpoint']} - Endpoint not in DB (expected)")
        else:
            fail_count += 1
            print(f"❌ Test {i}/{len(test_cases)}: {test_data['endpoint']} - {response.status_code}")

        time.sleep(0.1)  # 부하 방지

    except Exception as e:
        fail_count += 1
        print(f"❌ Test {i}/{len(test_cases)}: 오류 - {e}")

print(f"\n총 {len(test_cases)}개 테스트: {success_count}개 성공, {fail_count}개 실패/스킵")
