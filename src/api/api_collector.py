"""
API 엔드포인트 자동 수집 유틸리티
Flask 라우트에서 API 정보를 추출하여 DB에 저장
"""
import logging
import re
from typing import Any, Dict, List, Optional

from flask import Flask

logger = logging.getLogger(__name__)


class APICollector:
    """Flask 라우트에서 API 정보를 자동 수집"""

    def __init__(self, app: Flask, db_connection):
        """
        Args:
            app: Flask 애플리케이션 인스턴스
            db_connection: DBConnection 인스턴스
        """
        self.app = app
        self.db = db_connection

    def collect_all_endpoints(self) -> List[Dict[str, Any]]:
        """
        모든 API 엔드포인트 수집

        Returns:
            엔드포인트 정보 목록
        """
        endpoints = []

        for rule in self.app.url_map.iter_rules():
            # OPTIONS, HEAD 메서드 제외
            methods = [m for m in rule.methods if m not in ('OPTIONS', 'HEAD')]

            # 각 메서드별로 엔드포인트 정보 수집
            for method in methods:
                endpoint_info = self._extract_endpoint_info(rule, method)
                if endpoint_info:
                    endpoints.append(endpoint_info)

        logger.info(f"총 {len(endpoints)}개 엔드포인트 수집 완료")
        return endpoints

    def _extract_endpoint_info(self, rule, method: str) -> Optional[Dict[str, Any]]:
        """
        단일 엔드포인트 정보 추출

        Args:
            rule: Flask URL Rule
            method: HTTP 메서드

        Returns:
            엔드포인트 정보 딕셔너리
        """
        try:
            view_func = self.app.view_functions[rule.endpoint]
            docstring = view_func.__doc__ or ""

            # 카테고리 분류
            category = self._categorize_endpoint(rule.rule)

            # Docstring 파싱
            summary, description = self._parse_docstring(docstring)

            return {
                'path': rule.rule,
                'method': method,
                'summary': summary or self._generate_default_summary(rule.rule, method),
                'description': description,
                'category': category,
                'version': '1.0',
                'deprecated': False,
                'auth_required': self._check_auth_required(view_func)
            }

        except Exception as e:
            logger.warning(f"엔드포인트 정보 추출 실패 ({rule.rule} {method}): {e}")
            return None

    def _categorize_endpoint(self, path: str) -> str:
        """
        경로 기반 카테고리 분류

        Args:
            path: URL 경로

        Returns:
            카테고리 이름
        """
        if '/email' in path:
            return '이메일'
        elif '/evidence' in path:
            return '증거'
        elif '/timeline' in path:
            return '타임라인'
        elif '/system' in path or '/admin' in path:
            return '시스템'
        elif '/api/docs' in path or '/swagger' in path:
            return 'API 문서'
        elif '/logs' in path:
            return '로그'
        elif '/upload' in path or '/download' in path:
            return '파일'
        else:
            return '기타'

    def _parse_docstring(self, docstring: str) -> tuple[Optional[str], Optional[str]]:
        """
        Docstring에서 요약과 설명 추출

        Args:
            docstring: 함수 docstring

        Returns:
            (요약, 상세 설명) 튜플
        """
        if not docstring:
            return None, None

        lines = [line.strip() for line in docstring.strip().split('\n') if line.strip()]

        if not lines:
            return None, None

        # 첫 줄은 요약
        summary = lines[0]

        # 나머지는 설명
        description = '\n'.join(lines[1:]) if len(lines) > 1 else None

        return summary, description

    def _generate_default_summary(self, path: str, method: str) -> str:
        """
        기본 요약 문구 생성

        Args:
            path: URL 경로
            method: HTTP 메서드

        Returns:
            기본 요약
        """
        # 경로에서 마지막 세그먼트 추출
        segments = [s for s in path.split('/') if s and '<' not in s]
        resource = segments[-1] if segments else 'resource'

        method_action = {
            'GET': '조회',
            'POST': '생성',
            'PUT': '수정',
            'PATCH': '업데이트',
            'DELETE': '삭제'
        }

        action = method_action.get(method, '처리')
        return f"{resource} {action}"

    def _check_auth_required(self, view_func) -> bool:
        """
        인증 필요 여부 확인

        Args:
            view_func: View 함수

        Returns:
            인증 필요 여부
        """
        # 데코레이터나 함수 이름으로 판단
        func_name = view_func.__name__
        if 'admin' in func_name or 'protected' in func_name:
            return True
        return False

    def save_to_db(self, endpoints: List[Dict[str, Any]]) -> int:
        """
        수집된 엔드포인트를 DB에 저장

        Args:
            endpoints: 엔드포인트 정보 목록

        Returns:
            저장된 엔드포인트 수
        """
        saved_count = 0

        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()

                for ep in endpoints:
                    try:
                        # UNIQUE 제약으로 중복 시 무시
                        cursor.execute("""
                            INSERT OR REPLACE INTO api_endpoints
                            (path, method, summary, description, category, version, deprecated, auth_required)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            ep['path'],
                            ep['method'],
                            ep['summary'],
                            ep['description'],
                            ep['category'],
                            ep['version'],
                            1 if ep['deprecated'] else 0,
                            1 if ep['auth_required'] else 0
                        ))
                        saved_count += 1

                    except Exception as e:
                        logger.warning(f"엔드포인트 저장 실패 ({ep['path']} {ep['method']}): {e}")

                conn.commit()
                logger.info(f"{saved_count}개 엔드포인트 DB 저장 완료")

        except Exception as e:
            logger.error(f"DB 저장 오류: {e}")

        return saved_count

    def collect_and_save(self) -> int:
        """
        수집 및 저장 한 번에 실행

        Returns:
            저장된 엔드포인트 수
        """
        endpoints = self.collect_all_endpoints()
        return self.save_to_db(endpoints)


def collect_api_docs(app: Flask, db_connection) -> int:
    """
    편의 함수: API 문서 수집 및 저장

    Args:
        app: Flask 애플리케이션
        db_connection: DBConnection 인스턴스

    Returns:
        저장된 엔드포인트 수
    """
    collector = APICollector(app, db_connection)
    return collector.collect_and_save()
