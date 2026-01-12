"""
데이터베이스 마이그레이션 관리자
스키마 버전을 추적하고 자동으로 마이그레이션 실행
"""
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class Migration:
    """단일 마이그레이션을 나타내는 클래스"""

    def __init__(self, version: int, description: str):
        self.version = version
        self.description = description

    def up(self, conn) -> bool:
        """
        마이그레이션 적용

        Args:
            conn: 데이터베이스 연결

        Returns:
            성공 여부
        """
        raise NotImplementedError("up() 메서드를 구현해야 합니다")

    def down(self, conn) -> bool:
        """
        마이그레이션 롤백

        Args:
            conn: 데이터베이스 연결

        Returns:
            성공 여부
        """
        raise NotImplementedError("down() 메서드를 구현해야 합니다")


class MigrationManager:
    """마이그레이션 관리자"""

    def __init__(self, db_connection):
        """
        Args:
            db_connection: DBConnection 인스턴스
        """
        self.db = db_connection
        self.migrations_dir = Path(__file__).parent / 'versions'
        self._ensure_schema_version_table()

    def _ensure_schema_version_table(self):
        """schema_version 테이블 생성"""
        try:
            with self.db.get_connection() as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS schema_version (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        version INTEGER NOT NULL UNIQUE,
                        description TEXT NOT NULL,
                        applied_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
        except Exception as e:
            logger.error(f"schema_version 테이블 생성 오류: {e}")

    def get_current_version(self) -> int:
        """
        현재 스키마 버전 조회

        Returns:
            현재 버전 번호 (없으면 0)
        """
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT version FROM schema_version
                    ORDER BY version DESC
                    LIMIT 1
                """)
                row = cursor.fetchone()
                return row[0] if row else 0
        except Exception as e:
            logger.error(f"현재 버전 조회 오류: {e}")
            return 0

    def get_migration_history(self) -> List[Dict[str, Any]]:
        """
        마이그레이션 이력 조회

        Returns:
            마이그레이션 이력 목록
        """
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT version, description, applied_at
                    FROM schema_version
                    ORDER BY version ASC
                """)
                return [
                    {
                        'version': row[0],
                        'description': row[1],
                        'applied_at': row[2]
                    }
                    for row in cursor.fetchall()
                ]
        except Exception as e:
            logger.error(f"마이그레이션 이력 조회 오류: {e}")
            return []

    def update_version(self, version: int, description: str) -> bool:
        """
        버전 정보 업데이트

        Args:
            version: 버전 번호
            description: 버전 설명

        Returns:
            성공 여부
        """
        try:
            with self.db.get_connection() as conn:
                conn.execute("""
                    INSERT OR IGNORE INTO schema_version (version, description)
                    VALUES (?, ?)
                """, (version, description))
            return True
        except Exception as e:
            logger.error(f"버전 업데이트 오류: {e}")
            return False

    def run_migrations(self, target_version: Optional[int] = None) -> bool:
        """
        마이그레이션 실행

        Args:
            target_version: 목표 버전 (None이면 최신 버전까지)

        Returns:
            성공 여부
        """
        current_version = self.get_current_version()
        logger.info(f"현재 스키마 버전: {current_version}")

        # 초기 스키마 적용 (버전 0 -> 1)
        if current_version == 0:
            if self._apply_initial_schema():
                logger.info("초기 스키마 적용 완료")
                current_version = 1
            else:
                logger.error("초기 스키마 적용 실패")
                return False

        # 버전 3 마이그레이션: API 문서 테이블
        if current_version < 3:
            if self._apply_api_docs_schema():
                logger.info("API 문서 스키마 (v3) 적용 완료")
                current_version = 3
            else:
                logger.error("API 문서 스키마 적용 실패")
                return False

        # 버전 4 마이그레이션: API 테스트 이력 테이블
        if current_version < 4:
            if self._apply_api_test_schema():
                logger.info("API 테스트 이력 스키마 (v4) 적용 완료")
                current_version = 4
            else:
                logger.error("API 테스트 이력 스키마 적용 실패")
                return False

        # 추가 마이그레이션 실행
        # TODO: versions/ 디렉토리에서 마이그레이션 파일 로드 및 실행

        return True

    def _apply_api_docs_schema(self) -> bool:
        """
        API 문서 스키마 적용 (버전 3)

        Returns:
            성공 여부
        """
        try:
            from src.database.api_docs_models import API_DOCS_SCHEMA

            with self.db.get_connection() as conn:
                # 테이블 생성
                for ddl in API_DOCS_SCHEMA['tables']:
                    conn.execute(ddl)

                # 인덱스 생성
                for idx_ddl in API_DOCS_SCHEMA['indexes']:
                    conn.execute(idx_ddl)

            # 버전 기록
            self.update_version(3, API_DOCS_SCHEMA['description'])

            logger.info("API 문서 스키마 (v3) 적용 완료")
            return True

        except Exception as e:
            logger.exception(f"API 문서 스키마 적용 오류: {e}")
            return False

    def _apply_api_test_schema(self) -> bool:
        """
        API 테스트 이력 스키마 적용 (버전 4)

        Returns:
            성공 여부
        """
        try:
            from src.database.api_docs_models import API_TEST_SCHEMA

            with self.db.get_connection() as conn:
                # 테이블 생성
                for ddl in API_TEST_SCHEMA['tables']:
                    conn.execute(ddl)

                # 인덱스 생성
                for idx_ddl in API_TEST_SCHEMA['indexes']:
                    conn.execute(idx_ddl)

            # 버전 기록
            self.update_version(4, API_TEST_SCHEMA['description'])

            logger.info("API 테스트 이력 스키마 (v4) 적용 완료")
            return True

        except Exception as e:
            logger.exception(f"API 테스트 이력 스키마 적용 오류: {e}")
            return False

    def _apply_initial_schema(self) -> bool:
        """
        초기 스키마 적용 (버전 1)

        Returns:
            성공 여부
        """
        try:
            from src.database.models import SCHEMA_DEFINITIONS

            schema_v1 = SCHEMA_DEFINITIONS[1]

            with self.db.get_connection() as conn:
                # 테이블 생성
                for ddl in schema_v1['tables']:
                    conn.execute(ddl)

                # 인덱스 생성
                for idx_ddl in schema_v1['indexes']:
                    conn.execute(idx_ddl)

            # 버전 기록
            self.update_version(1, schema_v1['description'])

            logger.info("초기 스키마 (v1) 적용 완료")
            return True

        except Exception as e:
            logger.exception(f"초기 스키마 적용 오류: {e}")
            return False

    def get_migration_status(self) -> Dict[str, Any]:
        """
        마이그레이션 상태 조회

        Returns:
            마이그레이션 상태 정보
        """
        return {
            'current_version': self.get_current_version(),
            'history': self.get_migration_history(),
            'migrations_dir': str(self.migrations_dir)
        }
