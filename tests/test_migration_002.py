"""
Tests for migration 002_create_economic_events_table.sql

TDD Approach:
- RED: Test the expected schema structure
- GREEN: Migration creates the table with correct columns
- REFACTOR: Verify idempotency

These tests verify:
1. Table exists with correct name
2. All columns exist with correct types
3. Indexes are created
4. Constraints are properly defined
5. Migration is idempotent (can be run multiple times)
"""

from pathlib import Path


class TestMigration002EconomicEvents:
    """Tests for the economic_events migration file."""

    MIGRATION_FILE = Path(__file__).parent.parent / "migrations" / "002_create_economic_events_table.sql"

    def test_migration_file_exists(self) -> None:
        """Migration file should exist."""
        assert self.MIGRATION_FILE.exists(), (
            f"Migration file does not exist: {self.MIGRATION_FILE}"
        )

    def test_migration_creates_table(self) -> None:
        """Migration should contain CREATE TABLE statement."""
        content = self.MIGRATION_FILE.read_text()
        assert "CREATE TABLE IF NOT EXISTS economic_events" in content, (
            "Migration should create economic_events table with IF NOT EXISTS"
        )

    def test_migration_has_required_columns(self) -> None:
        """Migration should define all required columns."""
        content = self.MIGRATION_FILE.read_text()
        required_columns = [
            "id",
            "timestamp",
            "currency",
            "event_name",
            "impact",
            "actual",
            "forecast",
            "previous",
            "sentiment_score",
            "raw_response",
            "created_at",
            "updated_at",
        ]
        for column in required_columns:
            assert column in content, f"Missing required column: {column}"

    def test_migration_has_primary_key(self) -> None:
        """Migration should define primary key on id column."""
        content = self.MIGRATION_FILE.read_text()
        assert "PRIMARY KEY" in content.upper() or "SERIAL PRIMARY KEY" in content.upper(), (
            "Migration should define a PRIMARY KEY"
        )

    def test_migration_has_timestamp_with_timezone(self) -> None:
        """Timestamp columns should use TIMESTAMP WITH TIME ZONE."""
        content = self.MIGRATION_FILE.read_text().upper()
        # Check for TIMESTAMPTZ or TIMESTAMP WITH TIME ZONE
        has_timestamptz = "TIMESTAMPTZ" in content or "TIMESTAMP WITH TIME ZONE" in content
        assert has_timestamptz, (
            "Migration should use TIMESTAMP WITH TIME ZONE for timestamp columns"
        )

    def test_migration_has_jsonb_for_raw_response(self) -> None:
        """raw_response column should use JSONB type."""
        content = self.MIGRATION_FILE.read_text().upper()
        assert "JSONB" in content, (
            "Migration should use JSONB for raw_response column"
        )

    def test_migration_has_required_indexes(self) -> None:
        """Migration should create required indexes."""
        content = self.MIGRATION_FILE.read_text()

        # Individual indexes
        assert "CREATE INDEX IF NOT EXISTS" in content, (
            "Migration should create indexes with IF NOT EXISTS"
        )

        # Check for specific index patterns
        content_lower = content.lower()
        assert "idx_economic_events_timestamp" in content_lower or \
               ("index" in content_lower and "timestamp" in content_lower), (
            "Migration should create index on timestamp"
        )
        assert "idx_economic_events_currency" in content_lower or \
               ("index" in content_lower and "currency" in content_lower), (
            "Migration should create index on currency"
        )
        assert "idx_economic_events_impact" in content_lower or \
               ("index" in content_lower and "impact" in content_lower), (
            "Migration should create index on impact"
        )

    def test_migration_has_composite_index(self) -> None:
        """Migration should create composite index on (timestamp, currency)."""
        content = self.MIGRATION_FILE.read_text().lower()
        # Check for composite index pattern
        assert "(timestamp, currency)" in content or "(\"timestamp\", currency)" in content, (
            "Migration should create composite index on (timestamp, currency)"
        )

    def test_migration_has_unique_constraint(self) -> None:
        """Migration should have unique constraint on (timestamp, event_name, currency)."""
        content = self.MIGRATION_FILE.read_text().upper()
        # Check for UNIQUE constraint
        assert "UNIQUE" in content, (
            "Migration should define UNIQUE constraint"
        )

    def test_migration_has_impact_constraint(self) -> None:
        """Migration should constrain impact to valid values."""
        content = self.MIGRATION_FILE.read_text().lower()
        # Should have check constraint or enum for impact values
        assert "high" in content and "medium" in content and "low" in content, (
            "Migration should define valid impact values (high/medium/low)"
        )

    def test_migration_is_idempotent(self) -> None:
        """Migration should use IF NOT EXISTS for idempotency."""
        content = self.MIGRATION_FILE.read_text()
        # All CREATE statements should have IF NOT EXISTS
        create_statements = [
            line for line in content.split('\n')
            if line.strip().upper().startswith('CREATE ')
        ]
        for stmt in create_statements:
            if 'TABLE' in stmt.upper() or 'INDEX' in stmt.upper():
                assert 'IF NOT EXISTS' in stmt.upper(), (
                    f"Statement should be idempotent: {stmt.strip()}"
                )

    def test_migration_has_down_migration(self) -> None:
        """Migration should include DROP statements for rollback."""
        content = self.MIGRATION_FILE.read_text().upper()
        assert "DROP TABLE IF EXISTS" in content, (
            "Migration should include DROP TABLE IF EXISTS for rollback"
        )

    def test_migration_has_comments(self) -> None:
        """Migration should include documentation comments."""
        content = self.MIGRATION_FILE.read_text()
        assert "-- Migration 002:" in content, (
            "Migration should have header comment with migration number"
        )
        assert "COMMENT ON TABLE economic_events" in content, (
            "Migration should add comment on table"
        )

    def test_migration_has_not_null_constraints(self) -> None:
        """Required columns should have NOT NULL constraint."""
        content = self.MIGRATION_FILE.read_text().upper()
        # Check critical columns have NOT NULL
        lines = content.split('\n')

        # Find lines with column definitions
        for line in lines:
            # timestamp column must be NOT NULL
            if 'TIMESTAMP' in line and 'TIMESTAMPTZ' in line and 'CREATED_AT' not in line and 'UPDATED_AT' not in line:
                if 'TIMESTAMP' in line.split()[0] or 'timestamp' in line.lower().split()[0]:
                    assert 'NOT NULL' in line, "timestamp column should be NOT NULL"
