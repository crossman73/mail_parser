"""
시스템 테스트 초기 데이터 설정
"""
import sys
from pathlib import Path

# 프로젝트 루트 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.email_db import test_manager


def initialize_default_tests():
    """기본 테스트 추가"""
    
    default_tests = [
        {
            'test_key': 'test_web_app',
            'test_name': '웹 애플리케이션',
            'test_category': 'web',
            'test_description': 'Flask 웹 애플리케이션 초기화 및 메인 페이지 접근 테스트',
            'test_module': 'src.system_tests.core_tests',
            'test_function': 'test_web_application',
            'is_enabled': True,
            'timeout_seconds': 30,
            'display_order': 1
        },
        {
            'test_key': 'test_health_check',
            'test_name': '헬스체크',
            'test_category': 'web',
            'test_description': '시스템 헬스체크 엔드포인트 테스트',
            'test_module': 'src.system_tests.core_tests',
            'test_function': 'test_health_check',
            'is_enabled': True,
            'timeout_seconds': 10,
            'display_order': 2
        },
        {
            'test_key': 'test_database',
            'test_name': '데이터베이스 연결',
            'test_category': 'database',
            'test_description': 'SQLite 데이터베이스 연결 및 쿼리 실행 테스트',
            'test_module': 'src.system_tests.core_tests',
            'test_function': 'test_database_connection',
            'is_enabled': True,
            'timeout_seconds': 10,
            'display_order': 10
        },
        {
            'test_key': 'test_config',
            'test_name': '설정 파일',
            'test_category': 'system',
            'test_description': 'config.json 파일 존재 여부 및 필수 키 검증',
            'test_module': 'src.system_tests.core_tests',
            'test_function': 'test_config_file',
            'is_enabled': True,
            'timeout_seconds': 5,
            'display_order': 20
        },
        {
            'test_key': 'test_directories',
            'test_name': '디렉토리 구조',
            'test_category': 'system',
            'test_description': '필수 디렉토리(data, uploads 등) 존재 여부 검증',
            'test_module': 'src.system_tests.core_tests',
            'test_function': 'test_directory_structure',
            'is_enabled': True,
            'timeout_seconds': 5,
            'display_order': 21
        },
        {
            'test_key': 'test_email_processor',
            'test_name': '이메일 프로세서',
            'test_category': 'email',
            'test_description': 'EmailEvidenceProcessor 초기화 테스트',
            'test_module': 'src.system_tests.core_tests',
            'test_function': 'test_email_processor',
            'is_enabled': True,
            'timeout_seconds': 15,
            'display_order': 30
        },
        {
            'test_key': 'test_forensic',
            'test_name': '포렌식 무결성 서비스',
            'test_category': 'forensic',
            'test_description': 'ForensicIntegrityService 초기화 테스트',
            'test_module': 'src.system_tests.core_tests',
            'test_function': 'test_forensic_integrity_service',
            'is_enabled': True,
            'timeout_seconds': 15,
            'display_order': 40
        },
        {
            'test_key': 'test_api_endpoints',
            'test_name': 'API 엔드포인트',
            'test_category': 'api',
            'test_description': '주요 API 엔드포인트 응답 테스트',
            'test_module': 'src.system_tests.core_tests',
            'test_function': 'test_api_endpoints',
            'is_enabled': True,
            'timeout_seconds': 30,
            'display_order': 50
        },
        {
            'test_key': 'test_system_settings',
            'test_name': '시스템 설정',
            'test_category': 'system',
            'test_description': '시스템 설정 CRUD 기능 테스트',
            'test_module': 'src.system_tests.core_tests',
            'test_function': 'test_system_settings',
            'is_enabled': True,
            'timeout_seconds': 10,
            'display_order': 22
        },
        {
            'test_key': 'test_disk_space',
            'test_name': '디스크 공간',
            'test_category': 'system',
            'test_description': '디스크 여유 공간 확인',
            'test_module': 'src.system_tests.core_tests',
            'test_function': 'test_disk_space',
            'is_enabled': True,
            'timeout_seconds': 5,
            'display_order': 23
        }
    ]
    
    print("="*60)
    print("시스템 테스트 초기 데이터 설정")
    print("="*60)
    
    success_count = 0
    for test in default_tests:
        try:
            result = test_manager.add_test(**test)
            if result:
                print(f"✅ {test['test_name']} ({test['test_key']})")
                success_count += 1
            else:
                print(f"⚠️  {test['test_name']} - 이미 존재하거나 추가 실패")
        except Exception as e:
            print(f"❌ {test['test_name']} - 오류: {e}")
    
    print("="*60)
    print(f"완료: {success_count}/{len(default_tests)}개 테스트 추가됨")
    print("="*60)
    
    return success_count


if __name__ == '__main__':
    initialize_default_tests()
