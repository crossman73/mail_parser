# src/mail_parser/forensic_integrity.py
import datetime
import getpass
import hashlib
import json
import logging
import os
import platform
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class ChainOfCustodyRecord:
    """연계보관성 기록"""
    original_hash: str
    timestamp: str
    collector: str
    system_info: Dict
    verification_status: str
    file_path: str
    file_size: int
    notes: Optional[str] = None


class ForensicIntegrityService:
    """포렌식 무결성 검증 서비스"""

    def __init__(self):
        self.custody_records: List[ChainOfCustodyRecord] = []
        self.logger = logging.getLogger(__name__)

    def create_chain_of_custody(self, file_path: str, notes: str = None) -> ChainOfCustodyRecord:
        """연계보관성 기록 생성"""
        try:
            file_hash = self._calculate_sha256(file_path)
            file_size = os.path.getsize(file_path)

            record = ChainOfCustodyRecord(
                original_hash=file_hash,
                timestamp=datetime.datetime.utcnow().isoformat() + "Z",
                collector=getpass.getuser(),
                system_info={
                    'platform': platform.platform(),
                    'processor': platform.processor(),
                    'python_version': platform.python_version(),
                    'hostname': platform.node(),
                    'machine': platform.machine(),
                    'system': platform.system()
                },
                verification_status="VERIFIED",
                file_path=file_path,
                file_size=file_size,
                notes=notes
            )

            self.custody_records.append(record)
            self.logger.info(
                f"연계보관성 기록 생성: {file_path} -> {file_hash[:16]}...")
            return record

        except Exception as e:
            self.logger.error(f"연계보관성 기록 생성 실패: {str(e)}")
            raise

    def _calculate_sha256(self, file_path: str) -> str:
        """SHA-256 해시 계산 (대용량 파일 지원)"""
        hash_sha256 = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                # 64KB 청크로 읽어서 메모리 효율적 처리
                for chunk in iter(lambda: f.read(65536), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            self.logger.error(f"해시 계산 실패: {file_path} - {str(e)}")
            raise

    def verify_integrity(self, file_path: str, original_hash: str) -> bool:
        """파일 무결성 검증"""
        try:
            current_hash = self._calculate_sha256(file_path)
            is_valid = current_hash == original_hash

            if is_valid:
                self.logger.info(f"무결성 검증 성공: {file_path}")
            else:
                self.logger.error(f"무결성 검증 실패: {file_path}")
                self.logger.error(f"원본 해시: {original_hash}")
                self.logger.error(f"현재 해시: {current_hash}")

            return is_valid
        except Exception as e:
            self.logger.error(f"무결성 검증 중 오류: {str(e)}")
            return False

    def export_custody_log(self, output_path: str = None) -> str:
        """연계보관성 로그 내보내기"""
        if not output_path:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"logs/chain_of_custody_{timestamp}.json"

        # 출력 디렉토리 생성
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        custody_data = {
            'report_info': {
                'generated_at': datetime.datetime.utcnow().isoformat() + "Z",
                'generator': 'Email Evidence Processor v2.0',
                'total_records': len(self.custody_records)
            },
            'records': [
                {
                    'original_hash': record.original_hash,
                    'timestamp': record.timestamp,
                    'collector': record.collector,
                    'system_info': record.system_info,
                    'verification_status': record.verification_status,
                    'file_path': record.file_path,
                    'file_size_bytes': record.file_size,
                    'notes': record.notes
                }
                for record in self.custody_records
            ]
        }

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(custody_data, f, indent=2, ensure_ascii=False)

            self.logger.info(f"연계보관성 로그 저장: {output_path}")
            return output_path
        except Exception as e:
            self.logger.error(f"연계보관성 로그 저장 실패: {str(e)}")
            raise

    def get_custody_summary(self) -> Dict:
        """연계보관성 요약 정보"""
        if not self.custody_records:
            return {'total_records': 0, 'status': 'No records'}

        return {
            'total_records': len(self.custody_records),
            'first_record': self.custody_records[0].timestamp,
            'last_record': self.custody_records[-1].timestamp,
            'verified_records': sum(1 for r in self.custody_records if r.verification_status == 'VERIFIED'),
            'total_file_size': sum(r.file_size for r in self.custody_records),
            'collectors': list(set(r.collector for r in self.custody_records))
        }
