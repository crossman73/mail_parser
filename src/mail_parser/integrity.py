# src/mail_parser/integrity.py

import hashlib
import json
import os
from datetime import datetime
from typing import Dict, List, Optional


class IntegrityManager:
    """
    파일 무결성 검증 및 해시값 관리 클래스
    """

    def __init__(self, output_dir: str = "processed_emails"):
        self.output_dir = output_dir
        self.integrity_log = []
        self.hash_records = {}

    def calculate_file_hash(self, filepath: str, algorithm: str = 'sha256') -> Optional[str]:
        """
        파일의 해시값을 계산합니다.

        Args:
            filepath: 해시를 계산할 파일 경로
            algorithm: 해시 알고리즘 (sha256, md5 등)

        Returns:
            해시값 문자열 또는 None (오류 시)
        """
        try:
            hash_obj = hashlib.new(algorithm)
            with open(filepath, 'rb') as f:
                # 대용량 파일을 위한 청크 단위 처리
                for chunk in iter(lambda: f.read(8192), b""):
                    hash_obj.update(chunk)

            hash_value = hash_obj.hexdigest()

            # 해시 기록 저장
            self.hash_records[filepath] = {
                'algorithm': algorithm,
                'hash': hash_value,
                'size': os.path.getsize(filepath),
                'timestamp': datetime.now().isoformat(),
                'filename': os.path.basename(filepath)
            }

            return hash_value

        except Exception as e:
            self._log_error(f"해시 계산 실패: {filepath} - {str(e)}")
            return None

    def calculate_content_hash(self, content: str, algorithm: str = 'sha256') -> str:
        """
        문자열 내용의 해시값을 계산합니다.
        """
        hash_obj = hashlib.new(algorithm)
        hash_obj.update(content.encode('utf-8'))
        return hash_obj.hexdigest()

    def verify_file_integrity(self, filepath: str, expected_hash: str, algorithm: str = 'sha256') -> bool:
        """
        파일의 무결성을 검증합니다.

        Args:
            filepath: 검증할 파일 경로
            expected_hash: 기대되는 해시값
            algorithm: 해시 알고리즘

        Returns:
            무결성 검증 결과 (True/False)
        """
        current_hash = self.calculate_file_hash(filepath, algorithm)

        if current_hash is None:
            return False

        is_valid = current_hash == expected_hash

        self._log_verification(filepath, expected_hash, current_hash, is_valid)

        return is_valid

    def generate_integrity_report(self, report_path: Optional[str] = None) -> str:
        """
        무결성 검증 보고서를 생성합니다.

        Args:
            report_path: 보고서 저장 경로 (None이면 자동 생성)

        Returns:
            보고서 파일 경로
        """
        if report_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_path = os.path.join(
                self.output_dir, f"integrity_report_{timestamp}.json")

        report_data = {
            'generation_time': datetime.now().isoformat(),
            'total_files': len(self.hash_records),
            'hash_algorithm': 'sha256',
            'files': self.hash_records,
            'integrity_log': self.integrity_log
        }

        # 보고서 디렉토리 생성
        os.makedirs(os.path.dirname(report_path), exist_ok=True)

        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)

            self._log_info(f"무결성 보고서 생성 완료: {report_path}")
            return report_path

        except Exception as e:
            self._log_error(f"보고서 생성 실패: {str(e)}")
            return None

    def create_chain_of_custody_log(self, email_id: str, actions: List[Dict]) -> str:
        """
        체인 오브 커스터디(연계보관성) 로그를 생성합니다.

        Args:
            email_id: 메일 식별자
            actions: 수행된 작업 목록

        Returns:
            로그 엔트리 ID
        """
        timestamp = datetime.now().isoformat()
        entry_id = f"{email_id}_{timestamp}"

        custody_entry = {
            'entry_id': entry_id,
            'email_id': email_id,
            'timestamp': timestamp,
            'actions': actions,
            'integrity_verified': True
        }

        self.integrity_log.append(custody_entry)
        return entry_id

    def batch_calculate_hashes(self, directory: str, file_patterns: List[str] = None) -> Dict[str, str]:
        """
        디렉토리 내 파일들의 해시값을 일괄 계산합니다.

        Args:
            directory: 대상 디렉토리
            file_patterns: 처리할 파일 패턴 리스트 (None이면 모든 파일)

        Returns:
            파일경로: 해시값 딕셔너리
        """
        hash_results = {}

        if not os.path.exists(directory):
            self._log_error(f"디렉토리를 찾을 수 없습니다: {directory}")
            return hash_results

        for root, dirs, files in os.walk(directory):
            for filename in files:
                filepath = os.path.join(root, filename)

                # 파일 패턴 필터링
                if file_patterns:
                    if not any(pattern in filename for pattern in file_patterns):
                        continue

                hash_value = self.calculate_file_hash(filepath)
                if hash_value:
                    hash_results[filepath] = hash_value

        self._log_info(f"일괄 해시 계산 완료: {len(hash_results)}개 파일")
        return hash_results

    def export_hash_list(self, output_path: str) -> bool:
        """
        해시 목록을 CSV 형태로 내보냅니다.
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("파일경로,파일명,해시값,알고리즘,크기,생성시간\n")

                for filepath, record in self.hash_records.items():
                    f.write(f'"{filepath}","{record["filename"]}",{record["hash"]},'
                            f'{record["algorithm"]},{record["size"]},{record["timestamp"]}\n')

            self._log_info(f"해시 목록 내보내기 완료: {output_path}")
            return True

        except Exception as e:
            self._log_error(f"해시 목록 내보내기 실패: {str(e)}")
            return False

    def _log_info(self, message: str):
        """정보 로그 기록"""
        print(f"[무결성] {message}")

    def _log_error(self, message: str):
        """오류 로그 기록"""
        print(f"[무결성 오류] {message}")

    def _log_verification(self, filepath: str, expected: str, actual: str, is_valid: bool):
        """검증 로그 기록"""
        status = "성공" if is_valid else "실패"
        print(f"[무결성 검증] {os.path.basename(filepath)}: {status}")

        verification_entry = {
            'timestamp': datetime.now().isoformat(),
            'filepath': filepath,
            'expected_hash': expected,
            'actual_hash': actual,
            'verification_result': is_valid
        }
        self.integrity_log.append(verification_entry)
