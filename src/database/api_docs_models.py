"""
API 문서 데이터 모델 정의
DB 기반 동적 API 문서 관리 시스템
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class APIEndpoint:
    """API 엔드포인트 모델"""
    path: str
    method: str
    summary: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    version: str = "1.0"
    deprecated: bool = False
    auth_required: bool = False
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    id: Optional[int] = None

    @classmethod
    def get_table_schema(cls) -> str:
        """테이블 생성 DDL 반환"""
        return """
            CREATE TABLE IF NOT EXISTS api_endpoints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT NOT NULL,
                method TEXT NOT NULL,
                summary TEXT,
                description TEXT,
                category TEXT,
                version TEXT DEFAULT '1.0',
                deprecated INTEGER DEFAULT 0,
                auth_required INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(path, method)
            )
        """

    @classmethod
    def get_indexes(cls) -> list[str]:
        """인덱스 생성 DDL 목록 반환"""
        return [
            "CREATE INDEX IF NOT EXISTS idx_api_endpoints_category ON api_endpoints(category)",
            "CREATE INDEX IF NOT EXISTS idx_api_endpoints_method ON api_endpoints(method)",
            "CREATE INDEX IF NOT EXISTS idx_api_endpoints_path ON api_endpoints(path)"
        ]


@dataclass
class APIParameter:
    """API 파라미터 모델"""
    endpoint_id: int
    name: str
    type: Optional[str] = None
    required: bool = False
    location: Optional[str] = None  # query, body, path, header
    description: Optional[str] = None
    default_value: Optional[str] = None
    example: Optional[str] = None
    id: Optional[int] = None

    @classmethod
    def get_table_schema(cls) -> str:
        """테이블 생성 DDL 반환"""
        return """
            CREATE TABLE IF NOT EXISTS api_parameters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                endpoint_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                type TEXT,
                required INTEGER DEFAULT 0,
                location TEXT,
                description TEXT,
                default_value TEXT,
                example TEXT,
                FOREIGN KEY (endpoint_id) REFERENCES api_endpoints(id) ON DELETE CASCADE
            )
        """

    @classmethod
    def get_indexes(cls) -> list[str]:
        """인덱스 생성 DDL 목록 반환"""
        return [
            "CREATE INDEX IF NOT EXISTS idx_api_parameters_endpoint ON api_parameters(endpoint_id)"
        ]


@dataclass
class APIResponse:
    """API 응답 모델"""
    endpoint_id: int
    status_code: int
    description: Optional[str] = None
    content_type: str = "application/json"
    schema: Optional[str] = None  # JSON schema
    example: Optional[str] = None  # JSON example
    id: Optional[int] = None

    @classmethod
    def get_table_schema(cls) -> str:
        """테이블 생성 DDL 반환"""
        return """
            CREATE TABLE IF NOT EXISTS api_responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                endpoint_id INTEGER NOT NULL,
                status_code INTEGER NOT NULL,
                description TEXT,
                content_type TEXT DEFAULT 'application/json',
                schema TEXT,
                example TEXT,
                FOREIGN KEY (endpoint_id) REFERENCES api_endpoints(id) ON DELETE CASCADE
            )
        """

    @classmethod
    def get_indexes(cls) -> list[str]:
        """인덱스 생성 DDL 목록 반환"""
        return [
            "CREATE INDEX IF NOT EXISTS idx_api_responses_endpoint ON api_responses(endpoint_id)"
        ]


@dataclass
class APIExample:
    """API 예제 코드 모델"""
    endpoint_id: int
    language: str  # python, javascript, curl
    title: Optional[str] = None
    request_code: Optional[str] = None
    response_code: Optional[str] = None
    id: Optional[int] = None

    @classmethod
    def get_table_schema(cls) -> str:
        """테이블 생성 DDL 반환"""
        return """
            CREATE TABLE IF NOT EXISTS api_examples (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                endpoint_id INTEGER NOT NULL,
                language TEXT NOT NULL,
                title TEXT,
                request_code TEXT,
                response_code TEXT,
                FOREIGN KEY (endpoint_id) REFERENCES api_endpoints(id) ON DELETE CASCADE
            )
        """

    @classmethod
    def get_indexes(cls) -> list[str]:
        """인덱스 생성 DDL 목록 반환"""
        return [
            "CREATE INDEX IF NOT EXISTS idx_api_examples_endpoint ON api_examples(endpoint_id)"
        ]


@dataclass
class APITestExecution:
    """API 테스트 실행 이력 모델"""
    endpoint_id: int
    method: str
    status_code: Optional[int] = None
    response_time_ms: Optional[int] = None
    success: bool = False
    error_message: Optional[str] = None
    request_data: Optional[str] = None  # JSON string
    response_data: Optional[str] = None  # JSON string (truncated)
    executed_at: Optional[str] = None
    user_agent: Optional[str] = None
    id: Optional[int] = None

    @classmethod
    def get_table_schema(cls) -> str:
        """테이블 생성 DDL 반환"""
        return """
            CREATE TABLE IF NOT EXISTS api_test_executions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                endpoint_id INTEGER NOT NULL,
                method TEXT NOT NULL,
                status_code INTEGER,
                response_time_ms INTEGER,
                success INTEGER DEFAULT 0,
                error_message TEXT,
                request_data TEXT,
                response_data TEXT,
                executed_at TEXT DEFAULT CURRENT_TIMESTAMP,
                user_agent TEXT,
                FOREIGN KEY (endpoint_id) REFERENCES api_endpoints(id) ON DELETE CASCADE
            )
        """

    @classmethod
    def get_indexes(cls) -> list[str]:
        """인덱스 생성 DDL 목록 반환"""
        return [
            "CREATE INDEX IF NOT EXISTS idx_api_test_executions_endpoint ON api_test_executions(endpoint_id)",
            "CREATE INDEX IF NOT EXISTS idx_api_test_executions_executed_at ON api_test_executions(executed_at DESC)",
            "CREATE INDEX IF NOT EXISTS idx_api_test_executions_success ON api_test_executions(success)"
        ]


# API 문서 스키마 버전 3
API_DOCS_SCHEMA = {
    'description': 'API documentation tables for dynamic API docs generation',
    'tables': [
        APIEndpoint.get_table_schema(),
        APIParameter.get_table_schema(),
        APIResponse.get_table_schema(),
        APIExample.get_table_schema()
    ],
    'indexes': (
        APIEndpoint.get_indexes() +
        APIParameter.get_indexes() +
        APIResponse.get_indexes() +
        APIExample.get_indexes()
    )
}


# API 테스트 이력 스키마 (버전 4에서 추가 예정)
API_TEST_SCHEMA = {
    'description': 'API test execution history tracking',
    'tables': [
        APITestExecution.get_table_schema()
    ],
    'indexes': APITestExecution.get_indexes()
}
