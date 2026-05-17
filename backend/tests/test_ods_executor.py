"""
Unit tests for ODSExecutor.

Tests cover:
- Data model creation (ODSConfig, ODSResult, ODSError, WriteMode)
- Validation methods (_validate_config, _validate_records)
- Query building (_build_insert_query, _build_upsert_query)
- Record sorting (_sort_records_for_upsert)
- Operation execution (append, overwrite, upsert) with mocked connections
- Error handling and retry logic
"""

import pytest
import asyncio
import math
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch, call
from typing import Any

# Import the modules under test
from app.services.ods_executor import (
    ODSExecutor, ODSConfig, ODSResult, ODSError, WriteMode,
    ERROR_CODES, RETRYABLE_ERRORS, STATEMENT_TIMEOUTS, MAX_RETRIES,
    ods_executor
)


# Fixtures
@pytest.fixture
def executor():
    """Create a fresh ODSExecutor instance."""
    return ODSExecutor()


@pytest.fixture
def sample_config():
    """Create a sample ODSConfig for testing."""
    return ODSConfig(
        connection_id="test-conn",
        schema="public",
        table="test_table",
        write_mode=WriteMode.APPEND,
        identity_fields=[],
        batch_size=100
    )


@pytest.fixture
def mock_connection():
    """Create a mock asyncpg connection."""
    conn = AsyncMock()
    
    # Setup transaction context manager
    transaction_mock = MagicMock()
    transaction_mock.__aenter__ = AsyncMock()
    transaction_mock.__aexit__ = AsyncMock()
    conn.transaction = MagicMock(return_value=transaction_mock)
    
    # Setup async methods
    conn.fetchval = AsyncMock()
    conn.fetch = AsyncMock()
    conn.execute = AsyncMock()
    conn.executemany = AsyncMock()
    
    return conn


