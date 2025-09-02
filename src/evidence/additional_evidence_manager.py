"""
추가 증거 자료 관리 시스템
Additional Evidence Manager for Court Submission

이메일 외의 추가 증거 자료들을 관리하고 법원 제출 형식에 맞게 처리합니다.
- 계약서, 회의록, 사진, 음성파일, 영상파일 등
- 증거번호 자동 할당 및 분류
- 메타데이터 자동 생성
- 법원 제출 형식 준수
"""

import hashlib
import json
import mimetypes
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class AdditionalEvidenceManager:
    """추가 증거 자료 관리자"""

    def __init__(self, base_dir: str = "processed_emails"):
        self.base_dir = Path(base_dir)
        self.additional_evidence_dir = self.base_dir / "05_추가증거"
        self.metadata_file = self.additional_evidence_dir / "추가증거_목록.json"

        # 지원되는 파일 형식 정의
        self.allowed_formats = {
            'documents': ['.pdf', '.doc', '.docx', '.hwp', '.txt', '.rtf'],
            'images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff'],
            'audio': ['.mp3', '.wav', '.m4a', '.aac', '.wma'],
            'video': ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv'],
            'archives': ['.zip', '.rar', '.7z', '.tar', '.gz'],
            'spreadsheets': ['.xls', '.xlsx', '.csv'],
            'presentations': ['.ppt', '.pptx']
        }

        # 증거 분류별 한글 이름
        self.category_names = {
            'documents': '문서류',
            'images': '이미지',
            'audio': '음성파일',
            'video': '영상파일',
            'archives': '압축파일',
            'spreadsheets': '스프레드시트',
            'presentations': '프레젠테이션',
            'other': '기타'
        }

        self._ensure_directories()
        self._load_metadata()

    def _ensure_directories(self):
        """필요한 디렉토리 구조 생성"""
        self.additional_evidence_dir.mkdir(parents=True, exist_ok=True)

        # 카테고리별 하위 디렉토리 생성
        for category in self.category_names.keys():
            category_dir = self.additional_evidence_dir / category
            category_dir.mkdir(exist_ok=True)

    def _load_metadata(self):
        """메타데이터 파일 로드"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    self.metadata = json.load(f)
            except Exception:
                self.metadata = self._create_empty_metadata()
        else:
            self.metadata = self._create_empty_metadata()

    def _create_empty_metadata(self) -> Dict:
        """빈 메타데이터 구조 생성"""
        return {
            'created_at': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat(),
            'total_files': 0,
            'evidence_counter': 0,
            'files': {},
            'categories': {cat: 0 for cat in self.category_names.keys()}
        }

    def _save_metadata(self):
        """메타데이터 파일 저장"""
        self.metadata['last_updated'] = datetime.now().isoformat()
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, ensure_ascii=False, indent=2)

    def _get_file_category(self, file_path: Path) -> str:
        """파일 확장자로 카테고리 판별"""
        extension = file_path.suffix.lower()

        for category, extensions in self.allowed_formats.items():
            if extension in extensions:
                return category

        return 'other'

    def _generate_evidence_number(self, category: str, party: str = '갑') -> str:
        """증거번호 자동 생성"""
        self.metadata['evidence_counter'] += 1
        evidence_num = self.metadata['evidence_counter']

        # 카테고리별 접두사
        category_prefix = {
            'documents': '문서',
            'images': '사진',
            'audio': '음성',
            'video': '영상',
            'archives': '압축',
            'spreadsheets': '표',
            'presentations': '발표',
            'other': '기타'
        }

        prefix = category_prefix.get(category, '기타')
        return f"{party}제{evidence_num}호증({prefix})"

    def add_evidence_file(self,
                          file_path: str,
                          title: str,
                          description: str = "",
                          party: str = "갑",
                          evidence_date: str = None,
                          related_email_ids: List[str] = None) -> Dict:
        """
        추가 증거 파일 등록

        Args:
            file_path: 원본 파일 경로
            title: 증거 제목
            description: 증거 설명
            party: 당사자 구분 (갑/을)
            evidence_date: 증거 발생 일자 (YYYY-MM-DD)
            related_email_ids: 관련 이메일 ID 목록
        """
        try:
            source_path = Path(file_path)
            if not source_path.exists():
                raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")

            # 파일 정보 수집
            file_size = source_path.stat().st_size
            file_hash = self._calculate_file_hash(source_path)
            category = self._get_file_category(source_path)
            evidence_number = self._generate_evidence_number(category, party)

            # 파일명 생성 (법원 제출 규격)
            safe_title = self._sanitize_filename(title)
            new_filename = f"{evidence_number}_{safe_title}{source_path.suffix}"

            # 목적지 경로
            dest_dir = self.additional_evidence_dir / category
            dest_path = dest_dir / new_filename

            # 파일 복사
            shutil.copy2(source_path, dest_path)

            # 메타데이터 생성
            file_id = f"add_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(str(dest_path))}"
            file_metadata = {
                'file_id': file_id,
                'original_path': str(source_path),
                'current_path': str(dest_path.relative_to(self.base_dir)),
                'evidence_number': evidence_number,
                'title': title,
                'description': description,
                'category': category,
                'category_name': self.category_names[category],
                'party': party,
                'evidence_date': evidence_date or datetime.now().strftime('%Y-%m-%d'),
                'file_size': file_size,
                'file_hash': file_hash,
                'mime_type': mimetypes.guess_type(str(source_path))[0],
                'added_at': datetime.now().isoformat(),
                'related_email_ids': related_email_ids or [],
                'court_compliant': True
            }

            # 메타데이터 업데이트
            self.metadata['files'][file_id] = file_metadata
            self.metadata['total_files'] += 1
            self.metadata['categories'][category] += 1
            self._save_metadata()

            print(f"✅ 추가 증거 등록 완료: {evidence_number}")
            print(f"   제목: {title}")
            print(f"   카테고리: {self.category_names[category]}")
            print(f"   파일: {new_filename}")

            return file_metadata

        except Exception as e:
            print(f"❌ 추가 증거 등록 실패: {str(e)}")
            raise

    def _sanitize_filename(self, filename: str) -> str:
        """파일명 안전화 (법원 제출용)"""
        # 특수문자 제거 및 공백을 언더스코어로 변경
        import re
        safe_name = re.sub(r'[<>:"/\\|?*]', '', filename)
        safe_name = re.sub(r'\s+', '_', safe_name)
        return safe_name[:50]  # 길이 제한

    def _calculate_file_hash(self, file_path: Path) -> str:
        """파일 SHA-256 해시 계산"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()

    def get_evidence_list(self, category: str = None, party: str = None) -> List[Dict]:
        """증거 목록 조회"""
        files = list(self.metadata['files'].values())

        if category:
            files = [f for f in files if f['category'] == category]

        if party:
            files = [f for f in files if f['party'] == party]

        # 증거번호 순으로 정렬
        files.sort(key=lambda x: x['evidence_number'])
        return files

    def get_evidence_by_id(self, file_id: str) -> Optional[Dict]:
        """ID로 특정 증거 조회"""
        return self.metadata['files'].get(file_id)

    def remove_evidence(self, file_id: str) -> bool:
        """증거 제거"""
        try:
            if file_id not in self.metadata['files']:
                return False

            file_info = self.metadata['files'][file_id]
            file_path = self.base_dir / file_info['current_path']

            # 파일 삭제
            if file_path.exists():
                file_path.unlink()

            # 메타데이터에서 제거
            category = file_info['category']
            del self.metadata['files'][file_id]
            self.metadata['total_files'] -= 1
            self.metadata['categories'][category] -= 1
            self._save_metadata()

            print(f"✅ 증거 제거 완료: {file_info['evidence_number']}")
            return True

        except Exception as e:
            print(f"❌ 증거 제거 실패: {str(e)}")
            return False

    def update_evidence_metadata(self, file_id: str, updates: Dict) -> bool:
        """증거 메타데이터 업데이트"""
        try:
            if file_id not in self.metadata['files']:
                return False

            # 허용된 필드만 업데이트
            allowed_fields = ['title', 'description',
                              'evidence_date', 'related_email_ids']
            for field in allowed_fields:
                if field in updates:
                    self.metadata['files'][file_id][field] = updates[field]

            self._save_metadata()
            return True

        except Exception as e:
            print(f"❌ 메타데이터 업데이트 실패: {str(e)}")
            return False

    def generate_evidence_index(self) -> str:
        """증거목록서 생성"""
        try:
            index_content = []
            index_content.append("추가 증거 목록서")
            index_content.append("=" * 40)
            index_content.append(
                f"작성일시: {datetime.now().strftime('%Y년 %m월 %d일 %H시 %M분')}")
            index_content.append(f"총 증거 수: {self.metadata['total_files']}건")
            index_content.append("")

            # 카테고리별 통계
            index_content.append("카테고리별 현황:")
            for category, count in self.metadata['categories'].items():
                if count > 0:
                    index_content.append(
                        f"  - {self.category_names[category]}: {count}건")
            index_content.append("")

            # 증거 목록
            index_content.append("증거 목록:")
            index_content.append("-" * 80)
            index_content.append(
                f"{'증거번호':<20} {'제목':<30} {'카테고리':<15} {'크기':<10} {'일자'}")
            index_content.append("-" * 80)

            evidence_list = self.get_evidence_list()
            for evidence in evidence_list:
                size_kb = evidence['file_size'] / 1024
                index_content.append(
                    f"{evidence['evidence_number']:<20} "
                    f"{evidence['title'][:28]:<30} "
                    f"{evidence['category_name']:<15} "
                    f"{size_kb:>8.1f}KB "
                    f"{evidence['evidence_date']}"
                )

            index_content.append("-" * 80)
            index_content.append("")
            index_content.append("본 목록서는 법원 제출용 추가 증거 자료의 색인입니다.")

            # 파일 저장
            index_file = self.additional_evidence_dir / \
                f"추가증거목록서_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(index_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(index_content))

            print(f"📋 증거목록서 생성 완료: {index_file.name}")
            return str(index_file)

        except Exception as e:
            print(f"❌ 증거목록서 생성 실패: {str(e)}")
            raise

    def get_statistics(self) -> Dict:
        """통계 정보 반환"""
        return {
            'total_files': self.metadata['total_files'],
            'categories': dict(self.metadata['categories']),
            'category_names': self.category_names,
            'last_updated': self.metadata['last_updated'],
            'evidence_counter': self.metadata['evidence_counter']
        }

    def export_for_court_submission(self) -> str:
        """법원 제출용 패키징"""
        try:
            # 패키징 디렉토리 생성
            export_dir = self.base_dir / \
                f"법원제출용_추가증거_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            export_dir.mkdir(exist_ok=True)

            # 카테고리별로 파일 복사
            for category, count in self.metadata['categories'].items():
                if count > 0:
                    category_export_dir = export_dir / \
                        f"{self.category_names[category]}"
                    category_export_dir.mkdir(exist_ok=True)

                    category_files = self.get_evidence_list(category=category)
                    for file_info in category_files:
                        source_path = self.base_dir / file_info['current_path']
                        if source_path.exists():
                            shutil.copy2(source_path, category_export_dir)

            # 증거목록서 생성
            index_file = self.generate_evidence_index()
            shutil.copy2(index_file, export_dir)

            # 메타데이터 JSON 복사
            if self.metadata_file.exists():
                shutil.copy2(self.metadata_file, export_dir)

            print(f"📦 법원 제출용 패키징 완료: {export_dir.name}")
            return str(export_dir)

        except Exception as e:
            print(f"❌ 법원 제출용 패키징 실패: {str(e)}")
            raise


# 사용 예시
if __name__ == "__main__":
    manager = AdditionalEvidenceManager()

    # 통계 출력
    stats = manager.get_statistics()
    print("📊 추가 증거 현황:")
    print(f"  총 파일 수: {stats['total_files']}개")
    for category, count in stats['categories'].items():
        if count > 0:
            print(f"  {stats['category_names'][category]}: {count}개")
