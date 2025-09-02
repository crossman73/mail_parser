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

    def cleanup_old_sessions(self, days_old: int = 7) -> int:
        """
        오래된 세션 디렉토리들을 정리합니다.

        Args:
            days_old: 삭제할 세션의 일 수 (기본 7일)

        Returns:
            삭제된 세션 수
        """
        if not self.base_temp_dir.exists():
            return 0

        deleted_count = 0
        cutoff_date = datetime.now().timestamp() - (days_old * 24 * 60 * 60)

        try:
            for date_dir in self.base_temp_dir.iterdir():
                if date_dir.is_dir():
                    for session_dir in date_dir.iterdir():
                        if session_dir.is_dir():
                            # 디렉토리 생성 시간 확인
                            if session_dir.stat().st_ctime < cutoff_date:
                                shutil.rmtree(session_dir)
                                deleted_count += 1

                    # 빈 날짜 디렉토리 삭제
                    if not any(date_dir.iterdir()):
                        date_dir.rmdir()

        except Exception as e:
            print(f"오래된 세션 정리 실패: {e}")

        return deleted_count

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


# 전역 인스턴스
temp_manager = TempDataManager()
