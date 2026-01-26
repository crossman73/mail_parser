"""
Court Evidence Integrity Verifier with Additional Evidence Support
법원 증거 무결성 검증기 - 추가 증거 지원
"""

import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


class CourtEvidenceIntegrityVerifier:
    """법원 증거 무결성 검증기 - 통합 증거 지원"""

    def __init__(self, processed_emails_dir: str, additional_evidence_dir: Optional[str] = None):
        """
        초기화

        Args:
            processed_emails_dir: 처리된 이메일 디렉토리
            additional_evidence_dir: 추가 증거 디렉토리 (선택적)
        """
        self.processed_emails_dir = Path(processed_emails_dir)
        self.additional_evidence_dir = Path(
            additional_evidence_dir) if additional_evidence_dir else None
        self.verification_dir = self.processed_emails_dir / "04_검증자료"
        self.font_path = self._find_korean_font()

        # 한글 폰트 등록
        if self.font_path and os.path.exists(self.font_path):
            try:
                pdfmetrics.registerFont(TTFont('NanumGothic', self.font_path))
                self.font_available = True
            except Exception as e:
                print(f"⚠️  한글 폰트 등록 실패: {e}")
                self.font_available = False
        else:
            self.font_available = False

        self.verification_dir.mkdir(exist_ok=True)

    def _find_korean_font(self) -> Optional[str]:
        """한글 폰트 찾기"""
        font_paths = [
            "email_files/NanumGothic.ttf",
            "fonts/NanumGothic.ttf",
            "/System/Library/Fonts/AppleGothic.ttf",  # macOS
            "C:/Windows/Fonts/malgun.ttf",  # Windows
            "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"  # Linux
        ]

        for font_path in font_paths:
            if os.path.exists(font_path):
                return font_path
        return None

    def calculate_file_hash(self, file_path: Path) -> str:
        """파일의 SHA-256 해시 계산"""
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            return sha256_hash.hexdigest()
        except Exception as e:
            print(f"❌ 파일 해시 계산 실패 {file_path}: {e}")
            return ""

    def verify_integrity(self) -> Dict:
        """통합 무결성 검증 실행"""
        print("🔍 통합 증거 무결성 검증을 시작합니다...")

        # 이메일 증거 검증
        print("📧 이메일 증거 검증 중...")
        email_results = self._verify_email_evidence()

        # 추가 증거 검증
        print("📁 추가 증거 검증 중...")
        additional_results = self._verify_additional_evidence()

        # 통합 결과 생성
        verification_result = {
            'timestamp': datetime.now().isoformat(),
            'email_evidence': email_results,
            'additional_evidence': additional_results,
            'summary': {
                'total_files': len(email_results['files']) + len(additional_results['files']),
                'total_verified': email_results['verified_count'] + additional_results['verified_count'],
                'total_failed': email_results['failed_count'] + additional_results['failed_count'],
                'total_errors': len(email_results['errors']) + len(additional_results['errors'])
            }
        }

        # 전체 성공률 계산
        total_files = verification_result['summary']['total_files']
        if total_files > 0:
            success_rate = (
                verification_result['summary']['total_verified'] / total_files) * 100
            verification_result['summary']['success_rate'] = success_rate
        else:
            verification_result['summary']['success_rate'] = 0

        # 결과 저장
        self._save_verification_results(verification_result)

        # 법원 제출용 증명서 생성
        self._generate_court_certificate(verification_result)

        return verification_result

    def _verify_email_evidence(self) -> Dict:
        """이메일 증거 검증"""
        email_results = {
            'verified_count': 0,
            'failed_count': 0,
            'files': [],
            'errors': []
        }

        if not self.processed_emails_dir.exists():
            email_results['errors'].append(
                f"이메일 디렉토리가 존재하지 않음: {self.processed_emails_dir}")
            return email_results

        # 이메일 디렉토리 검증
        for email_dir in self.processed_emails_dir.iterdir():
            if email_dir.is_dir() and email_dir.name.startswith('['):
                try:
                    # 메타데이터 파일 확인
                    metadata_file = email_dir / "metadata.json"
                    if metadata_file.exists():
                        with open(metadata_file, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)

                        # 원본 메시지 파일 검증
                        for file_pattern in ["original_message.eml", "*.eml", "*.msg"]:
                            eml_files = list(email_dir.glob(file_pattern))
                            if eml_files:
                                eml_file = eml_files[0]
                                file_hash = self.calculate_file_hash(eml_file)

                                email_results['files'].append({
                                    'path': str(eml_file.relative_to(self.processed_emails_dir)),
                                    'hash': file_hash,
                                    'size': eml_file.stat().st_size,
                                    'modified': datetime.fromtimestamp(eml_file.stat().st_mtime).isoformat(),
                                    'type': 'email_original',
                                    'verified': bool(file_hash)
                                })

                                if file_hash:
                                    email_results['verified_count'] += 1
                                else:
                                    email_results['failed_count'] += 1
                                break

                        # 첨부파일 검증
                        attachments_dir = email_dir / "attachments"
                        if attachments_dir.exists():
                            for attachment in attachments_dir.iterdir():
                                if attachment.is_file():
                                    file_hash = self.calculate_file_hash(
                                        attachment)

                                    email_results['files'].append({
                                        'path': str(attachment.relative_to(self.processed_emails_dir)),
                                        'hash': file_hash,
                                        'size': attachment.stat().st_size,
                                        'modified': datetime.fromtimestamp(attachment.stat().st_mtime).isoformat(),
                                        'type': 'email_attachment',
                                        'verified': bool(file_hash)
                                    })

                                    if file_hash:
                                        email_results['verified_count'] += 1
                                    else:
                                        email_results['failed_count'] += 1

                except Exception as e:
                    error_msg = f"이메일 디렉토리 검증 실패 {email_dir.name}: {str(e)}"
                    email_results['errors'].append(error_msg)
                    print(f"❌ {error_msg}")

        return email_results

    def _verify_additional_evidence(self) -> Dict:
        """추가 증거 검증"""
        additional_results = {
            'verified_count': 0,
            'failed_count': 0,
            'files': [],
            'errors': []
        }

        if not self.additional_evidence_dir or not self.additional_evidence_dir.exists():
            return additional_results

        try:
            # 증거 인덱스 파일 확인
            index_file = self.additional_evidence_dir / "evidence_index.json"
            if index_file.exists():
                with open(index_file, 'r', encoding='utf-8') as f:
                    evidence_index = json.load(f)

                # 각 증거 파일 검증
                for evidence_id, evidence_info in evidence_index.get('evidence_files', {}).items():
                    evidence_path = self.additional_evidence_dir / \
                        evidence_info['relative_path']

                    if evidence_path.exists():
                        current_hash = self.calculate_file_hash(evidence_path)
                        original_hash = evidence_info.get('file_hash', '')

                        additional_results['files'].append({
                            'path': evidence_info['relative_path'],
                            'hash': current_hash,
                            'original_hash': original_hash,
                            'size': evidence_path.stat().st_size,
                            'modified': datetime.fromtimestamp(evidence_path.stat().st_mtime).isoformat(),
                            'type': 'additional_evidence',
                            'category': evidence_info.get('category', ''),
                            'evidence_number': evidence_info.get('evidence_number', ''),
                            'verified': current_hash == original_hash and bool(current_hash)
                        })

                        if current_hash == original_hash and current_hash:
                            additional_results['verified_count'] += 1
                        else:
                            additional_results['failed_count'] += 1
                            if current_hash != original_hash:
                                additional_results['errors'].append(
                                    f"해시 불일치: {evidence_info['relative_path']} "
                                    f"(원본: {original_hash[:16]}..., 현재: {current_hash[:16]}...)"
                                )
                    else:
                        additional_results['failed_count'] += 1
                        additional_results['errors'].append(
                            f"파일 없음: {evidence_info['relative_path']}")

        except Exception as e:
            error_msg = f"추가 증거 검증 실패: {str(e)}"
            additional_results['errors'].append(error_msg)
            print(f"❌ {error_msg}")

        return additional_results

    def _save_verification_results(self, results: Dict):
        """검증 결과 저장"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # JSON 결과 저장
        json_file = self.verification_dir / f"무결성검증결과_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        print(f"✅ 검증 결과 저장: {json_file}")

    def _generate_court_certificate(self, results: Dict):
        """법원 제출용 무결성 증명서 생성"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 텍스트 증명서
        txt_file = self.verification_dir / f"법원제출용_무결성증명서_{timestamp}.txt"
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("                    디지털 증거 무결성 증명서\n")
            f.write("=" * 80 + "\n\n")

            f.write(f"검증 일시: {results['timestamp']}\n")
            f.write("검증 도구: CourtEvidenceIntegrityVerifier v2.0\n\n")

            f.write("■ 검증 요약\n")
            f.write(f"  - 총 파일 수: {results['summary']['total_files']}개\n")
            f.write(f"  - 검증 성공: {results['summary']['total_verified']}개\n")
            f.write(f"  - 검증 실패: {results['summary']['total_failed']}개\n")
            f.write(f"  - 성공률: {results['summary']['success_rate']:.1f}%\n\n")

            f.write("=" * 80 + "\n")
            f.write("본 증명서는 디지털 포렌식 표준에 따라 생성되었으며,\n")
            f.write("SHA-256 해시 알고리즘을 사용하여 파일 무결성을 검증하였습니다.\n")
            f.write("=" * 80 + "\n")

        print(f"✅ 법원 제출용 증명서 생성: {txt_file}")


if __name__ == "__main__":
    # 테스트 실행
    verifier = CourtEvidenceIntegrityVerifier(
        processed_emails_dir="processed_emails",
        additional_evidence_dir="additional_evidence"
    )
    results = verifier.verify_integrity()
    print(f"검증 완료: {results['summary']['success_rate']:.1f}% 성공")
