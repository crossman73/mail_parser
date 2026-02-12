"""Unit tests for migration_manager module."""

import pytest
from unittest.mock import MagicMock, patch


class TestMigration:
    """Tests for Migration base class."""

    def test_up_not_implemented(self):
        """up() should raise NotImplementedError."""
        from src.database.migrations.migration_manager import Migration

        migration = Migration(version=1, description="test")
        with pytest.raises(NotImplementedError):
            migration.up(None)

    def test_down_not_implemented(self):
        """down() should raise NotImplementedError."""
        from src.database.migrations.migration_manager import Migration

        migration = Migration(version=1, description="test")
        with pytest.raises(NotImplementedError):
            migration.down(None)


class TestMigrationManager:
    """Tests for MigrationManager class."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database connection."""
        db = MagicMock()
        conn = MagicMock()
        cursor = MagicMock()
        cursor.fetchone.return_value = None
        cursor.fetchall.return_value = []
        conn.cursor.return_value = cursor
        db.get_connection.return_value.__enter__ = MagicMock(return_value=conn)
        db.get_connection.return_value.__exit__ = MagicMock(return_value=False)
        return db

    def test_get_current_version_returns_zero_on_empty(self, mock_db):
        """Should return 0 when no versions exist."""
        from src.database.migrations.migration_manager import MigrationManager

        manager = MigrationManager(mock_db)
        version = manager.get_current_version()
        assert version == 0

    def test_get_current_version_returns_latest(self, mock_db):
        """Should return the latest version number."""
        from src.database.migrations.migration_manager import MigrationManager

        cursor = mock_db.get_connection.return_value.__enter__.return_value.cursor.return_value
        cursor.fetchone.return_value = (4,)

        manager = MigrationManager(mock_db)
        version = manager.get_current_version()
        assert version == 4

    def test_get_migration_history_returns_list(self, mock_db):
        """Should return migration history as list."""
        from src.database.migrations.migration_manager import MigrationManager

        cursor = mock_db.get_connection.return_value.__enter__.return_value.cursor.return_value
        cursor.fetchall.return_value = [
            (1, "Initial schema", "2026-01-01T00:00:00"),
            (2, "Add index", "2026-01-02T00:00:00"),
        ]

        manager = MigrationManager(mock_db)
        history = manager.get_migration_history()

        assert len(history) == 2
        assert history[0]["version"] == 1
        assert history[1]["description"] == "Add index"

    def test_update_version_records_migration(self, mock_db):
        """Should insert version record."""
        from src.database.migrations.migration_manager import MigrationManager

        manager = MigrationManager(mock_db)
        result = manager.update_version(5, "Test migration")

        assert result is True
        conn = mock_db.get_connection.return_value.__enter__.return_value
        conn.execute.assert_called()

    def test_get_migration_status(self, mock_db):
        """Should return status dict with current version."""
        from src.database.migrations.migration_manager import MigrationManager

        cursor = mock_db.get_connection.return_value.__enter__.return_value.cursor.return_value
        cursor.fetchone.return_value = (3,)
        cursor.fetchall.return_value = []

        manager = MigrationManager(mock_db)
        status = manager.get_migration_status()

        assert "current_version" in status
        assert "history" in status
        assert "migrations_dir" in status
        assert status["current_version"] == 3