# Data Model Tests
class TestDataModels:
    """Tests for data model creation and validation."""
    
    def test_ods_config_creation(self):
        """Test ODSConfig dataclass can be created with valid parameters."""
        config = ODSConfig(
            connection_id="conn-1",
            schema="ods",
            table="sales",
            write_mode=WriteMode.UPSERT,
            identity_fields=["id", "date"],
            batch_size=500
        )
        assert config.connection_id == "conn-1"
        assert config.schema == "ods"
        assert config.table == "sales"
        assert config.write_mode == WriteMode.UPSERT
        assert config.identity_fields == ["id", "date"]
        assert config.batch_size == 500
    
    def test_ods_config_default_values(self):
        """Test ODSConfig uses correct defaults."""
        config = ODSConfig(
            connection_id="test",
            schema="public",
            table="test",
            write_mode=WriteMode.APPEND
        )
        assert config.batch_size == 1000
        assert config.identity_fields == []
        assert config.statement_timeout == "5min"  # Default for APPEND
    
    def test_ods_config_statement_timeouts(self):
        """Test statement timeout defaults per write mode."""
        append_config = ODSConfig(
            connection_id="test", schema="public", table="test",
            write_mode=WriteMode.APPEND
        )
        overwrite_config = ODSConfig(
            connection_id="test", schema="public", table="test",
            write_mode=WriteMode.OVERWRITE
        )
        upsert_config = ODSConfig(
            connection_id="test", schema="public", table="test",
            write_mode=WriteMode.UPSERT, identity_fields=["id"]
        )
        
        assert append_config.statement_timeout == "5min"
        assert overwrite_config.statement_timeout == "30min"
        assert upsert_config.statement_timeout == "10min"
    
    def test_ods_config_validation_missing_connection_id(self):
        """Test ODSConfig rejects empty connection_id."""
        with pytest.raises(ValueError, match="connection_id"):
            ODSConfig(
                connection_id="",
                schema="public",
                table="test",
                write_mode=WriteMode.APPEND
            )
    
    def test_ods_config_validation_missing_schema(self):
        """Test ODSConfig rejects empty schema."""
        with pytest.raises(ValueError, match="schema"):
            ODSConfig(
                connection_id="test",
                schema="",
                table="test",
                write_mode=WriteMode.APPEND
            )
    
    def test_ods_config_validation_missing_table(self):
        """Test ODSConfig rejects empty table."""
        with pytest.raises(ValueError, match="table"):
            ODSConfig(
                connection_id="test",
                schema="public",
                table="",
                write_mode=WriteMode.APPEND
            )
    
    def test_ods_config_validation_upsert_requires_identity_fields(self):
        """Test ODSConfig requires identity_fields for upsert mode."""
        with pytest.raises(ValueError, match="identity_fields"):
            ODSConfig(
                connection_id="test",
                schema="public",
                table="test",
                write_mode=WriteMode.UPSERT,
                identity_fields=[]
            )
    
    def test_write_mode_enum_values(self):
        """Test WriteMode enum has expected values."""
        assert WriteMode.APPEND.value == "append"
        assert WriteMode.OVERWRITE.value == "overwrite"
        assert WriteMode.UPSERT.value == "upsert"
    
    def test_ods_result_creation(self):
        """Test ODSResult dataclass creation."""
        result = ODSResult(
            success=True,
            complete_success=True,
            rows_affected=100,
            rows_inserted=100,
            rows_updated=0,
            batches_total=1,
            batches_successful=1,
            batches_failed=0,
            errors=[],
            duration_ms=500
        )
        assert result.success is True
        assert result.rows_affected == 100
        assert result.complete_success is True
    
    def test_ods_result_defaults(self):
        """Test ODSResult uses correct defaults."""
        result = ODSResult()
        assert result.success is False
        assert result.complete_success is False
        assert result.errors == []
        assert result.rows_affected == 0
    
    def test_ods_error_creation(self):
        """Test ODSError dataclass creation."""
        error = ODSError(
            batch_number=1,
            error_type="UniqueViolationError",
            message="Duplicate key",
            record_index=5,
            record_preview={"id": 123}
        )
        assert error.batch_number == 1
        assert error.error_type == "UniqueViolationError"
        assert error.record_preview == {"id": 123}
    
    def test_error_codes_mapping(self):
        """Test ERROR_CODES contains expected mappings."""
        assert ERROR_CODES['40P01'] == 'DEADLOCK'
        assert ERROR_CODES['23505'] == 'UNIQUE_VIOLATION'
        assert ERROR_CODES['23503'] == 'FK_VIOLATION'
        assert ERROR_CODES['57014'] == 'TIMEOUT'
    
    def test_retryable_errors_set(self):
        """Test RETRYABLE_ERRORS contains expected error types."""
        assert 'DEADLOCK' in RETRYABLE_ERRORS
        assert 'TIMEOUT' in RETRYABLE_ERRORS
        assert 'CONNECTION_ERROR' in RETRYABLE_ERRORS
        assert 'UNIQUE_VIOLATION' not in RETRYABLE_ERRORS


# Validation Tests
class TestValidation:
    """Tests for validation methods."""
    
    def test_validate_config_rejects_large_batch_size(self, executor):
        """Test batch size > 10000 is rejected."""
        with pytest.raises(ValueError, match="batch_size"):
            ODSConfig(
                connection_id="test",
                schema="public",
                table="test",
                write_mode=WriteMode.APPEND,
                identity_fields=[],
                batch_size=15000
            )
    
    def test_validate_config_rejects_small_batch_size(self, executor):
        """Test batch size < 1 is rejected."""
        with pytest.raises(ValueError, match="batch_size"):
            ODSConfig(
                connection_id="test",
                schema="public",
                table="test",
                write_mode=WriteMode.APPEND,
                identity_fields=[],
                batch_size=0
            )
    
    def test_validate_records_accepts_valid_data(self, executor):
        """Test valid records pass validation."""
        records = [
            {"id": 1, "name": "test", "value": 100.5},
            {"id": 2, "name": "test2", "value": None}
        ]
        validated = executor._validate_records(records)
        assert len(validated) == 2
        assert validated[0]["id"] == 1
        assert validated[0]["name"] == "test"
    
    def test_validate_records_rejects_nan(self, executor):
        """Test NaN values are rejected."""
        records = [{"id": 1, "value": float('nan')}]
        with pytest.raises(ValueError, match="NaN"):
            executor._validate_records(records)
    
    def test_validate_records_rejects_positive_infinity(self, executor):
        """Test positive Infinity values are rejected."""
        records = [{"id": 1, "value": float('inf')}]
        with pytest.raises(ValueError, match="Infinity"):
            executor._validate_records(records)
    
    def test_validate_records_rejects_negative_infinity(self, executor):
        """Test negative Infinity values are rejected."""
        records = [{"id": 1, "value": float('-inf')}]
        with pytest.raises(ValueError, match="Infinity"):
            executor._validate_records(records)
    
    def test_validate_records_converts_large_integers(self, executor):
        """Test large integers (> 2^53) are converted to strings."""
        records = [{"id": 2**53 + 1, "value": "test"}]
        validated = executor._validate_records(records)
        assert isinstance(validated[0]["id"], str)
        assert validated[0]["id"] == str(2**53 + 1)
    
    def test_validate_records_preserves_small_integers(self, executor):
        """Test small integers remain as integers."""
        records = [{"id": 1000, "value": "test"}]
        validated = executor._validate_records(records)
        assert isinstance(validated[0]["id"], int)
        assert validated[0]["id"] == 1000
    
    def test_validate_records_converts_datetime(self, executor):
        """Test datetime objects are converted to ISO format."""
        now = datetime(2024, 1, 15, 10, 30, 0)
        records = [{"id": 1, "created_at": now}]
        validated = executor._validate_records(records)
        assert validated[0]["created_at"] == "2024-01-15T10:30:00"
    
    def test_validate_records_converts_date(self, executor):
        """Test date objects are converted to ISO format."""
        today = datetime(2024, 1, 15).date()
        records = [{"id": 1, "date": today}]
        validated = executor._validate_records(records)
        assert validated[0]["date"] == "2024-01-15"


