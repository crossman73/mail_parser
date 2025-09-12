"""
통합 아키텍처 - 모든 컴포넌트를 연결하는 중앙 허브
"""
import json
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import psutil
except Exception:
    psutil = None


@dataclass
class SystemConfig:
    """시스템 통합 설정"""
    app_name: str = "이메일 증거 처리 시스템"
    version: str = "2.0.0"
    debug_mode: bool = False
    project_root: Path = field(default_factory=Path.cwd)
    config_data: Dict[str, Any] = field(default_factory=dict)

    # 디렉토리 구조
    uploads_dir: Path = field(default_factory=lambda: Path("uploads"))
    processed_dir: Path = field(
        default_factory=lambda: Path("processed_emails"))
    temp_dir: Path = field(default_factory=lambda: Path("temp"))
    logs_dir: Path = field(default_factory=lambda: Path("logs"))
    docs_dir: Path = field(default_factory=lambda: Path("docs"))

    def ensure_directories(self):
        """필수 디렉토리 생성"""
        for dir_path in [self.uploads_dir, self.processed_dir,
                         self.temp_dir, self.logs_dir, self.docs_dir]:
            dir_path.mkdir(exist_ok=True)


class UnifiedArchitecture:
    """통합 아키텍처 매니저"""

    def __init__(self, config: SystemConfig):
        self.config = config
        self.logger = self._setup_logging()
        self.services: Dict[str, Any] = {}
        self._initialized = False
    # track start time for uptime reporting
    self.start_time = datetime.now()

    def initialize(self):
        """시스템 초기화"""
        if self._initialized:
            return

        self._load_configuration()
        self.config.ensure_directories()
        self._register_default_services()
        self._initialized = True

        self.logger.info(
            f"시스템 초기화 완료: {self.config.app_name} v{self.config.version}")

    def cleanup(self):
        """시스템 정리"""
        self.logger.info("시스템 정리 중...")
        self.services.clear()
        self._initialized = False

    def _setup_logging(self) -> logging.Logger:
        """통합 로깅 설정"""
        logger = logging.getLogger(self.config.app_name)

        if not logger.handlers:
            # 콘솔 핸들러
            console_handler = logging.StreamHandler()
            console_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(console_formatter)

            # 파일 핸들러
            self.config.logs_dir.mkdir(exist_ok=True)
            log_file = self.config.logs_dir / \
                f"system_{datetime.now().strftime('%Y%m%d')}.log"
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
            )
            file_handler.setFormatter(file_formatter)

            logger.addHandler(console_handler)
            logger.addHandler(file_handler)
            logger.setLevel(
                logging.INFO if not self.config.debug_mode else logging.DEBUG)

        return logger

    def _load_configuration(self):
        """설정 파일 로드"""
        try:
            # config_data가 이미 설정에 포함되어 있으면 사용
            if self.config.config_data:
                config_data = self.config.config_data
            else:
                # config.json 파일에서 로드 시도
                config_file = self.config.project_root / "config.json"
                if config_file.exists():
                    with open(config_file, 'r', encoding='utf-8') as f:
                        config_data = json.load(f)
                        self.config.config_data = config_data
                else:
                    config_data = {}

            # 설정 적용
            if 'debug' in config_data:
                self.config.debug_mode = config_data['debug']

            self.logger.info(f"설정 로드 완료: {len(config_data)} 항목")
        except Exception as e:
            print(f"설정 로드 실패: {e}")  # logger가 아직 초기화되지 않았을 수 있음

    def _register_default_services(self):
        """기본 서비스들 등록"""
        try:
            # 기본적으로 사용할 서비스들만 등록 (Phase 1)
            self.logger.info("기본 서비스 등록 중...")

            # Phase 2에서 실제 서비스들 등록 예정
            # 지금은 기본적인 구조만 설정

        except Exception as e:
            self.logger.warning(f"기본 서비스 등록 실패 (무시됨): {e}")

    def register_service(self, name: str, service_instance: Any):
        """서비스 등록"""
        self.services[name] = service_instance
        self.logger.info(f"서비스 등록: {name} - {type(service_instance).__name__}")

    def get_service(self, name: str) -> Optional[Any]:
        """서비스 조회"""
        return self.services.get(name)

    def initialize_core_services(self):
        """핵심 서비스 초기화"""
        try:
            # 기존 서비스들을 동적으로 로드
            from src.mail_parser.performance import PerformanceMonitor
            from src.mail_parser.processor import EmailEvidenceProcessor

            # 핵심 서비스들 등록
            self.register_service("email_processor",
                                  EmailEvidenceProcessor(self.config.config_data))
            self.register_service("performance_monitor",
                                  PerformanceMonitor())

            # 포렌식 무결성 서비스 (있으면 로드)
            try:
                from src.mail_parser.forensic_integrity import \
                    ForensicIntegrityService
                self.register_service("forensic_service",
                                      ForensicIntegrityService())
            except ImportError:
                self.logger.warning("포렌식 무결성 서비스를 찾을 수 없습니다")

            # 스트리밍 프로세서 (있으면 로드)
            try:
                from src.mail_parser.streaming_processor import \
                    StreamingEmailProcessor
                self.register_service(
                    "streaming_processor", StreamingEmailProcessor())
            except ImportError:
                self.logger.warning("스트리밍 프로세서를 찾을 수 없습니다")

            self.logger.info("핵심 서비스 초기화 완료")

        except Exception as e:
            self.logger.error(f"서비스 초기화 실패: {e}")

    def get_system_status(self) -> Dict[str, Any]:
        """시스템 상태 조회"""
        status: Dict[str, Any] = {
            "app_name": self.config.app_name,
            "version": self.config.version,
            "debug_mode": self.config.debug_mode,
            "registered_services": list(self.services.keys()),
            "directories": {
                "uploads": str(self.config.uploads_dir),
                "processed": str(self.config.processed_dir),
                "temp": str(self.config.temp_dir),
                "logs": str(self.config.logs_dir),
                "docs": str(self.config.docs_dir)
            },
            "timestamp": datetime.now().isoformat()
        }

        # Uptime (seconds)
        try:
            status['uptime_seconds'] = (
                datetime.now() - self.start_time).total_seconds()
        except Exception:
            status['uptime_seconds'] = None

        # psutil-based system/process metrics (best-effort)
        try:
            if psutil:
                # overall CPU and memory
                status['system_cpu_percent'] = psutil.cpu_percent(interval=0.1)
                vm = psutil.virtual_memory()
                status['system_memory'] = {
                    'total': vm.total,
                    'available': vm.available,
                    'percent': vm.percent,
                    'used': vm.used,
                    'free': vm.free
                }

                # current process metrics
                proc = psutil.Process(os.getpid())
                # cpu_percent with short interval; may report 0.0 on first call
                status['process_cpu_percent'] = proc.cpu_percent(interval=0.1)
                mem = proc.memory_info()
                status['process_memory'] = {
                    'rss': getattr(mem, 'rss', None),
                    'vms': getattr(mem, 'vms', None),
                }
                status['process_threads'] = proc.num_threads()

                # port listening check (5000)
                try:
                    conns = psutil.net_connections(kind='inet')
                    status['port_5000_listening'] = any(
                        (c.laddr and getattr(c.laddr, 'port', None)
                         == 5000 and c.status == 'LISTEN')
                        for c in conns
                    )
                except Exception:
                    status['port_5000_listening'] = None
            else:
                status['system_cpu_percent'] = None
                status['system_memory'] = None
                status['process_cpu_percent'] = None
                status['process_memory'] = None
                status['process_threads'] = None
                status['port_5000_listening'] = None
        except Exception as e:
            # non-fatal: include error note
            status['metrics_error'] = str(e)

        # DB connectivity quick check (best-effort)
        try:
            from src.core import db_manager

            try:
                # attempt a harmless read
                _ = db_manager.get_setting('DEV_RELOAD_TOKEN')
                status['db_accessible'] = True
            except Exception:
                status['db_accessible'] = False
        except Exception:
            status['db_accessible'] = False

        return status


# 전역 아키텍처 인스턴스
_unified_arch = None


def get_unified_architecture(config_path: Optional[Path] = None) -> UnifiedArchitecture:
    """통합 아키텍처 싱글톤 인스턴스 반환"""
    global _unified_arch
    if _unified_arch is None:
        # SystemConfig 생성
        config = SystemConfig(project_root=Path.cwd())
        _unified_arch = UnifiedArchitecture(config)
        _unified_arch.initialize()
    return _unified_arch
