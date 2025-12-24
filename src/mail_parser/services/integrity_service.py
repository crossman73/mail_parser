"""
Integrity verification service.
"""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional


class IntegrityService:
    """무결성 검증 서비스"""

    def __init__(self, log_file: str = "integrity.log"):
        """초기화"""
        self.log_file = Path(log_file)
        self.integrity_log = []

        # 기존 로그 로드
        self._load_integrity_log()

    def _load_integrity_log(self):
        """무결성 로그 로드"""
        if not self.log_file.exists():
            return

        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                self.integrity_log = json.load(f)
        except Exception as e:
            print(f"무결성 로그 로드 오류: {e}")
            self.integrity_log = []

    def _save_integrity_log(self):
        """무결성 로그 저장"""
        try:
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump(self.integrity_log, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"무결성 로그 저장 오류: {e}")

    def calculate_file_hash(self, file_path: str) -> str:
        """파일 해시 계산"""
        hasher = hashlib.sha256()

        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as e:
            print(f"파일 해시 계산 오류 ({file_path}): {e}")
            return ""

    def calculate_message_hash(self, message_content: str) -> str:
        """메시지 내용 해시 계산"""
        hasher = hashlib.sha256()
        hasher.update(message_content.encode('utf-8'))
        return hasher.hexdigest()

    def calculate_data_hash(self, data: bytes) -> str:
        """바이너리 데이터 해시 계산"""
        hasher = hashlib.sha256()
        hasher.update(data)
        return hasher.hexdigest()

    def verify_file_integrity(self, file_path: str, expected_hash: str) -> bool:
        """파일 무결성 검증"""
        current_hash = self.calculate_file_hash(file_path)
        return current_hash == expected_hash

    def log_integrity_check(
        self,
        entity_id: str,
        entity_type: str,
        file_path: str,
        original_hash: str,
        current_hash: str,
        verified: bool,
        notes: Optional[str] = None
    ):
        """무결성 검증 로그 추가"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'entity_id': entity_id,
            'entity_type': entity_type,
            'file_path': file_path,
            'original_hash': original_hash,
            'current_hash': current_hash,
            'verified': verified,
            'notes': notes or ""
        }

        self.integrity_log.append(log_entry)
        self._save_integrity_log()

    def get_integrity_report(self) -> Dict[str, Any]:
        """무결성 검증 리포트 생성"""
        if not self.integrity_log:
            return {
                'total_checks': 0,
                'verified_count': 0,
                'failed_count': 0,
                'success_rate': 0.0,
                'last_check': None
            }

        total_checks = len(self.integrity_log)
        verified_count = len(
            [log for log in self.integrity_log if log['verified']])
        failed_count = total_checks - verified_count
        success_rate = verified_count / total_checks * 100 if total_checks > 0 else 0.0

        # 최근 검증 날짜
        last_check = max(log['timestamp'] for log in self.integrity_log)

        return {
            'total_checks': total_checks,
            'verified_count': verified_count,
            'failed_count': failed_count,
            'success_rate': success_rate,
            'last_check': last_check
        }

    def get_failed_verifications(self) -> list:
        """검증 실패 목록 조회"""
        return [log for log in self.integrity_log if not log['verified']]

    def create_chain_of_custody(self, entity_id: str, entity_type: str) -> Dict[str, Any]:
        """증거 보관 연쇄성 기록 생성"""
        entity_logs = [
            log for log in self.integrity_log
            if log['entity_id'] == entity_id and log['entity_type'] == entity_type
        ]

        if not entity_logs:
            return {}

        # 시간순 정렬
        entity_logs.sort(key=lambda x: x['timestamp'])

        return {
            'entity_id': entity_id,
            'entity_type': entity_type,
            'creation_time': entity_logs[0]['timestamp'],
            'last_verification': entity_logs[-1]['timestamp'],
            'verification_count': len(entity_logs),
            'all_verified': all(log['verified'] for log in entity_logs),
            'verification_history': entity_logs
        }