# Query Building Tests
class TestQueryBuilding:
    """Tests for SQL query building methods."""
    
    def test_build_insert_query(self, executor, sample_config):
        """Test INSERT query generation."""
        records = [{"id": 1, "name": "test", "value": 100}]
        sql, columns = executor._build_insert_query(sample_config, records[0].keys())
        
        assert "INSERT INTO" in sql
        assert '"public"' in sql
        assert '"test_table"' in sql
        assert '"id"' in sql
        assert '"name"' in sql
        assert '"value"' in sql
        assert "$1" in sql
        assert columns == ["id", "name", "value"]
    
    def test_build_insert_query_empty_columns(self, executor, sample_config):
        """Test INSERT query with empty columns raises error."""
        with pytest.raises(ValueError):
            executor._build_insert_query(sample_config, [])
    
    def test_build_upsert_query(self, executor):
        """Test UPSERT query generation."""
        config = ODSConfig(
            connection_id="test",
            schema="public",
            table="test_table",
            write_mode=WriteMode.UPSERT,
            identity_fields=["id"]
        )
        records = [{"id": 1, "name": "test", "value": 100}]
        sql, columns = executor._build_upsert_query(config, list(records[0].keys()))
        
        assert "INSERT INTO" in sql
        assert "ON CONFLICT" in sql
        assert '("id")' in sql  # Conflict target
        assert "DO UPDATE SET" in sql
        assert "EXCLUDED." in sql
        assert "name" in sql
        assert "value" in sql
    
    def test_build_upsert_query_composite_keys(self, executor):
        """Test UPSERT with composite identity fields."""
        config = ODSConfig(
            connection_id="test",
            schema="public",
            table="test_table",
            write_mode=WriteMode.UPSERT,
            identity_fields=["id", "date"]
        )
        records = [{"id": 1, "date": "2024-01-01", "value": 100}]
        sql, columns = executor._build_upsert_query(config, list(records[0].keys()))
        
        assert 'ON CONFLICT ("id", "date")' in sql
    
    def test_build_upsert_query_all_identity_fields(self, executor):
        """Test UPSERT when all fields are identity fields."""
        config = ODSConfig(
            connection_id="test",
            schema="public",
            table="test_table",
            write_mode=WriteMode.UPSERT,
            identity_fields=["id"]
        )
        records = [{"id": 1}]
        sql, columns = executor._build_upsert_query(config, list(records[0].keys()))
        
        assert "ON CONFLICT" in sql
        assert "DO NOTHING" in sql
    
    def test_sort_records_for_upsert(self, executor):
        """Test records are sorted by identity fields."""
        records = [
            {"id": 3, "name": "c"},
            {"id": 1, "name": "a"},
            {"id": 2, "name": "b"}
        ]
        sorted_records = executor._sort_records_for_upsert(records, ["id"])
        
        assert sorted_records[0]["id"] == 1
        assert sorted_records[1]["id"] == 2
        assert sorted_records[2]["id"] == 3
    
    def test_sort_records_for_upsert_empty(self, executor):
        """Test sorting empty records returns empty list."""
        records = []
        sorted_records = executor._sort_records_for_upsert(records, ["id"])
        assert sorted_records == []
    
    def test_sort_records_for_upsert_single(self, executor):
        """Test sorting single record returns same record."""
        records = [{"id": 1, "name": "test"}]
        sorted_records = executor._sort_records_for_upsert(records, ["id"])
        assert sorted_records == records
    
    def test_sort_records_for_upsert_composite(self, executor):
        """Test sorting with composite identity fields."""
        records = [
            {"id": 2, "date": "2024-01-02"},
            {"id": 1, "date": "2024-01-03"},
            {"id": 1, "date": "2024-01-01"}
        ]
        sorted_records = executor._sort_records_for_upsert(records, ["id", "date"])
        
        assert sorted_records[0] == {"id": 1, "date": "2024-01-01"}
        assert sorted_records[1] == {"id": 1, "date": "2024-01-03"}
        assert sorted_records[2] == {"id": 2, "date": "2024-01-02"}


