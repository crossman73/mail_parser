"""
데이터베이스 연결 관리 모듈
싱글톤 패턴으로 DB 연결을 중앙 관리하고 헬스체크 기능 제공
"""
import logging
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class DBConnection:
    """싱글톤 패턴의 데이터베이스 연결 관리자"""

    _instance: Optional['DBConnection'] = None
    _lock = threading.Lock()
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """초기화 (싱글톤이므로 한 번만 실행됨)"""
        if not self._initialized:
            self.db_path: Optional[str] = None
            self._connection_pool = []
            self._pool_size = 5
            self._last_health_check: Optional[datetime] = None
            self._health_status: Dict[str, Any] = {}
            DBConnection._initialized = True

    def initialize(self, db_path: str) -> bool:
        """
        데이터베이스 초기화

        Args:
            db_path: 데이터베이스 파일 경로

        Returns:
            초기화 성공 여부
        """
        try:
            self.db_path = db_path
            db_file = Path(db_path)

            # 디렉토리 확인 및 생성
            db_file.parent.mkdir(parents=True, exist_ok=True)

            # DB 파일 존재 확인
            if not db_file.exists():
                logger.warning(f"DB 파일이 없습니다. 생성됩니다: {db_path}")
                # 빈 DB 파일 생성
                with sqlite3.connect(db_path) as conn:
                    conn.execute("SELECT 1")

            # 연결 테스트 (degraded 상태도 허용 - 테이블이 없을 수 있음)
            health = self.health_check()

            if health['status'] in ['healthy', 'degraded']:
                logger.info(f"DB 초기화 완료: {db_path}")
                if health['status'] == 'healthy':
                    logger.info(f"DB 크기: {health['size_mb']:.2f}MB, "
                              f"테이블 수: {health['table_count']}")
                else:
                    logger.info("DB 파일은 정상이나 테이블이 없습니다 (마이그레이션 필요)")
                return True
            else:
                logger.error(f"DB 연결 실패: {health.get('error')}")
                return False

        except Exception as e:
            logger.exception(f"DB 초기화 오류: {e}")
            return False

    @contextmanager
    def get_connection(self):
        """
        컨텍스트 매니저로 DB 연결 제공
        자동으로 커밋/롤백 처리

        Usage:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(...)
        """
        if not self.db_path:
            raise RuntimeError("DB가 초기화되지 않았습니다. initialize()를 먼저 호출하세요.")

        conn = sqlite3.connect(
            self.db_path,
            timeout=30.0,
            check_same_thread=False
        )
        conn.row_factory = sqlite3.Row

        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"DB 작업 오류: {e}")
            raise
        finally:
            conn.close()

    def health_check(self) -> Dict[str, Any]:
        """
        데이터베이스 헬스체크

        Returns:
            헬스체크 결과 딕셔너리
            {
                'status': 'healthy' | 'unhealthy',
                'db_path': str,
                'exists': bool,
                'size_mb': float,
                'writable': bool,
                'table_count': int,
                'last_check': str,
                'response_time_ms': float,
                'error': str (optional)
            }
        """
        start_time = datetime.now()
        result = {
            'status': 'unknown',
            'db_path': self.db_path,
            'exists': False,
            'size_mb': 0.0,
            'writable': False,
            'table_count': 0,
            'last_check': start_time.isoformat(),
            'response_time_ms': 0.0
        }

        try:
            if not self.db_path:
                result['status'] = 'unhealthy'
                result['error'] = 'DB 경로가 설정되지 않음'
                return result

            db_file = Path(self.db_path)

            # 파일 존재 확인
            result['exists'] = db_file.exists()
            if not result['exists']:
                result['status'] = 'unhealthy'
                result['error'] = 'DB 파일이 존재하지 않음'
                return result

            # 파일 크기 확인
            result['size_mb'] = db_file.stat().st_size / (1024 * 1024)

            # 쓰기 가능 여부 확인
            result['writable'] = db_file.parent.is_dir() and \
                                db_file.parent.stat().st_mode & 0o200

            # 연결 테스트
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # 테이블 수 조회
                cursor.execute("""
                    SELECT COUNT(*) as cnt
                    FROM sqlite_master
                    WHERE type='table' AND name NOT LIKE 'sqlite_%'
                """)
                result['table_count'] = cursor.fetchone()[0]

                # 간단한 쓰기 테스트
                cursor.execute("CREATE TABLE IF NOT EXISTS _health_check (id INTEGER)")
                cursor.execute("DROP TABLE IF EXISTS _health_check")

            # 응답 시간 계산
            end_time = datetime.now()
            result['response_time_ms'] = (end_time - start_time).total_seconds() * 1000

            # 상태 판정
            if result['writable'] and result['table_count'] > 0:
                result['status'] = 'healthy'
            else:
                result['status'] = 'degraded'
                result['error'] = '테이블이 없거나 쓰기 불가능'

        except Exception as e:
            result['status'] = 'unhealthy'
            result['error'] = str(e)
            logger.error(f"헬스체크 오류: {e}")

        # 결과 캐싱
        self._last_health_check = datetime.now()
        self._health_status = result

        return result

    def get_database_info(self) -> Dict[str, Any]:
        """
        데이터베이스 상세 정보 조회

        Returns:
            DB 상세 정보 딕셔너리
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # SQLite 버전
                cursor.execute("SELECT sqlite_version()")
                sqlite_version = cursor.fetchone()[0]

                # 테이블 목록
                cursor.execute("""
                    SELECT name FROM sqlite_master
                    WHERE type='table' AND name NOT LIKE 'sqlite_%'
                    ORDER BY name
                """)
                tables = [row[0] for row in cursor.fetchall()]

                # 각 테이블의 레코드 수
                table_counts = {}
                for table in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    table_counts[table] = cursor.fetchone()[0]

                # 인덱스 수
                cursor.execute("""
                    SELECT COUNT(*) FROM sqlite_master
                    WHERE type='index' AND name NOT LIKE 'sqlite_%'
                """)
                index_count = cursor.fetchone()[0]

                return {
                    'sqlite_version': sqlite_version,
                    'tables': tables,
                    'table_counts': table_counts,
                    'index_count': index_count,
                    'total_records': sum(table_counts.values())
                }
        except Exception as e:
            logger.error(f"DB 정보 조회 오류: {e}")
            return {
                'error': str(e)
            }

    def vacuum(self) -> bool:
        """
        데이터베이스 최적화 (VACUUM)

        Returns:
            성공 여부
        """
        try:
            with self.get_connection() as conn:
                conn.execute("VACUUM")
            logger.info("DB VACUUM 완료")
            return True
        except Exception as e:
            logger.error(f"VACUUM 오류: {e}")
            return False

    def get_schema_version(self) -> int:
        """
        현재 스키마 버전 조회

        Returns:
            스키마 버전 번호 (테이블이 없으면 0)
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # schema_version 테이블 확인
                cursor.execute("""
                    SELECT name FROM sqlite_master
                    WHERE type='table' AND name='schema_version'
                """)

                if not cursor.fetchone():
                    return 0

                cursor.execute("SELECT version FROM schema_version ORDER BY id DESC LIMIT 1")
                row = cursor.fetchone()
                return row[0] if row else 0
        except Exception as e:
            logger.error(f"스키마 버전 조회 오류: {e}")
            return 0


# 전역 인스턴스
db_connection = DBConnection()
