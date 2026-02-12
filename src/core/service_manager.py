"""Service management module for controlling background services."""

import logging
import os
import subprocess
import threading
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ServiceStatus(Enum):
    """Service status enum."""

    RUNNING = "running"
    STOPPED = "stopped"
    IDLE = "idle"
    ERROR = "error"
    STARTING = "starting"
    STOPPING = "stopping"


class ServiceCategory(Enum):
    """Service category enum."""

    CORE = "core"
    BACKGROUND = "background"
    DATABASE = "database"
    MONITORING = "monitoring"


@dataclass
class ServiceInfo:
    """Service information data class."""

    id: str
    name: str
    description: str
    category: ServiceCategory
    status: ServiceStatus = ServiceStatus.STOPPED
    uptime: str = "0s"
    restart_count: int = 0
    last_update: str = ""
    pid: Optional[int] = None
    start_time: Optional[datetime] = None
    log_file: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "status": self.status.value,
            "uptime": self.uptime,
            "restart_count": self.restart_count,
            "last_update": self.last_update or datetime.now().isoformat(),
            "pid": self.pid,
        }


class ServiceRegistry:
    """Registry for managing application services."""

    _instance: Optional["ServiceRegistry"] = None
    _lock = threading.Lock()
    _initialized: bool = False

    def __new__(cls) -> "ServiceRegistry":
        """Singleton pattern implementation."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        """Initialize the service registry."""
        if getattr(self, "_initialized", False):
            return
        self._services: Dict[str, ServiceInfo] = {}
        self._processes: Dict[str, "subprocess.Popen[bytes]"] = {}
        self._base_path = Path(__file__).parent.parent.parent
        self._logs_dir = self._base_path / "logs"
        self._register_default_services()
        self._initialized = True

    def _register_default_services(self) -> None:
        """Register default application services."""
        defaults = [
            ServiceInfo(
                id="flask-app",
                name="Flask Application",
                description="메인 웹 애플리케이션 서버",
                category=ServiceCategory.CORE,
                status=ServiceStatus.RUNNING,  # Always running in context
                log_file="flask_app.log",
            ),
            ServiceInfo(
                id="email-processor",
                name="Email Processor",
                description="이메일 파싱 및 처리 서비스",
                category=ServiceCategory.BACKGROUND,
                status=ServiceStatus.STOPPED,
                log_file="email_processor.log",
            ),
            ServiceInfo(
                id="database",
                name="SQLite Database",
                description="데이터베이스 서비스",
                category=ServiceCategory.DATABASE,
                status=ServiceStatus.RUNNING,  # SQLite is always available
                log_file="database.log",
            ),
            ServiceInfo(
                id="log-monitor",
                name="Log Monitor",
                description="로그 모니터링 서비스",
                category=ServiceCategory.MONITORING,
                status=ServiceStatus.IDLE,
                log_file="log_monitor.log",
            ),
        ]
        for svc in defaults:
            self._services[svc.id] = svc

    def get_all_services(self) -> List[ServiceInfo]:
        """Get all registered services."""
        self._update_service_status()
        return list(self._services.values())

    def get_service(self, service_id: str) -> Optional[ServiceInfo]:
        """Get a specific service by ID."""
        self._update_service_status()
        return self._services.get(service_id)

    def _update_service_status(self) -> None:
        """Update service status and uptime."""
        now = datetime.now()
        for svc in self._services.values():
            svc.last_update = now.isoformat()
            if svc.start_time and svc.status == ServiceStatus.RUNNING:
                delta = now - svc.start_time
                hours, remainder = divmod(int(delta.total_seconds()), 3600)
                minutes, seconds = divmod(remainder, 60)
                if hours > 0:
                    svc.uptime = f"{hours}h {minutes}m"
                elif minutes > 0:
                    svc.uptime = f"{minutes}m {seconds}s"
                else:
                    svc.uptime = f"{seconds}s"

    def start_service(self, service_id: str) -> bool:
        """Start a service."""
        svc = self._services.get(service_id)
        if not svc:
            logger.error(f"Service not found: {service_id}")
            return False

        if svc.status == ServiceStatus.RUNNING:
            logger.info(f"Service already running: {service_id}")
            return True

        try:
            svc.status = ServiceStatus.STARTING
            svc.last_update = datetime.now().isoformat()

            # Simulate service start (actual implementation would spawn process)
            svc.status = ServiceStatus.RUNNING
            svc.start_time = datetime.now()
            svc.pid = os.getpid()  # Placeholder
            logger.info(f"Service started: {service_id}")
            return True
        except Exception as e:
            logger.exception(f"Failed to start service {service_id}: {e}")
            svc.status = ServiceStatus.ERROR
            return False

    def stop_service(self, service_id: str) -> bool:
        """Stop a service."""
        svc = self._services.get(service_id)
        if not svc:
            logger.error(f"Service not found: {service_id}")
            return False

        if svc.status == ServiceStatus.STOPPED:
            logger.info(f"Service already stopped: {service_id}")
            return True

        # Prevent stopping core services
        if service_id in ("flask-app", "database"):
            logger.warning(f"Cannot stop core service: {service_id}")
            return False

        try:
            svc.status = ServiceStatus.STOPPING
            svc.last_update = datetime.now().isoformat()

            # Terminate process if exists
            if service_id in self._processes:
                proc = self._processes.pop(service_id)
                proc.terminate()
                proc.wait(timeout=5)

            svc.status = ServiceStatus.STOPPED
            svc.pid = None
            svc.start_time = None
            svc.uptime = "0s"
            logger.info(f"Service stopped: {service_id}")
            return True
        except Exception as e:
            logger.exception(f"Failed to stop service {service_id}: {e}")
            svc.status = ServiceStatus.ERROR
            return False

    def restart_service(self, service_id: str) -> bool:
        """Restart a service."""
        svc = self._services.get(service_id)
        if not svc:
            return False

        if service_id not in ("flask-app", "database"):
            self.stop_service(service_id)

        result = self.start_service(service_id)
        if result:
            svc.restart_count += 1
        return result

    def get_service_logs(
        self, service_id: str, lines: int = 100
    ) -> Optional[str]:
        """Get recent logs for a service."""
        svc = self._services.get(service_id)
        if not svc or not svc.log_file:
            return None

        log_path = self._logs_dir / svc.log_file
        if not log_path.exists():
            # Return placeholder if log doesn't exist
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return f"[{now}] INFO: {svc.name} - No log entries yet."

        try:
            with open(log_path, "r", encoding="utf-8") as f:
                all_lines = f.readlines()
                return "".join(all_lines[-lines:])
        except Exception as e:
            logger.error(f"Failed to read logs for {service_id}: {e}")
            return None

    def start_all(self) -> int:
        """Start all stoppable services."""
        started = 0
        for svc_id, svc in self._services.items():
            if svc.status != ServiceStatus.RUNNING:
                if self.start_service(svc_id):
                    started += 1
        return started

    def stop_all(self) -> int:
        """Stop all stoppable services (except core)."""
        stopped = 0
        for svc_id, svc in self._services.items():
            if svc_id not in ("flask-app", "database"):
                if svc.status == ServiceStatus.RUNNING:
                    if self.stop_service(svc_id):
                        stopped += 1
        return stopped

    def restart_all(self) -> int:
        """Restart all services."""
        restarted = 0
        for svc_id in self._services:
            if self.restart_service(svc_id):
                restarted += 1
        return restarted


# Singleton accessor
def get_service_registry() -> ServiceRegistry:
    """Get the global service registry instance."""
    return ServiceRegistry()