# Async Operation Tests
@pytest.mark.asyncio
class TestOperations:
    """Tests for async operation execution."""
    
    async def test_execute_append(self, executor, sample_config, mock_connection):
        """Test append operation with mocked connection."""
        sample_config.write_mode = WriteMode.APPEND
        records = [{"id": 1, "name": "test"}]
        
        # Mock table exists check
        mock_connection.fetchval.return_value = True
        
        # Mock executemany to return success
        mock_connection.executemany.return_value = "INSERT 0 1"
        
        result = await executor.execute(sample_config, records, mock_connection)
        
        assert result.success is True
        assert result.complete_success is True
        assert result.rows_inserted == 1
        assert mock_connection.executemany.called
    
    async def test_execute_overwrite_calls_truncate(self, executor, sample_config, mock_connection):
        """Test overwrite operation calls TRUNCATE on first batch."""
        sample_config.write_mode = WriteMode.OVERWRITE
        records = [{"id": 1, "name": "test"}]
        
        mock_connection.fetchval.return_value = True
        mock_connection.executemany.return_value = "INSERT 0 1"
        
        result = await executor.execute(sample_config, records, mock_connection)
        
        # Check that TRUNCATE was called on first batch
        execute_calls = [str(call) for call in mock_connection.execute.call_args_list]
        truncate_calls = [c for c in execute_calls if 'TRUNCATE' in c]
        assert len(truncate_calls) > 0
    
    async def test_execute_upsert_validates_constraint(self, executor, mock_connection):
        """Test upsert operation validates unique constraint."""
        config = ODSConfig(
            connection_id="test",
            schema="public",
            table="test_table",
            write_mode=WriteMode.UPSERT,
            identity_fields=["id"],
            batch_size=100
        )
        records = [{"id": 1, "name": "updated"}]
        
        # Mock table exists check
        mock_connection.fetchval.side_effect = [
            True,  # schema exists
            True,  # table exists
        ]
        
        # Mock unique constraint check
        mock_connection.fetch.return_value = [
            {"constraint_name": "test_pkey", "columns": ["id"]}
        ]
        
        mock_connection.executemany.return_value = "INSERT 0 1"
        
        result = await executor.execute(config, records, mock_connection)
        
        assert result.success is True
        assert mock_connection.executemany.called
    
    async def test_execute_empty_records_raises_error(self, executor, sample_config, mock_connection):
        """Test execute raises error for empty records."""
        with pytest.raises(ValueError, match="records cannot be empty"):
            await executor.execute(sample_config, [], mock_connection)
    
    async def test_execute_validates_table_exists(self, executor, sample_config, mock_connection):
        """Test execute validates table existence."""
        records = [{"id": 1, "name": "test"}]
        
        # Mock schema exists but table doesn't
        mock_connection.fetchval.side_effect = [True, False]
        
        with pytest.raises(ValueError, match="does not exist"):
            await executor.execute(sample_config, records, mock_connection)
    
    async def test_batch_processing(self, executor, sample_config, mock_connection):
        """Test records are processed in batches."""
        sample_config.batch_size = 2
        records = [
            {"id": 1, "name": "a"},
            {"id": 2, "name": "b"},
            {"id": 3, "name": "c"}
        ]
        
        mock_connection.fetchval.return_value = True
        mock_connection.executemany.return_value = "INSERT 0 2"
        
        result = await executor.execute(sample_config, records, mock_connection)
        
        assert result.batches_total == 2  # 3 records / 2 batch_size = 2 batches
        assert mock_connection.executemany.call_count == 2
    
    async def test_statement_timeout_set(self, executor, sample_config, mock_connection):
        """Test statement timeout is set per operation."""
        records = [{"id": 1, "name": "test"}]
        
        mock_connection.fetchval.return_value = True
        mock_connection.executemany.return_value = "INSERT 0 1"
        
        await executor.execute(sample_config, records, mock_connection)
        
        # Check that SET LOCAL statement_timeout was called
        execute_calls = [str(call) for call in mock_connection.execute.call_args_list]
        timeout_calls = [c for c in execute_calls if 'statement_timeout' in c]
        assert len(timeout_calls) > 0


