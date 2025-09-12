"""
문서 자동 업데이트 시스템
파일 변경 감지 및 실시간 문서 재생성
"""
import hashlib
import json
import logging
import os
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List

try:
    from watchdog.events import FileSystemEventHandler
    from watchdog.observers import Observer
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    print("⚠️ watchdog 라이브러리가 설치되지 않았습니다. pip install watchdog로 설치하세요.")


class DocumentAutoUpdater:
    """문서 자동 업데이트 관리자"""

    def __init__(self, project_root: Path = None):
        if project_root is None:
            project_root = Path(__file__).parent.parent.parent

        self.project_root = Path(project_root)
        self.docs_root = self.project_root / "docs"
        self.logger = logging.getLogger(__name__)

        # 설정 로드
        self.config = self._load_config()

        # 상태 관리
        self.last_update = None
        self.update_count = 0
        self.file_hashes = {}
        self.is_running = False
        self.observer = None

        # 업데이트 콜백
        self.update_callbacks: List[Callable] = []

    def _load_config(self) -> Dict[str, Any]:
        """문서 설정 파일 로드"""
        config_path = self.docs_root / "docs_config.json"

        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"설정 파일 로드 실패: {e}")

        # 기본 설정
        return {
            "auto_update": {
                "enabled": True,
                "watch_directories": ["src/", "templates/"],
                "watch_files": ["*.py", "*.html", "*.md"],
                "exclude_patterns": ["__pycache__", "*.pyc", ".git", "*.log"],
                "debounce_seconds": 2
            },
            "generation_settings": {
                "formats": ["markdown", "html", "json"],
                "include_timestamps": True
            }
        }

    def add_update_callback(self, callback: Callable):
        """업데이트 콜백 함수 등록"""
        self.update_callbacks.append(callback)

    def _calculate_file_hash(self, file_path: Path) -> str:
        """파일 해시 계산"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception:
            return ""

    def _should_trigger_update(self, file_path: Path) -> bool:
        """파일 변경이 업데이트를 트리거해야 하는지 확인"""
        # 제외 패턴 확인
        exclude_patterns = self.config.get(
            "auto_update", {}).get("exclude_patterns", [])
        for pattern in exclude_patterns:
            if pattern.replace("*", "") in str(file_path):
                return False

        # 감시 대상 파일 확인
        watch_files = self.config.get(
            "auto_update", {}).get("watch_files", ["*"])
        file_extension = file_path.suffix

        for pattern in watch_files:
            if pattern == "*" or pattern.endswith(file_extension):
                return True

        return False

    def _trigger_documentation_update(self, changed_file: Path = None):
        """문서 업데이트 트리거"""
        try:
            self.logger.info(f"문서 업데이트 시작 - 변경 파일: {changed_file}")
            print(f"🔄 문서 자동 업데이트 시작 (변경: {changed_file})")

            # 디바운싱 (연속 변경 방지)
            debounce = self.config.get(
                "auto_update", {}).get("debounce_seconds", 2)
            time.sleep(debounce)

            # 문서 생성 실행
            from src.docs import generate_all_documentation

            start_time = time.time()
            result = generate_all_documentation()

            if result and 'generated_docs' in result:
                execution_time = time.time() - start_time
                self.last_update = datetime.now()
                self.update_count += 1

                # 상태 정보
                generated_docs = result['generated_docs']
                scan_result = result.get('scan_result', {})
                statistics = scan_result.get('statistics', {})

                print(f"✅ 자동 업데이트 완료 ({execution_time:.2f}초)")
                print(f"  📄 생성된 문서: {len(generated_docs)}개")
                print(
                    f"  🔍 스캔된 엔드포인트: {statistics.get('total_endpoints', 0)}개")

                # 콜백 실행
                for callback in self.update_callbacks:
                    try:
                        callback(result)
                    except Exception as e:
                        self.logger.error(f"콜백 실행 실패: {e}")

                # 업데이트 로그 저장
                self._log_update(changed_file, result)

            else:
                print("❌ 자동 업데이트 실패")
                self.logger.error("문서 생성 실패")

        except Exception as e:
            print(f"❌ 자동 업데이트 오류: {e}")
            self.logger.error(f"자동 업데이트 실패: {e}")

    def _log_update(self, changed_file: Path, result: Dict[str, Any]):
        """업데이트 로그 기록"""
        log_path = self.docs_root / "update_log.json"

        log_entry = {
            "timestamp": self.last_update.isoformat(),
            "trigger_file": str(changed_file) if changed_file else None,
            "update_count": self.update_count,
            "generated_files": list(result.get('generated_docs', {}).keys()),
            "statistics": result.get('scan_result', {}).get('statistics', {})
        }

        # 기존 로그 로드
        logs = []
        if log_path.exists():
            try:
                with open(log_path, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
            except Exception:
                pass

        # 새 로그 추가 (최대 50개 유지)
        logs.append(log_entry)
        if len(logs) > 50:
            logs = logs[-50:]

        # 로그 저장
        try:
            with open(log_path, 'w', encoding='utf-8') as f:
                json.dump(logs, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"업데이트 로그 저장 실패: {e}")


class DocumentFileHandler(FileSystemEventHandler):
    """파일 시스템 이벤트 핸들러"""

    def __init__(self, updater: DocumentAutoUpdater):
        self.updater = updater
        self.logger = logging.getLogger(__name__)

    def on_modified(self, event):
        if not event.is_directory:
            file_path = Path(event.src_path)
            if self.updater._should_trigger_update(file_path):
                print(f"📝 파일 변경 감지: {file_path}")
                # 별도 스레드에서 업데이트 실행 (블로킹 방지)
                update_thread = threading.Thread(
                    target=self.updater._trigger_documentation_update,
                    args=(file_path,),
                    daemon=True
                )
                update_thread.start()


def start_auto_updater(project_root: Path = None) -> DocumentAutoUpdater:
    """자동 업데이터 시작 (편의 함수)"""
    if not WATCHDOG_AVAILABLE:
        print("❌ watchdog 라이브러리가 필요합니다. pip install watchdog")
        return None

    updater = DocumentAutoUpdater(project_root)

    if not updater.config.get("auto_update", {}).get("enabled", True):
        print("⚠️ 자동 업데이트가 비활성화되어 있습니다.")
        return updater

    try:
        # 감시 디렉토리 설정
        watch_dirs = updater.config.get("auto_update", {}).get(
            "watch_directories", ["src/"])

        # 파일 시스템 감시 시작
        event_handler = DocumentFileHandler(updater)
        observer = Observer()

        for watch_dir in watch_dirs:
            dir_path = updater.project_root / watch_dir
            if dir_path.exists():
                observer.schedule(event_handler, str(dir_path), recursive=True)
                print(f"👁️ 디렉토리 감시 시작: {dir_path}")

        observer.start()
        updater.observer = observer
        updater.is_running = True

        print("🚀 문서 자동 업데이터 시작됨")
        print("📝 파일 변경 시 자동으로 문서가 업데이트됩니다.")

        return updater

    except Exception as e:
        print(f"❌ 자동 업데이터 시작 실패: {e}")
        return None


def stop_auto_updater(updater: DocumentAutoUpdater):
    """자동 업데이터 중지"""
    if updater and updater.observer:
        updater.observer.stop()
        updater.observer.join()
        updater.is_running = False
        print("⏹️ 문서 자동 업데이터 중지됨")


def manual_update_trigger():
    """수동 문서 업데이트 트리거 (편의 함수)"""
    updater = DocumentAutoUpdater()
    updater._trigger_documentation_update()
    return updater.last_update
