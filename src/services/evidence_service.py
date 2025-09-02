"""
Evidence service for managing court evidence
법정 증거 관리 서비스
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class EvidenceService:
    """증거 관리 서비스"""

    def __init__(self, output_dir: str = "processed_emails"):
        """초기화"""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # 메타데이터 파일
        self.metadata_file = self.output_dir / "evidence_metadata.json"
        self.evidence_counter = {"갑": 0, "을": 0}

        # 기존 증거 목록 로드
        self._load_existing_evidence()

    def _load_existing_evidence(self):
        """기존 증거 메타데이터 로드"""
        if not self.metadata_file.exists():
            return

        try:
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 카운터 복원
            self.evidence_counter = data.get(
                'evidence_counter', {"갑": 0, "을": 0})

        except Exception as e:
            print(f"기존 증거 목록 로드 오류: {e}")

    def get_evidence_list(self) -> List[Dict[str, Any]]:
        """증거 목록 조회"""
        evidence_list = []

        # processed_emails 디렉토리에서 증거 폴더들 검색
        if not self.output_dir.exists():
            return evidence_list

        for folder in self.output_dir.iterdir():
            if folder.is_dir() and folder.name.startswith('['):
                try:
                    # 폴더명에서 날짜와 제목 추출
                    folder_name = folder.name
                    if ']_' in folder_name:
                        date_part = folder_name.split(']_')[
                            0][1:]  # [날짜] 부분에서 [] 제거
                        title_part = folder_name.split(']_')[1]
                    else:
                        date_part = folder_name
                        title_part = "제목없음"

                    # 폴더 내 파일들 확인
                    html_files = list(folder.glob('*.html'))
                    pdf_files = list(folder.glob('*.pdf'))
                    attachment_dirs = [d for d in folder.iterdir(
                    ) if d.is_dir() and d.name == 'attachments']

                    attachment_count = 0
                    if attachment_dirs:
                        attachment_count = len(
                            list(attachment_dirs[0].iterdir()))

                    # 증거 번호 추출 (파일명에서)
                    evidence_number = "미지정"
                    if html_files:
                        html_name = html_files[0].stem
                        if html_name.startswith(('갑', '을')):
                            parts = html_name.split('_')
                            if parts:
                                evidence_number = parts[0]

                    evidence_list.append({
                        'folder_name': folder_name,
                        'folder_path': str(folder),
                        'date': date_part,
                        'title': title_part,
                        'evidence_number': evidence_number,
                        'html_files': len(html_files),
                        'pdf_files': len(pdf_files),
                        'attachment_count': attachment_count,
                        'created_time': folder.stat().st_ctime,
                        'modified_time': folder.stat().st_mtime
                    })

                except Exception as e:
                    print(f"증거 폴더 처리 오류 ({folder.name}): {e}")
                    continue

        # 날짜순 정렬
        evidence_list.sort(key=lambda x: x.get('date', ''))
        return evidence_list

    def get_evidence_details(self, folder_name: str) -> Dict[str, Any]:
        """특정 증거의 상세 정보"""
        evidence_folder = self.output_dir / folder_name

        if not evidence_folder.exists():
            return {
                'success': False,
                'message': '증거 폴더를 찾을 수 없습니다.',
                'details': {}
            }

        try:
            details = {
                'folder_name': folder_name,
                'folder_path': str(evidence_folder),
                'files': [],
                'attachments': [],
                'html_content': '',
                'metadata': {}
            }

            # 폴더 내 파일들 스캔
            for file_path in evidence_folder.iterdir():
                if file_path.is_file():
                    file_info = {
                        'name': file_path.name,
                        'path': str(file_path),
                        'size': file_path.stat().st_size,
                        'type': file_path.suffix,
                        'modified': file_path.stat().st_mtime
                    }
                    details['files'].append(file_info)

                    # HTML 내용 읽기
                    if file_path.suffix == '.html':
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                details['html_content'] = f.read()
                        except Exception as e:
                            details['html_content'] = f'HTML 읽기 오류: {e}'

            # 첨부파일 디렉토리 확인
            attachments_dir = evidence_folder / 'attachments'
            if attachments_dir.exists():
                for attachment in attachments_dir.iterdir():
                    if attachment.is_file():
                        attachment_info = {
                            'name': attachment.name,
                            'path': str(attachment),
                            'size': attachment.stat().st_size,
                            'type': attachment.suffix
                        }
                        details['attachments'].append(attachment_info)

            return {
                'success': True,
                'message': '증거 정보를 성공적으로 로드했습니다.',
                'details': details
            }

        except Exception as e:
            return {
                'success': False,
                'message': f'증거 정보 로드 오류: {str(e)}',
                'details': {}
            }

    def delete_evidence(self, folder_name: str) -> Dict[str, Any]:
        """증거 삭제"""
        evidence_folder = self.output_dir / folder_name

        if not evidence_folder.exists():
            return {
                'success': False,
                'message': '삭제할 증거 폴더를 찾을 수 없습니다.'
            }

        try:
            # 폴더와 내용 전체 삭제
            import shutil
            shutil.rmtree(evidence_folder)

            return {
                'success': True,
                'message': f'증거 "{folder_name}"이 성공적으로 삭제되었습니다.'
            }

        except Exception as e:
            return {
                'success': False,
                'message': f'증거 삭제 오류: {str(e)}'
            }

    def get_evidence_statistics(self) -> Dict[str, Any]:
        """증거 통계 정보"""
        evidence_list = self.get_evidence_list()

        if not evidence_list:
            return {
                'total_count': 0,
                'by_type': {'갑': 0, '을': 0},
                'file_stats': {'html': 0, 'pdf': 0},
                'attachment_stats': {'total_count': 0, 'avg_per_evidence': 0},
                'date_range': None
            }

        # 통계 계산
        total_count = len(evidence_list)
        type_counts = {'갑': 0, '을': 0}
        html_count = sum(e['html_files'] for e in evidence_list)
        pdf_count = sum(e['pdf_files'] for e in evidence_list)
        total_attachments = sum(e['attachment_count'] for e in evidence_list)

        # 증거 유형별 카운트
        for evidence in evidence_list:
            evidence_num = evidence['evidence_number']
            if evidence_num.startswith('갑'):
                type_counts['갑'] += 1
            elif evidence_num.startswith('을'):
                type_counts['을'] += 1

        # 날짜 범위
        dates = [e['date'] for e in evidence_list if e['date']]
        date_range = None
        if dates:
            dates.sort()
            date_range = {
                'start': dates[0],
                'end': dates[-1]
            }

        return {
            'total_count': total_count,
            'by_type': type_counts,
            'file_stats': {
                'html': html_count,
                'pdf': pdf_count
            },
            'attachment_stats': {
                'total_count': total_attachments,
                'avg_per_evidence': total_attachments / total_count if total_count > 0 else 0
            },
            'date_range': date_range
        }

    def export_evidence_list(self, format: str = 'json') -> str:
        """증거 목록 내보내기"""
        evidence_list = self.get_evidence_list()

        if format.lower() == 'json':
            return json.dumps(evidence_list, ensure_ascii=False, indent=2)

        elif format.lower() == 'csv':
            import csv
            import io

            output = io.StringIO()
            writer = csv.writer(output)

            # 헤더
            writer.writerow([
                '증거번호', '날짜', '제목', '폴더명', 'HTML파일수', 'PDF파일수', '첨부파일수'
            ])

            # 데이터
            for evidence in evidence_list:
                writer.writerow([
                    evidence['evidence_number'],
                    evidence['date'],
                    evidence['title'],
                    evidence['folder_name'],
                    evidence['html_files'],
                    evidence['pdf_files'],
                    evidence['attachment_count']
                ])

            return output.getvalue()

        return ""

    def validate_evidence_integrity(self) -> Dict[str, Any]:
        """증거 무결성 검증"""
        evidence_list = self.get_evidence_list()
        results = {
            'total_checked': 0,
            'valid_count': 0,
            'invalid_count': 0,
            'issues': []
        }

        for evidence in evidence_list:
            results['total_checked'] += 1
            folder_path = Path(evidence['folder_path'])

            # 기본 파일 존재 확인
            html_files = list(folder_path.glob('*.html'))
            pdf_files = list(folder_path.glob('*.pdf'))

            issues = []

            if not html_files:
                issues.append('HTML 파일 누락')

            if not pdf_files:
                issues.append('PDF 파일 누락')

            # 파일 크기 확인
            for html_file in html_files:
                if html_file.stat().st_size == 0:
                    issues.append(f'빈 HTML 파일: {html_file.name}')

            if issues:
                results['invalid_count'] += 1
                results['issues'].append({
                    'folder_name': evidence['folder_name'],
                    'issues': issues
                })
            else:
                results['valid_count'] += 1

        return results