# Error Handling Tests
@pytest.mark.asyncio
class TestErrorHandling:
    """Tests for error classification and retry logic."""
    
    async def test_error_classification_connection_error(self, executor):
        """Test connection errors are classified correctly."""
        try:
            import asyncpg
            error = asyncpg.ConnectionDoesNotExistError("Connection lost")
            classified = executor._classify_error(error, 1)
            assert classified.error_type == "CONNECTION_ERROR"
        except ImportError:
            pytest.skip("asyncpg not installed")
    
    async def test_error_classification_unique_violation(self, executor):
        """Test unique violation errors are classified correctly."""
        try:
            import asyncpg
            error = asyncpg.UniqueViolationError("Duplicate key")
            classified = executor._classify_error(error, 1)
            assert classified.error_type == "UNIQUE_VIOLATION"
        except ImportError:
            pytest.skip("asyncpg not installed")
    
    async def test_error_classification_deadlock(self, executor):
        """Test deadlock errors are classified correctly."""
        try:
            import asyncpg
            error = asyncpg.DeadlockDetectedError("deadlock detected")
            classified = executor._classify_error(error, 1)
            assert classified.error_type == "DEADLOCK"
        except ImportError:
            pytest.skip("asyncpg not installed")
    
    async def test_error_classification_timeout(self, executor):
        """Test timeout errors are classified correctly."""
        try:
            import asyncpg
            error = asyncpg.QueryCanceledError("query canceled")
            classified = executor._classify_error(error, 1)
            assert classified.error_type == "TIMEOUT"
        except ImportError:
            pytest.skip("asyncpg not installed")
    
    async def test_error_classification_unknown(self, executor):
        """Test unknown errors are classified as UNKNOWN."""
        error = Exception("Some random error")
        classified = executor._classify_error(error, 1)
        assert classified.error_type == "UNKNOWN"
        assert classified.message == "Some random error"
    
    async def test_retry_on_deadlock(self, executor, sample_config, mock_connection):
        """Test retry logic is triggered on deadlock."""
        try:
            import asyncpg
            sample_config.write_mode = WriteMode.UPSERT
            sample_config.identity_fields = ["id"]
            records = [{"id": 1, "name": "test"}]
            
            # Mock validation calls
            mock_connection.fetchval.side_effect = [True, True]
            mock_connection.fetch.return_value = [
                {"constraint_name": "test_pkey", "columns": ["id"]}
            ]
            
            # First two calls raise deadlock, third succeeds
            call_count = [0]
            async def side_effect(*args, **kwargs):
                call_count[0] += 1
                if call_count[0] <= 2:
                    raise asyncpg.DeadlockDetectedError("deadlock detected")
                return "INSERT 0 1"
            
            mock_connection.executemany = AsyncMock(side_effect=side_effect)
            
            # Patch _execute_batch to track calls and simulate retries
            original_execute_batch = executor._execute_batch
            batch_call_count = [0]
            
            async def patched_execute_batch(config, batch, connection, batch_number):
                batch_call_count[0] += 1
                if batch_call_count[0] <= 2:
                    raise asyncpg.DeadlockDetectedError("deadlock detected")
                return {'success': True, 'rows_inserted': 1}
            
            executor._execute_batch = patched_execute_batch
            
            with patch('asyncio.sleep', new_callable=AsyncMock):
                result = await executor.execute(sample_config, records, mock_connection)
            
            # Should have retried (multiple calls expected)
            assert batch_call_count[0] == 3
            
            # Restore original method
            executor._execute_batch = original_execute_batch
        except ImportError:
            pytest.skip("asyncpg not installed")
    
    async def test_no_retry_on_unique_violation(self, executor, sample_config, mock_connection):
        """Test no retry on unique violation (non-retryable error)."""
        try:
            import asyncpg
            records = [{"id": 1, "name": "test"}]
            
            mock_connection.fetchval.return_value = True
            
            # Patch _execute_batch to raise unique violation (non-retryable)
            original_execute_batch = executor._execute_batch
            batch_call_count = [0]
            
            async def patched_execute_batch(config, batch, connection, batch_number):
                batch_call_count[0] += 1
                raise asyncpg.UniqueViolationError("Duplicate key")
            
            executor._execute_batch = patched_execute_batch
            
            result = await executor.execute(sample_config, records, mock_connection)
            
            # Should fail immediately without retry (only 1 call)
            assert batch_call_count[0] == 1
            assert result.success is False
            assert len(result.errors) > 0
            assert result.errors[0].error_type == "UNIQUE_VIOLATION"
            
            # Restore original method
            executor._execute_batch = original_execute_batch
        except ImportError:
            pytest.skip("asyncpg not installed")


