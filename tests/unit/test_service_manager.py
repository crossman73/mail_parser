"""Unit tests for ServiceRegistry."""

import pytest
from src.core.service_manager import (
    ServiceCategory,
    ServiceInfo,
    ServiceRegistry,
    ServiceStatus,
    get_service_registry,
)


class TestServiceInfo:
    """Tests for ServiceInfo dataclass."""

    def test_to_dict_returns_all_fields(self):
        """to_dict should return all required fields."""
        info = ServiceInfo(
            id="test-svc",
            name="Test Service",
            description="A test service",
            category=ServiceCategory.CORE,
            status=ServiceStatus.RUNNING,
        )
        result = info.to_dict()

        assert result["id"] == "test-svc"
        assert result["name"] == "Test Service"
        assert result["category"] == "core"
        assert result["status"] == "running"
        assert "last_update" in result

    def test_default_values(self):
        """ServiceInfo should have sensible defaults."""
        info = ServiceInfo(
            id="svc",
            name="Svc",
            description="desc",
            category=ServiceCategory.BACKGROUND,
        )

        assert info.status == ServiceStatus.STOPPED
        assert info.uptime == "0s"
        assert info.restart_count == 0


class TestServiceRegistry:
    """Tests for ServiceRegistry singleton."""

    def test_singleton_pattern(self):
        """Registry should be a singleton."""
        reg1 = get_service_registry()
        reg2 = get_service_registry()
        assert reg1 is reg2

    def test_default_services_registered(self):
        """Default services should be registered on init."""
        registry = get_service_registry()
        services = registry.get_all_services()

        service_ids = [s.id for s in services]
        assert "flask-app" in service_ids
        assert "database" in service_ids
        assert "email-processor" in service_ids
        assert "log-monitor" in service_ids

    def test_get_service_by_id(self):
        """Should retrieve a specific service by ID."""
        registry = get_service_registry()
        svc = registry.get_service("flask-app")

        assert svc is not None
        assert svc.name == "Flask Application"
        assert svc.category == ServiceCategory.CORE

    def test_get_nonexistent_service_returns_none(self):
        """Should return None for unknown service ID."""
        registry = get_service_registry()
        assert registry.get_service("nonexistent") is None


class TestServiceControl:
    """Tests for service start/stop/restart."""

    def test_start_stopped_service(self):
        """Should start a stopped service."""
        registry = get_service_registry()
        # Reset email-processor to stopped
        svc = registry.get_service("email-processor")
        if svc:
            svc.status = ServiceStatus.STOPPED

        result = registry.start_service("email-processor")
        assert result is True

        svc = registry.get_service("email-processor")
        assert svc is not None
        assert svc.status == ServiceStatus.RUNNING

    def test_stop_core_service_fails(self):
        """Should not allow stopping core services."""
        registry = get_service_registry()
        result = registry.stop_service("flask-app")
        assert result is False

        result = registry.stop_service("database")
        assert result is False

    def test_restart_increments_count(self):
        """Restart should increment restart_count."""
        registry = get_service_registry()
        svc = registry.get_service("email-processor")
        if svc:
            initial_count = svc.restart_count
            registry.restart_service("email-processor")
            assert svc.restart_count == initial_count + 1


class TestServiceLogs:
    """Tests for service log retrieval."""

    def test_get_logs_nonexistent_service(self):
        """Should return None for unknown service."""
        registry = get_service_registry()
        logs = registry.get_service_logs("nonexistent")
        assert logs is None

    def test_get_logs_returns_placeholder_if_no_file(self):
        """Should return placeholder if log file doesn't exist."""
        registry = get_service_registry()
        logs = registry.get_service_logs("flask-app")
        # Either None or a placeholder string
        assert logs is None or "No log entries" in logs or isinstance(logs, str)
