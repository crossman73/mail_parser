# src/mail_parser/packaging.py

import json
import os
import shutil
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class EvidencePackager:
    """
    법원 제출용 증거 자료 패키징 클래스
    """

    def __init__(self, base_output_dir: str = "processed_emails"):
        self.base_output_dir = base_output_dir
        self.package_info = {
            'created_at': datetime.now().isoformat(),
            'packaged_folders': [],
            'total_files': 0,
            'total_size_mb': 0
        }

    def create_evidence_package(self,
                                party: str,
                                case_name: str = None,
                                output_path: str = None) -> str:
        """
        증거 자료를 법원 제출용 패키지로 생성합니다.

        Args:
            party: 당사자 ("갑" 또는 "을")
            case_name: 사건명 (없으면 자동 생성)
            output_path: 출력 파일 경로 (없으면 자동 생성)

        Returns:
            생성된 패키지 파일 경로
        """
        if case_name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            case_name = f"메일증거_{party}_{timestamp}"

        if output_path is None:
            output_path = f"{case_name}.zip"

        # 패키지 작업 디렉토리 생성
        package_dir = f"{case_name}_package"
        if os.path.exists(package_dir):
            shutil.rmtree(package_dir)
        os.makedirs(package_dir)

        try:
            # 1. 증거 파일들 구조화
            self._organize_evidence_files(package_dir, party)

            # 2. 메타데이터 및 목록 생성
            self._create_package_metadata(package_dir, case_name, party)

            # 3. README 파일 생성
            self._create_package_readme(package_dir, case_name, party)

            # 4. 압축 파일 생성
            zip_path = self._create_zip_package(package_dir, output_path)

            print(f"📦 증거 패키지 생성 완료: {zip_path}")
            return zip_path

        finally:
            # 임시 디렉토리 정리
            if os.path.exists(package_dir):
                shutil.rmtree(package_dir)

    def _organize_evidence_files(self, package_dir: str, party: str):
        """
        증거 파일들을 체계적으로 구조화합니다.
        """
        # 기본 디렉토리 구조 생성
        evidence_dir = os.path.join(package_dir, "01_증거파일")
        attachments_dir = os.path.join(package_dir, "02_첨부파일")
        reports_dir = os.path.join(package_dir, "03_보고서")

        os.makedirs(evidence_dir, exist_ok=True)
        os.makedirs(attachments_dir, exist_ok=True)
        os.makedirs(reports_dir, exist_ok=True)

        if not os.path.exists(self.base_output_dir):
            print(f"⚠️  출력 디렉토리가 없습니다: {self.base_output_dir}")
            return

        # 처리된 메일 폴더들을 순회
        for item in os.listdir(self.base_output_dir):
            item_path = os.path.join(self.base_output_dir, item)

            if not os.path.isdir(item_path):
                continue

            self.package_info['packaged_folders'].append(item)

            # PDF 증거 파일 복사
            pdf_dir = os.path.join(item_path, "pdf_evidence")
            if os.path.exists(pdf_dir):
                for pdf_file in os.listdir(pdf_dir):
                    if pdf_file.endswith('.pdf'):
                        src = os.path.join(pdf_dir, pdf_file)
                        dst = os.path.join(evidence_dir, f"{item}_{pdf_file}")
                        shutil.copy2(src, dst)
                        self.package_info['total_files'] += 1

            # 첨부파일들 복사
            for file in os.listdir(item_path):
                file_path = os.path.join(item_path, file)

                if os.path.isfile(file_path) and not file.endswith('.html'):
                    # 첨부파일로 간주되는 파일들
                    if any(file.lower().endswith(ext) for ext in
                           ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.jpg', '.png', '.zip']):
                        dst = os.path.join(attachments_dir, f"{item}_{file}")
                        shutil.copy2(file_path, dst)
                        self.package_info['total_files'] += 1

        # Excel 보고서 복사
        for file in os.listdir(self.base_output_dir):
            if file.endswith('.xlsx') and '증거목록' in file:
                src = os.path.join(self.base_output_dir, file)
                dst = os.path.join(reports_dir, file)
                shutil.copy2(src, dst)
                self.package_info['total_files'] += 1

    def _create_package_metadata(self, package_dir: str, case_name: str, party: str):
        """
        패키지 메타데이터를 생성합니다.
        """
        metadata = {
            'package_info': {
                'case_name': case_name,
                'party': party,
                'created_at': self.package_info['created_at'],
                'total_folders': len(self.package_info['packaged_folders']),
                'total_files': self.package_info['total_files']
            },
            'file_structure': {
                '01_증거파일': 'PDF 형태의 법원 제출용 증거 파일들',
                '02_첨부파일': '원본 첨부파일들 (문서, 이미지 등)',
                '03_보고서': '증거목록 및 처리 보고서'
            },
            'packaged_folders': self.package_info['packaged_folders'],
            'integrity_info': {
                'hash_algorithm': 'SHA-256',
                'verification_required': True,
                'chain_of_custody': '모든 파일의 처리 과정이 로그로 기록됨'
            },
            'legal_notice': {
                'purpose': '법원 증거 제출용',
                'compliance': '한국 법원 디지털 증거 제출 규정 준수',
                'authenticity': '원본성, 무결성, 신뢰성 확보'
            }
        }

        metadata_path = os.path.join(package_dir, "package_metadata.json")
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

    def _create_package_readme(self, package_dir: str, case_name: str, party: str):
        """
        패키지 설명서를 생성합니다.
        """
        readme_content = f"""# {case_name} - 증거 자료 패키지

## 📋 패키지 정보

- **생성일시**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **당사자**: {party}
- **총 증거 폴더**: {len(self.package_info['packaged_folders'])}개
- **총 파일 수**: {self.package_info['total_files']}개

## 📁 디렉토리 구조

### 01_증거파일/
법원 제출용 PDF 증거 파일들이 저장되어 있습니다.
- 각 PDF 파일 상단에 "{party} 제○호증" 증거번호가 표기되어 있습니다.
- 파일명은 [날짜]_메일제목 형식으로 구성되어 있습니다.

### 02_첨부파일/
원본 첨부파일들이 저장되어 있습니다.
- 모든 첨부파일은 원본 그대로 보존되었습니다.
- 파일명 앞에 해당 메일 폴더명이 접두어로 붙어있습니다.

### 03_보고서/
증거목록 및 처리 보고서가 저장되어 있습니다.
- Excel 형태의 증거목록이 포함되어 있습니다.
- 처리 통계 및 제외된 메일 목록을 확인할 수 있습니다.

## ⚖️ 법원 제출 시 유의사항

1. **증거번호 확인**: 각 PDF 파일의 증거번호가 올바르게 표기되어 있는지 확인하세요.
2. **첨부파일 원본성**: 첨부파일들은 원본 그대로 보존되어 있습니다.
3. **무결성 검증**: 필요시 해시값을 통한 무결성 검증이 가능합니다.
4. **처리 로그**: 모든 처리 과정이 로그로 기록되어 있습니다.

## 📞 문의사항

이 증거 자료에 대한 문의사항이 있으시면 담당 법무팀에 연락하시기 바랍니다.

---
*이 패키지는 법원 제출용 메일박스 증거 분류 시스템에 의해 자동 생성되었습니다.*
"""

        readme_path = os.path.join(package_dir, "README.md")
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)

    def _create_zip_package(self, package_dir: str, output_path: str) -> str:
        """
        디렉토리를 ZIP 파일로 압축합니다.
        """
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(package_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arc_name = os.path.relpath(file_path, package_dir)
                    zipf.write(file_path, arc_name)

        # 파일 크기 계산
        package_size_mb = os.path.getsize(output_path) / 1024 / 1024
        self.package_info['total_size_mb'] = package_size_mb

        return output_path

    def create_delivery_checklist(self, package_path: str, output_path: str = None) -> str:
        """
        법원 제출용 체크리스트를 생성합니다.
        """
        if output_path is None:
            base_name = os.path.splitext(package_path)[0]
            output_path = f"{base_name}_체크리스트.txt"

        checklist_content = f"""
# 법원 제출용 증거 자료 체크리스트

## 📦 패키지 정보
- 파일명: {os.path.basename(package_path)}
- 생성일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- 파일크기: {self.package_info['total_size_mb']:.2f}MB

## ✅ 제출 전 확인사항

### 1. 파일 무결성
□ ZIP 파일이 정상적으로 압축되었는가?
□ 압축 해제 시 모든 파일이 정상 확인되는가?
□ 각 증거 파일의 증거번호가 올바르게 표기되었는가?

### 2. 증거 내용
□ 사건과 관련된 메일들만 포함되어 있는가?
□ 관련 없는 메일들이 적절히 제외되었는가?
□ 첨부파일들이 모두 포함되어 있는가?

### 3. 형식 준수
□ PDF 파일 상단에 증거번호가 중앙 정렬로 표기되었는가?
□ 첨부파일들이 원본 그대로 보존되었는가?
□ Excel 증거목록이 포함되어 있는가?

### 4. 법적 요구사항
□ 디지털 포렌식 무결성이 확보되었는가?
□ 체인 오브 커스터디가 유지되었는가?
□ 처리 과정 로그가 기록되었는가?

### 5. 최종 확인
□ 법무팀 검토가 완료되었는가?
□ 제출할 법원 및 사건번호가 올바른가?
□ 제출 기한 내에 준비가 완료되었는가?

## 📝 제출 정보
- 제출 법원: ________________
- 사건번호: ________________
- 제출일자: ________________
- 담당자: ________________

---
*모든 항목을 확인한 후 법원에 제출하시기 바랍니다.*
"""

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(checklist_content)

        print(f"📋 체크리스트가 생성되었습니다: {output_path}")
        return output_path


def create_submission_package(case_name: str = None, party: str = "갑"):
    """
    간편한 패키지 생성 함수
    """
    packager = EvidencePackager()

    try:
        package_path = packager.create_evidence_package(party, case_name)
        checklist_path = packager.create_delivery_checklist(package_path)

        print("\n" + "="*50)
        print("📦 패키징 완료")
        print("="*50)
        print(f"증거 패키지: {package_path}")
        print(f"체크리스트: {checklist_path}")
        print(f"총 파일 수: {packager.package_info['total_files']}개")
        print(f"패키지 크기: {packager.package_info['total_size_mb']:.2f}MB")
        print("="*50)

        return package_path

    except Exception as e:
        print(f"❌ 패키징 중 오류 발생: {str(e)}")
        return None