# Split Batches Tests
class TestBatchSplitting:
    """Tests for record batching."""
    
    def test_split_into_batches_basic(self, executor):
        """Test basic batch splitting."""
        records = [{"id": i} for i in range(5)]
        batches = executor._split_into_batches(records, 2)
        
        assert len(batches) == 3
        assert len(batches[0]) == 2
        assert len(batches[1]) == 2
        assert len(batches[2]) == 1
    
    def test_split_into_batches_exact_multiple(self, executor):
        """Test batch splitting with exact multiple."""
        records = [{"id": i} for i in range(6)]
        batches = executor._split_into_batches(records, 3)
        
        assert len(batches) == 2
        assert len(batches[0]) == 3
        assert len(batches[1]) == 3
    
    def test_split_into_batches_single_batch(self, executor):
        """Test batch splitting when all fit in one batch."""
        records = [{"id": i} for i in range(3)]
        batches = executor._split_into_batches(records, 10)
        
        assert len(batches) == 1
        assert len(batches[0]) == 3
    
    def test_split_into_batches_empty(self, executor):
        """Test batch splitting with empty records."""
        batches = executor._split_into_batches([], 10)
        assert batches == []
    
    def test_split_into_batches_invalid_size(self, executor):
        """Test batch splitting with invalid batch size."""
        records = [{"id": 1}]
        with pytest.raises(ValueError, match="batch_size"):
            executor._split_into_batches(records, 0)


# Quote Identifier Tests
class TestQuoteIdentifier:
    """Tests for SQL identifier quoting."""
    
    def test_quote_valid_identifier(self, executor):
        """Test quoting valid identifiers."""
        assert executor._quote_identifier("test") == '"test"'
        assert executor._quote_identifier("test_table") == '"test_table"'
        assert executor._quote_identifier("_test") == '"_test"'
    
    def test_quote_rejects_invalid_identifier(self, executor):
        """Test rejecting invalid identifiers."""
        with pytest.raises(ValueError):
            executor._quote_identifier("test-table")  # Hyphen not allowed
        
        with pytest.raises(ValueError):
            executor._quote_identifier("123test")  # Can't start with digit
        
        with pytest.raises(ValueError):
            executor._quote_identifier("test;drop")  # Semicolon not allowed
        
        with pytest.raises(ValueError):
            executor._quote_identifier("test space")  # Space not allowed


# Singleton Tests
class TestSingleton:
    """Tests for the singleton instance."""
    
    def test_singleton_exists(self):
        """Test that ods_executor singleton exists."""
        assert ods_executor is not None
        assert isinstance(ods_executor, ODSExecutor)
    
    def test_singleton_is_same_instance(self):
        """Test that ods_executor is a singleton."""
        from app.services.ods_executor import ODSExecutor
        executor2 = ODSExecutor()
        # They should be different instances (class is not a singleton pattern)
        # but the module-level ods_executor is a shared instance
        assert ods_executor is not executor2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
