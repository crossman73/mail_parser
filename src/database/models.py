"""
데이터 모델 정의
dataclass 기반으로 타입 안전성을 확보하고 스키마를 중앙 관리
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class SystemTest:
    """시스템 테스트 모델"""
    test_key: str
    test_name: str
    test_category: str
    test_module: str
    test_function: str
    test_description: Optional[str] = None
    is_enabled: bool = True
    timeout_seconds: int = 60
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    id: Optional[int] = None

    @classmethod
    def get_table_schema(cls) -> str:
        """테이블 생성 DDL 반환"""
        return """
            CREATE TABLE IF NOT EXISTS system_tests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_key TEXT UNIQUE NOT NULL,
                test_name TEXT NOT NULL,
                test_category TEXT NOT NULL,
                test_module TEXT NOT NULL,
                test_function TEXT NOT NULL,
                test_description TEXT,
                is_enabled INTEGER DEFAULT 1,
                timeout_seconds INTEGER DEFAULT 60,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """

    @classmethod
    def get_indexes(cls) -> list[str]:
        """인덱스 생성 DDL 목록 반환"""
        return [
            "CREATE INDEX IF NOT EXISTS idx_test_key ON system_tests(test_key)",
            "CREATE INDEX IF NOT EXISTS idx_test_category ON system_tests(test_category)",
            "CREATE INDEX IF NOT EXISTS idx_is_enabled ON system_tests(is_enabled)"
        ]


@dataclass
class TestExecution:
    """테스트 실행 이력 모델"""
    test_id: int
    status: str
    execution_time: str
    duration_ms: int
    result_message: Optional[str] = None
    error_detail: Optional[str] = None
    executed_by: str = "system"
    id: Optional[int] = None

    @classmethod
    def get_table_schema(cls) -> str:
        """테이블 생성 DDL 반환"""
        return """
            CREATE TABLE IF NOT EXISTS test_executions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_id INTEGER NOT NULL,
                execution_time TEXT NOT NULL,
                status TEXT NOT NULL,
                result_message TEXT,
                error_detail TEXT,
                duration_ms INTEGER DEFAULT 0,
                executed_by TEXT DEFAULT 'system',
                FOREIGN KEY (test_id) REFERENCES system_tests(id) ON DELETE CASCADE
            )
        """

    @classmethod
    def get_indexes(cls) -> list[str]:
        """인덱스 생성 DDL 목록 반환"""
        return [
            "CREATE INDEX IF NOT EXISTS idx_test_id ON test_executions(test_id)",
            "CREATE INDEX IF NOT EXISTS idx_execution_time ON test_executions(execution_time DESC)",
            "CREATE INDEX IF NOT EXISTS idx_status ON test_executions(status)"
        ]


@dataclass
class SchemaVersion:
    """스키마 버전 관리 모델"""
    version: int
    description: str
    applied_at: Optional[str] = None
    id: Optional[int] = None

    @classmethod
    def get_table_schema(cls) -> str:
        """테이블 생성 DDL 반환"""
        return """
            CREATE TABLE IF NOT EXISTS schema_version (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version INTEGER NOT NULL UNIQUE,
                description TEXT NOT NULL,
                applied_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """


# 전체 스키마 정의 (버전별)
SCHEMA_DEFINITIONS = {
    1: {
        'description': 'Initial schema with system_tests and test_executions',
        'tables': [
            SystemTest.get_table_schema(),
            TestExecution.get_table_schema(),
            SchemaVersion.get_table_schema()
        ],
        'indexes': SystemTest.get_indexes() + TestExecution.get_indexes()
    },
    2: {
        'description': 'Add test_category column to system_tests',
        'migration': """
            -- test_category 컬럼이 없는 경우에만 추가
            -- SQLite는 IF NOT EXISTS를 지원하지 않으므로 예외 처리 필요
        """
    },
    3: {
        'description': 'API documentation tables for dynamic API docs generation',
        'tables': None,  # api_docs_models.py에서 임포트
        'indexes': None
    },
    4: {
        'description': 'API test execution history tracking',
        'tables': None,  # api_docs_models.py의 API_TEST_SCHEMA에서 임포트
        'indexes': None
    }
}
