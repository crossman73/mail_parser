"""
문서 디렉토리 구조 관리자
Phase 2.4: docs/ 디렉토리 체계화 및 자동 관리 시스템
"""
import json
import logging
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


class DocsStructureManager:
    """문서 디렉토리 구조 관리 클래스"""

    def __init__(self, docs_root: Path = None):
        if docs_root is None:
            docs_root = Path("docs")

        self.docs_root = Path(docs_root)
        self.logger = logging.getLogger(__name__)

        # 체계화된 디렉토리 구조 정의
        self.structure = {
            'api': {
                'description': 'API 관련 문서 (OpenAPI, Postman 등)',
                'subdirs': ['openapi', 'postman', 'references']
            },
            'guides': {
                'description': '사용자 및 개발자 가이드',
                'subdirs': ['developer', 'user', 'admin']
            },
            'assets': {
                'description': '문서용 정적 자원 (이미지, CSS, JS)',
                'subdirs': ['images', 'css', 'js', 'fonts']
            },
            'templates': {
                'description': '문서 템플릿',
                'subdirs': ['markdown', 'html']
            },
            'archive': {
                'description': '이전 버전 문서 보관',
                'subdirs': ['v1', 'legacy']
            }
        }

    def create_structured_directories(self) -> bool:
        """체계화된 디렉토리 구조 생성"""
        try:
            print("🏗️ 체계화된 디렉토리 구조 생성...")

            # 메인 디렉토리 생성
            for dir_name, config in self.structure.items():
                main_dir = self.docs_root / dir_name
                main_dir.mkdir(parents=True, exist_ok=True)

                # README 파일 생성
                readme_path = main_dir / "README.md"
                if not readme_path.exists():
                    with open(readme_path, 'w', encoding='utf-8') as f:
                        f.write(f"# {dir_name.upper()} 디렉토리\n\n")
                        f.write(f"{config['description']}\n\n")
                        f.write("## 하위 디렉토리\n\n")
                        for subdir in config['subdirs']:
                            f.write(f"- `{subdir}/` - {subdir} 관련 파일\n")
                        f.write(
                            f"\n---\n*자동 생성: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")

                # 하위 디렉토리 생성
                for subdir in config['subdirs']:
                    sub_path = main_dir / subdir
                    sub_path.mkdir(parents=True, exist_ok=True)

                    # .gitkeep 파일 생성 (빈 디렉토리 추적용)
                    gitkeep = sub_path / ".gitkeep"
                    if not gitkeep.exists():
                        gitkeep.touch()

                print(f"  ✅ {dir_name}/ 디렉토리 생성 완료")

            return True

        except Exception as e:
            self.logger.error(f"디렉토리 구조 생성 실패: {e}")
            print(f"❌ 디렉토리 구조 생성 실패: {e}")
            return False

    def organize_existing_files(self) -> bool:
        """기존 파일들을 새 구조로 이동"""
        try:
            print("📁 기존 파일들을 새 구조로 정리...")

            # 파일 분류 규칙 정의
            file_mapping = {
                # API 관련
                'openapi.json': 'api/openapi/',
                'postman_collection.json': 'api/postman/',
                'API_Reference.md': 'api/references/',

                # 가이드 문서
                'Developer_Guide.md': 'guides/developer/',
                'config_guide.md': 'guides/admin/',
                'RFP_Mail_parser.md': 'guides/user/',

                # HTML 문서
                'api_docs.html': 'api/references/',

                # 아키텍처 문서
                'architecture_refactoring.md': 'guides/developer/',
                'ARCHITECTURE.md': 'guides/developer/',
                'PROJECT_OVERVIEW.md': 'guides/developer/',
                'Timeline_System_Guide.md': 'guides/developer/',

                # 프로젝트 관리 문서
                'completion_report.md': 'archive/legacy/',
                'improvement_plan.md': 'guides/developer/'
            }

            moved_count = 0

            for filename, target_path in file_mapping.items():
                source_file = self.docs_root / filename
                if source_file.exists():
                    target_dir = self.docs_root / target_path
                    target_file = target_dir / filename

                    # 기존 파일이 있으면 백업
                    if target_file.exists():
                        backup_file = target_dir / f"{filename}.backup"
                        shutil.move(str(target_file), str(backup_file))
                        print(f"  🔄 기존 파일 백업: {backup_file}")

                    # 파일 이동
                    shutil.move(str(source_file), str(target_file))
                    print(f"  ✅ {filename} → {target_path}")
                    moved_count += 1

            print(f"📁 파일 정리 완료: {moved_count}개 파일 이동")
            return True

        except Exception as e:
            self.logger.error(f"파일 정리 실패: {e}")
            print(f"❌ 파일 정리 실패: {e}")
            return False

    def create_index_files(self) -> bool:
        """각 디렉토리에 인덱스 파일 생성"""
        try:
            print("📋 디렉토리 인덱스 파일 생성...")

            # 메인 docs 인덱스
            main_index = self.docs_root / "index.md"
            with open(main_index, 'w', encoding='utf-8') as f:
                f.write(f"""# 📚 이메일 증거 처리 시스템 문서

> 체계화된 문서 구조 v2.4 | 생성일: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 🗂️ 문서 구조

### 📁 주요 디렉토리

""")
                for dir_name, config in self.structure.items():
                    f.write(
                        f"- **[{dir_name}/]({dir_name}/)** - {config['description']}\n")

                f.write("""

### 🔗 빠른 링크

- [🔌 API 문서](api/references/API_Reference.md)
- [🌐 Swagger UI](../api/swagger-ui) (서버 실행 시)
- [📖 개발자 가이드](guides/developer/Developer_Guide.md)
- [⚙️ 설정 가이드](guides/admin/config_guide.md)

### 📊 문서 통계

이 문서는 Phase 2 API 문서 자동화 시스템에 의해 관리됩니다.

---

*자동 생성 및 관리: Phase 2.4 문서 구조 관리자*
""")

            # 각 하위 디렉토리 인덱스 생성
            for dir_name, config in self.structure.items():
                dir_path = self.docs_root / dir_name
                index_path = dir_path / "index.md"

                with open(index_path, 'w', encoding='utf-8') as f:
                    f.write(f"# {dir_name.upper()} 📁\n\n")
                    f.write(f"{config['description']}\n\n")

                    # 실제 파일들 나열
                    files = list(dir_path.rglob("*"))
                    doc_files = [f for f in files if f.is_file() and f.suffix in [
                        '.md', '.html', '.json'] and f.name not in ['index.md', 'README.md']]

                    if doc_files:
                        f.write("## 📄 파일 목록\n\n")
                        for doc_file in sorted(doc_files):
                            rel_path = doc_file.relative_to(dir_path)
                            f.write(f"- [{doc_file.name}]({rel_path})\n")

                    f.write(
                        f"\n---\n*업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")

            print("📋 인덱스 파일 생성 완료")
            return True

        except Exception as e:
            self.logger.error(f"인덱스 파일 생성 실패: {e}")
            print(f"❌ 인덱스 파일 생성 실패: {e}")
            return False

    def generate_docs_config(self) -> bool:
        """문서 설정 파일 생성"""
        try:
            config_path = self.docs_root / "docs_config.json"

            config = {
                "version": "2.4.0",
                "created": datetime.now().isoformat(),
                "structure": self.structure,
                "auto_update": {
                    "enabled": True,
                    "watch_directories": ["src/", "templates/"],
                    "watch_files": ["*.py", "*.html", "*.md"],
                    "exclude_patterns": ["__pycache__", "*.pyc", ".git"]
                },
                "generation_settings": {
                    "formats": ["markdown", "html", "json"],
                    "include_timestamps": True,
                    "include_statistics": True
                },
                "ci_cd": {
                    "github_actions": True,
                    "auto_deploy": False,
                    "quality_checks": True
                }
            }

            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            print(f"⚙️ 문서 설정 파일 생성: {config_path}")
            return True

        except Exception as e:
            self.logger.error(f"설정 파일 생성 실패: {e}")
            print(f"❌ 설정 파일 생성 실패: {e}")
            return False

    def get_structure_status(self) -> Dict[str, Any]:
        """문서 구조 상태 반환"""
        status = {
            'directories': {},
            'total_files': 0,
            'total_directories': 0
        }

        for dir_name in self.structure.keys():
            dir_path = self.docs_root / dir_name
            if dir_path.exists():
                files = list(dir_path.rglob("*"))
                file_count = len([f for f in files if f.is_file()])
                dir_count = len([f for f in files if f.is_dir()])

                status['directories'][dir_name] = {
                    'exists': True,
                    'files': file_count,
                    'subdirectories': dir_count
                }
                status['total_files'] += file_count
                status['total_directories'] += dir_count
            else:
                status['directories'][dir_name] = {'exists': False}

        return status


def reorganize_docs_structure():
    """문서 구조 재구성 메인 함수 (편의 함수)"""
    manager = DocsStructureManager()

    print("🚀 Phase 2.4: 문서 구조 재구성 시작")
    print("=" * 50)

    success_steps = 0
    total_steps = 4

    # 1. 디렉토리 구조 생성
    if manager.create_structured_directories():
        success_steps += 1

    # 2. 기존 파일 정리
    if manager.organize_existing_files():
        success_steps += 1

    # 3. 인덱스 파일 생성
    if manager.create_index_files():
        success_steps += 1

    # 4. 설정 파일 생성
    if manager.generate_docs_config():
        success_steps += 1

    # 결과 출력
    status = manager.get_structure_status()

    print("=" * 50)
    print(f"📊 문서 구조 재구성 완료: {success_steps}/{total_steps} 단계 성공")
    print(f"📁 총 디렉토리: {status['total_directories']}개")
    print(f"📄 총 파일: {status['total_files']}개")

    return success_steps == total_steps
