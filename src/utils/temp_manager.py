"""
임시 데이터 관리를 위한 유틸리티
날짜별 디렉토리 구조로 임시 파일들을 관리합니다.
"""
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class TempDataManager:
    """임시 데이터 관리 클래스"""

    def __init__(self, base_temp_dir: str = "temp"):
        """
        Args:
            base_temp_dir: 기본 임시 디렉토리 경로
        """
        self.base_temp_dir = Path(base_temp_dir)
        self.current_session_dir = None

    def create_session_directory(self, session_id: Optional[str] = None) -> str:
        """
        새로운 세션 디렉토리를 생성합니다.

        Args:
            session_id: 세션 ID (없으면 현재 날짜/시간으로 생성)

        Returns:
            생성된 세션 디렉토리 경로
        """
        if session_id is None:
            session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 날짜별 디렉토리 구조: temp/20240902/20240902_143022/
        date_dir = datetime.now().strftime("%Y%m%d")
        session_dir = self.base_temp_dir / date_dir / session_id

        # 디렉토리 생성
        session_dir.mkdir(parents=True, exist_ok=True)

        # 하위 디렉토리들 생성
        subdirs = [
            "parsed_emails",      # 파싱된 이메일 데이터
            "attachments",        # 첨부파일
            "generated_evidence",  # 생성된 증거
            "metadata",          # 메타데이터
            "temp_files"         # 기타 임시파일
        ]

        for subdir in subdirs:
            (session_dir / subdir).mkdir(exist_ok=True)

        self.current_session_dir = session_dir
        return str(session_dir)

    def get_session_dir(self, create_if_not_exists: bool = True) -> str:
        """
        현재 세션 디렉토리를 반환합니다.

        Args:
            create_if_not_exists: 존재하지 않으면 생성할지 여부

        Returns:
            현재 세션 디렉토리 경로
        """
        if self.current_session_dir is None and create_if_not_exists:
            return self.create_session_directory()
        return str(self.current_session_dir) if self.current_session_dir else ""

    def get_subdir(self, subdir_name: str) -> str:
        """
        특정 하위 디렉토리 경로를 반환합니다.

        Args:
            subdir_name: 하위 디렉토리 이름

        Returns:
            하위 디렉토리 경로
        """
        session_dir = self.get_session_dir()
        return str(Path(session_dir) / subdir_name)

    def save_parsed_emails(self, emails_data: Dict, filename: str = "parsed_emails.json") -> str:
        """
        파싱된 이메일 데이터를 저장합니다.

        Args:
            emails_data: 파싱된 이메일 데이터
            filename: 저장할 파일명

        Returns:
            저장된 파일 경로
        """
        import json

        parsed_dir = self.get_subdir("parsed_emails")
        file_path = Path(parsed_dir) / filename

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(emails_data, f, ensure_ascii=False,
                      indent=2, default=str)

        return str(file_path)

    def load_parsed_emails(self, filename: str = "parsed_emails.json") -> Dict:
        """
        파싱된 이메일 데이터를 로드합니다.

        Args:
            filename: 로드할 파일명

        Returns:
            파싱된 이메일 데이터
        """
        import json

        parsed_dir = self.get_subdir("parsed_emails")
        file_path = Path(parsed_dir) / filename

        if not file_path.exists():
            return {}

        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save_metadata(self, metadata: Dict, filename: str = "metadata.json") -> str:
        """
        메타데이터를 저장합니다.

        Args:
            metadata: 메타데이터
            filename: 저장할 파일명

        Returns:
            저장된 파일 경로
        """
        import json

        metadata_dir = self.get_subdir("metadata")
        file_path = Path(metadata_dir) / filename

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2, default=str)

        return str(file_path)

    def copy_attachments(self, source_attachments: List[str]) -> List[str]:
        """
        첨부파일을 임시 디렉토리로 복사합니다.

        Args:
            source_attachments: 원본 첨부파일 경로 리스트

        Returns:
            복사된 첨부파일 경로 리스트
        """
        attachments_dir = self.get_subdir("attachments")
        copied_files = []

        for source_file in source_attachments:
            if os.path.exists(source_file):
                filename = os.path.basename(source_file)
                dest_file = Path(attachments_dir) / filename

                # 동일한 파일명이 있으면 번호 추가
                counter = 1
                while dest_file.exists():
                    name, ext = os.path.splitext(filename)
                    dest_file = Path(attachments_dir) / \
                        f"{name}_{counter}{ext}"
                    counter += 1

                shutil.copy2(source_file, dest_file)
                copied_files.append(str(dest_file))

        return copied_files

    def cleanup_session(self, session_dir: Optional[str] = None) -> bool:
        """
        세션 디렉토리를 정리합니다.

        Args:
            session_dir: 정리할 세션 디렉토리 (없으면 현재 세션)

        Returns:
            정리 성공 여부
        """
        try:
            if session_dir is None:
                session_dir = self.get_session_dir(create_if_not_exists=False)

            if session_dir and os.path.exists(session_dir):
                shutil.rmtree(session_dir)
                return True
        except Exception as e:
            print(f"세션 디렉토리 정리 실패: {e}")
            return False

        return False

    def cleanup_old_sessions(self, days_old: int = 7, evidence_days_old: int = 30) -> Dict[str, int]:
        """
        오래된 세션 디렉토리들을 정리합니다.

        보관 정책:
        - 증거가 생성되지 않은 세션: days_old 일 후 삭제 (기본 7일)
        - 증거가 생성된 세션: evidence_days_old 일 후 삭제 (기본 30일)
        - 에러 발생 세션: 즉시 삭제 (1일)

        Args:
            days_old: 일반 세션 삭제 기준 (기본 7일)
            evidence_days_old: 증거 생성 세션 삭제 기준 (기본 30일)

        Returns:
            삭제 통계 {'normal': N, 'evidence': M, 'error': K, 'total': T}
        """
        if not self.base_temp_dir.exists():
            return {'normal': 0, 'evidence': 0, 'error': 0, 'total': 0}

        import json
        stats = {'normal': 0, 'evidence': 0, 'error': 0, 'total': 0}
        now = datetime.now().timestamp()
        cutoff_normal = now - (days_old * 24 * 60 * 60)
        cutoff_evidence = now - (evidence_days_old * 24 * 60 * 60)
        cutoff_error = now - (1 * 24 * 60 * 60)  # 에러 세션은 1일만 보관

        try:
            for date_dir in self.base_temp_dir.iterdir():
                if date_dir.is_dir():
                    for session_dir in date_dir.iterdir():
                        if session_dir.is_dir():
                            session_created = session_dir.stat().st_ctime

                            # 메타데이터 파일에서 상태 확인
                            has_evidence = False
                            has_error = False
                            metadata_dir = session_dir / "metadata"

                            if metadata_dir.exists():
                                # evidence_result 파일 존재 여부로 증거 생성 확인
                                evidence_files = list(metadata_dir.glob("evidence_result_*.json"))
                                has_evidence = len(evidence_files) > 0

                                # metadata 파일에서 에러 상태 확인
                                metadata_files = list(metadata_dir.glob("metadata_*.json"))
                                for meta_file in metadata_files:
                                    try:
                                        with open(meta_file, 'r', encoding='utf-8') as f:
                                            meta_data = json.load(f)
                                            if meta_data.get('status') == 'error':
                                                has_error = True
                                                break
                                    except Exception:
                                        pass

                            # 삭제 여부 결정
                            should_delete = False
                            delete_type = None

                            if has_error and session_created < cutoff_error:
                                should_delete = True
                                delete_type = 'error'
                            elif has_evidence and session_created < cutoff_evidence:
                                should_delete = True
                                delete_type = 'evidence'
                            elif not has_evidence and session_created < cutoff_normal:
                                should_delete = True
                                delete_type = 'normal'

                            if should_delete:
                                shutil.rmtree(session_dir)
                                stats[delete_type] += 1
                                stats['total'] += 1

                    # 빈 날짜 디렉토리 삭제
                    if not any(date_dir.iterdir()):
                        date_dir.rmdir()

        except Exception as e:
            print(f"오래된 세션 정리 실패: {e}")

        return stats

    def cleanup_system_temp_file(self, temp_file_path: str) -> bool:
        """
        시스템 임시 디렉토리의 특정 파일을 삭제합니다.

        Args:
            temp_file_path: 삭제할 임시 파일 경로

        Returns:
            삭제 성공 여부
        """
        try:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
                return True
        except Exception as e:
            print(f"임시 파일 삭제 실패 ({temp_file_path}): {e}")
        return False

    def finalize_session(self, session_id: str, keep_evidence_files: bool = True) -> bool:
        """
        세션 작업 완료 후 최종 정리를 수행합니다.

        Args:
            session_id: 세션 ID
            keep_evidence_files: 증거 파일 보관 여부

        Returns:
            정리 성공 여부
        """
        try:
            # 세션 디렉토리 찾기
            for date_dir in self.base_temp_dir.iterdir():
                if date_dir.is_dir():
                    session_dir = date_dir / session_id
                    if session_dir.exists():
                        if keep_evidence_files:
                            # 증거 파일은 보관하고 임시 파일만 정리
                            temp_files_dir = session_dir / "temp_files"
                            if temp_files_dir.exists():
                                shutil.rmtree(temp_files_dir)
                            # parsed_emails는 삭제 (DB에 저장되었으므로)
                            parsed_dir = session_dir / "parsed_emails"
                            if parsed_dir.exists():
                                shutil.rmtree(parsed_dir)
                            return True
                        else:
                            # 전체 세션 삭제
                            shutil.rmtree(session_dir)
                            return True
        except Exception as e:
            print(f"세션 최종 정리 실패: {e}")
            return False
        return False

    def list_sessions(self) -> List[Dict]:
        """
        모든 세션 정보를 반환합니다.

        Returns:
            세션 정보 리스트
        """
        sessions = []

        if not self.base_temp_dir.exists():
            return sessions

        try:
            for date_dir in self.base_temp_dir.iterdir():
                if date_dir.is_dir():
                    for session_dir in date_dir.iterdir():
                        if session_dir.is_dir():
                            stat_info = session_dir.stat()
                            sessions.append({
                                'session_id': session_dir.name,
                                'date': date_dir.name,
                                'path': str(session_dir),
                                'created_at': datetime.fromtimestamp(stat_info.st_ctime),
                                'modified_at': datetime.fromtimestamp(stat_info.st_mtime),
                                'size_mb': sum(f.stat().st_size for f in session_dir.rglob('*') if f.is_file()) / 1024 / 1024
                            })
        except Exception as e:
            print(f"세션 목록 조회 실패: {e}")

        return sorted(sessions, key=lambda x: x['created_at'], reverse=True)

    def get_storage_stats(self) -> Dict[str, any]:
        """
        임시 저장소 통계 정보를 반환합니다.

        Returns:
            통계 정보 (총 크기, 세션 수, 오래된 세션 수 등)
        """
        stats = {
            'total_size_mb': 0,
            'total_sessions': 0,
            'sessions_with_evidence': 0,
            'sessions_without_evidence': 0,
            'sessions_with_error': 0,
            'old_sessions_count': 0,  # 7일 이상 된 세션
            'very_old_sessions_count': 0  # 30일 이상 된 세션
        }

        if not self.base_temp_dir.exists():
            return stats

        import json
        now = datetime.now().timestamp()
        cutoff_7days = now - (7 * 24 * 60 * 60)
        cutoff_30days = now - (30 * 24 * 60 * 60)

        try:
            for date_dir in self.base_temp_dir.iterdir():
                if date_dir.is_dir():
                    for session_dir in date_dir.iterdir():
                        if session_dir.is_dir():
                            stats['total_sessions'] += 1

                            # 크기 계산
                            size = sum(f.stat().st_size for f in session_dir.rglob('*') if f.is_file())
                            stats['total_size_mb'] += size / 1024 / 1024

                            # 생성 시간
                            created = session_dir.stat().st_ctime
                            if created < cutoff_30days:
                                stats['very_old_sessions_count'] += 1
                            elif created < cutoff_7days:
                                stats['old_sessions_count'] += 1

                            # 상태 확인
                            metadata_dir = session_dir / "metadata"
                            if metadata_dir.exists():
                                if list(metadata_dir.glob("evidence_result_*.json")):
                                    stats['sessions_with_evidence'] += 1
                                else:
                                    stats['sessions_without_evidence'] += 1

                                # 에러 상태 확인
                                for meta_file in metadata_dir.glob("metadata_*.json"):
                                    try:
                                        with open(meta_file, 'r', encoding='utf-8') as f:
                                            if json.load(f).get('status') == 'error':
                                                stats['sessions_with_error'] += 1
                                                break
                                    except Exception:
                                        pass
        except Exception as e:
            print(f"저장소 통계 조회 실패: {e}")

        return stats


# 전역 인스턴스
temp_manager = TempDataManager()
