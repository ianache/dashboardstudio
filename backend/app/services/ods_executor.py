"""
ODS Executor Service - Core execution engine for PostgreSQL ODS operations.

This module provides the ODSExecutor class for handling Append, Overwrite, and Upsert
operations on PostgreSQL tables with proper batch processing, transaction isolation,
and comprehensive error handling.

Usage:
    from backend.app.services.ods_executor import ODSExecutor, ODSConfig, WriteMode
    
    config = ODSConfig(
        connection_id="conn-123",
        schema="ods",
        table="fact_sales",
        write_mode=WriteMode.UPSERT,
        identity_fields=["id"],
        batch_size=1000
    )
    
    executor = ODSExecutor()
    result = await executor.execute(config, records, connection)

Note:
    This executor is designed to be called from the Deno runner via a signal-based
    integration pattern. The connection is managed by the caller.
"""

import asyncio
import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import asyncpg

logger = logging.getLogger(__name__)


class WriteMode(Enum):
    """Supported write modes for ODS operations.
    
    - APPEND: Insert records without affecting existing data
    - OVERWRITE: Truncate table and insert all records (RESTART IDENTITY)
    - UPSERT: Insert records, update on conflict using identity fields
    
    Note: MERGE_SCD2 is deferred to v2 per REQUIREMENTS.md
    """
    APPEND = "append"
    OVERWRITE = "overwrite"
    UPSERT = "upsert"


# Error classification constants mapping PostgreSQL SQLSTATE codes
ERROR_CODES = {
    # Deadlock detected
    '40P01': 'DEADLOCK',
    # Unique violation
    '23505': 'UNIQUE_VIOLATION',
    # Foreign key violation
    '23503': 'FK_VIOLATION',
    # Query canceled (timeout)
    '57014': 'TIMEOUT',
    # Connection errors
    '08006': 'CONNECTION_ERROR',  # connection_failure
    '08003': 'CONNECTION_ERROR',  # connection_does_not_exist
    '08001': 'CONNECTION_ERROR',  # sqlclient_unable_to_establish_sqlconnection
}

# Error types that should trigger retry with exponential backoff
RETRYABLE_ERRORS = {'DEADLOCK', 'TIMEOUT', 'CONNECTION_ERROR'}

# Statement timeouts per operation type (in PostgreSQL interval format)
STATEMENT_TIMEOUTS = {
    WriteMode.APPEND: '5min',
    WriteMode.OVERWRITE: '30min',
    WriteMode.UPSERT: '10min',
}

# Retry configuration
MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = [1, 2, 4]  # Exponential: 1s, 2s, 4s


@dataclass
class ODSConfig:
    """Configuration for an ODS execution operation.
    
    Attributes:
        connection_id: Unique identifier for the data source connection
        schema: PostgreSQL schema name (e.g., 'ods', 'public')
        table: Target table name
        write_mode: One of WriteMode.APPEND, OVERWRITE, or UPSERT
        identity_fields: Column(s) used for conflict detection in upsert mode
        batch_size: Number of records per batch (1-10000, default 1000)
        statement_timeout: PostgreSQL statement timeout (default based on write_mode)
    
    Raises:
        ValueError: If configuration is invalid
    """
    connection_id: str
    schema: str
    table: str
    write_mode: WriteMode
    identity_fields: List[str] = field(default_factory=list)
    batch_size: int = 1000
    statement_timeout: Optional[str] = None
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if not self.connection_id:
            raise ValueError("connection_id is required")
        if not self.schema:
            raise ValueError("schema is required")
        if not self.table:
            raise ValueError("table is required")
        if not isinstance(self.write_mode, WriteMode):
            raise ValueError(f"write_mode must be a WriteMode enum, got {type(self.write_mode)}")
        if self.batch_size < 1 or self.batch_size > 10000:
            raise ValueError(f"batch_size must be between 1 and 10000, got {self.batch_size}")
        
        # Validate identity_fields for upsert
        if self.write_mode == WriteMode.UPSERT and not self.identity_fields:
            raise ValueError("identity_fields is required for UPSERT mode")
        
        # Set default timeout based on write_mode if not specified
        if self.statement_timeout is None:
            self.statement_timeout = STATEMENT_TIMEOUTS.get(self.write_mode, '5min')


@dataclass
class ODSError:
    """Detailed error information for a failed batch or record.
    
    Attributes:
        batch_number: The batch number where the error occurred (1-indexed)
        error_type: Classified error type (e.g., 'UNIQUE_VIOLATION', 'TIMEOUT')
        message: Human-readable error message
        record_index: Optional index of the specific record within the batch (0-indexed)
        record_preview: Optional preview of the problematic record (truncated for safety)
        sqlstate: Optional PostgreSQL SQLSTATE code
    """
    batch_number: int
    error_type: str
    message: str
    record_index: Optional[int] = None
    record_preview: Optional[Dict[str, Any]] = None
    sqlstate: Optional[str] = None


@dataclass
class ODSResult:
    """Result of an ODS execution operation.
    
    Attributes:
        success: True if at least one batch succeeded
        complete_success: True if all batches succeeded
        rows_affected: Total rows affected (inserted + updated)
        rows_inserted: Total rows inserted
        rows_updated: Total rows updated (upsert only)
        batches_total: Total number of batches processed
        batches_successful: Number of successful batches
        batches_failed: Number of failed batches
        errors: List of detailed error information
        duration_ms: Total execution duration in milliseconds
    
    Note:
        success=True means partial success is possible. Check complete_success
        to determine if all batches succeeded.
    """
    success: bool = False
    complete_success: bool = False
    rows_affected: int = 0
    rows_inserted: int = 0
    rows_updated: int = 0
    batches_total: int = 0
    batches_successful: int = 0
    batches_failed: int = 0
    errors: List[ODSError] = field(default_factory=list)
    duration_ms: int = 0


class ODSExecutor:
    """Core executor for PostgreSQL ODS operations.
    
    This class provides methods to execute Append, Overwrite, and Upsert operations
    on PostgreSQL tables with proper batch processing, transaction isolation per batch,
    automatic retry logic, and comprehensive error classification.
    
    Key Features:
        - Per-batch transaction isolation (batches are independent)
        - Configurable batch sizes with memory-efficient processing
        - Exponential backoff retry for deadlock, timeout, and connection errors
        - SQL injection prevention via parameterized queries
        - Record sorting before upsert to prevent deadlocks
        - Detailed error classification using PostgreSQL SQLSTATE codes
    
    Thread Safety:
        This class is stateless and safe to use from multiple concurrent contexts.
        However, the asyncpg.Connection passed to execute() should not be shared
        across concurrent operations.
    
    Example:
        executor = ODSExecutor()
        
        # Using an existing connection
        async with asyncpg.connect(dsn=connection_string) as conn:
            config = ODSConfig(
                connection_id="conn-123",
                schema="ods",
                table="fact_sales",
                write_mode=WriteMode.UPSERT,
                identity_fields=["id", "date"],
                batch_size=1000
            )
            result = await executor.execute(config, records, conn)
            print(f"Inserted: {result.rows_inserted}, Updated: {result.rows_updated}")
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def _validate_config(self, config: ODSConfig) -> None:
        """Validate ODSConfig (internal hook for validation)."""
        # Config validates itself in __post_init__, but we keep this for
        # explicit validation calls and future extension points
        if not isinstance(config, ODSConfig):
            raise ValueError(f"config must be an ODSConfig instance, got {type(config)}")
    
    def _validate_records(
        self, 
        records: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Validate records for JSON serialization safety.
        
        Checks:
        - No NaN or Infinity values
        - BigInt values converted to strings
        - Dates are ISO 8601 strings
        
        Args:
            records: List of record dictionaries
            
        Returns:
            Validated/cleaned records
            
        Raises:
            ValueError: If records contain invalid values
        """
        import math
        import datetime
        
        validated = []
        for idx, record in enumerate(records):
            clean_record = {}
            for key, value in record.items():
                # Check for NaN/Infinity
                if isinstance(value, float):
                    if math.isnan(value) or math.isinf(value):
                        raise ValueError(
                            f"Record {idx} field '{key}' contains invalid float value (NaN or Infinity)"
                        )
                    clean_record[key] = value
                # Convert BigInt to string
                elif isinstance(value, int) and abs(value) > 2**53:
                    clean_record[key] = str(value)
                # Ensure dates are strings
                elif isinstance(value, (datetime.datetime, datetime.date)):
                    clean_record[key] = value.isoformat()
                else:
                    clean_record[key] = value
            validated.append(clean_record)
        
        return validated
    
    async def _validate_table_exists(
        self, 
        conn: asyncpg.Connection, 
        schema: str, 
        table: str
    ) -> bool:
        """
        Validate that the target schema and table exist.
        
        Args:
            conn: Database connection
            schema: Schema name
            table: Table name
            
        Returns:
            True if table exists
            
        Raises:
            ValueError: If schema or table does not exist
        """
        # Validate schema exists
        schema_query = """
            SELECT EXISTS(
                SELECT 1 FROM information_schema.schemata 
                WHERE schema_name = $1
            )
        """
        schema_exists = await conn.fetchval(schema_query, schema)
        if not schema_exists:
            raise ValueError(f"Schema '{schema}' does not exist")
        
        # Validate table exists
        table_query = """
            SELECT EXISTS(
                SELECT 1 FROM information_schema.tables 
                WHERE table_schema = $1 AND table_name = $2
            )
        """
        table_exists = await conn.fetchval(table_query, schema, table)
        if not table_exists:
            raise ValueError(f"Table '{schema}.{table}' does not exist")
        
        return True
    
    async def _validate_unique_constraint(
        self, 
        conn: asyncpg.Connection, 
        schema: str, 
        table: str,
        identity_fields: List[str]
    ) -> bool:
        """
        Validate that identity fields have a unique constraint.
        Required for upsert operations to prevent ON CONFLICT failures.
        
        Args:
            conn: Database connection
            schema: Schema name
            table: Table name
            identity_fields: List of identity field names
            
        Returns:
            True if a unique constraint exists on identity_fields
            
        Raises:
            ValueError: If no matching unique constraint found
        """
        if not identity_fields:
            raise ValueError("Identity fields required for upsert validation")
        
        # Query for unique constraints that match the identity fields
        query = """
            SELECT tc.constraint_name, array_agg(kcu.column_name ORDER BY kcu.ordinal_position) as columns
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu 
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            WHERE tc.table_schema = $1
                AND tc.table_name = $2
                AND tc.constraint_type = 'UNIQUE'
            GROUP BY tc.constraint_name
        """
        
        rows = await conn.fetch(query, schema, table)
        
        identity_set = set(identity_fields)
        for row in rows:
            constraint_columns = set(row['columns'])
            # Check if identity fields are a subset of constraint columns
            if identity_set.issubset(constraint_columns):
                return True
        
        # Also check for primary key
        pk_query = """
            SELECT array_agg(kcu.column_name ORDER BY kcu.ordinal_position) as columns
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu 
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            WHERE tc.table_schema = $1
                AND tc.table_name = $2
                AND tc.constraint_type = 'PRIMARY KEY'
            GROUP BY tc.constraint_name
        """
        
        pk_rows = await conn.fetch(pk_query, schema, table)
        for row in pk_rows:
            pk_columns = set(row['columns'])
            if identity_set.issubset(pk_columns):
                return True
        
        raise ValueError(
            f"No unique constraint found on '{schema}.{table}' matching identity fields: {identity_fields}. "
            f"Upsert requires a unique index or primary key on the identity fields."
        )
    
    async def execute(
        self,
        config: ODSConfig,
        records: List[Dict[str, Any]],
        connection: asyncpg.Connection
    ) -> ODSResult:
        """Execute the configured ODS operation on the provided records.
        
        This method processes records in batches according to config.batch_size.
        Each batch is executed within its own transaction, providing isolation
        between batches. Failed batches are logged and recorded but do not
        prevent processing of subsequent batches.
        
        For UPSERT operations, records are automatically sorted by identity_fields
        before processing to prevent deadlocks in concurrent scenarios.
        
        Args:
            config: ODSConfig with operation settings
            records: List of record dictionaries to write
            connection: asyncpg Connection to use (managed by caller)
        
        Returns:
            ODSResult with detailed statistics about the operation
        
        Raises:
            ValueError: If records is empty or config is invalid
        
        Example:
            result = await executor.execute(config, records, conn)
            if result.complete_success:
                print(f"All {result.rows_affected} rows processed successfully")
            elif result.success:
                print(f"Partial success: {result.batches_successful}/{result.batches_total} batches")
            else:
                print(f"All batches failed. Errors: {len(result.errors)}")
        """
        import time
        start_time = time.time()
        
        # Validate config
        self._validate_config(config)
        
        # Validate records
        validated_records = self._validate_records(records)
        records = validated_records
        
        if not records:
            raise ValueError("records cannot be empty")
        
        # Validate table exists
        await self._validate_table_exists(connection, config.schema, config.table)
        
        # Validate unique constraint for upsert
        if config.write_mode == WriteMode.UPSERT:
            await self._validate_unique_constraint(
                connection, config.schema, config.table, config.identity_fields
            )
            # Sort records by identity fields for upsert (deadlock prevention)
            records = self._sort_records_for_upsert(records, config.identity_fields)
        
        # Split records into batches
        batches = self._split_into_batches(records, config.batch_size)
        total_batches = len(batches)
        
        self.logger.info(
            f"Starting {config.write_mode.value} operation on "
            f"{config.schema}.{config.table}: {len(records)} records in {total_batches} batches"
        )
        
        # Initialize result tracking
        result = ODSResult(batches_total=total_batches)
        
        # Process each batch
        for batch_num, batch in enumerate(batches, start=1):
            batch_result = await self._execute_batch_with_retry(
                config, batch, connection, batch_num
            )
            
            # Aggregate results
            if batch_result.get('success', False):
                result.batches_successful += 1
                result.rows_inserted += batch_result.get('rows_inserted', 0)
                result.rows_updated += batch_result.get('rows_updated', 0)
            else:
                result.batches_failed += 1
                if 'error' in batch_result:
                    result.errors.append(batch_result['error'])
            
            self.logger.debug(
                f"Batch {batch_num}/{total_batches} completed: "
                f"success={batch_result.get('success', False)}"
            )
        
        # Calculate final statistics
        result.rows_affected = result.rows_inserted + result.rows_updated
        result.success = result.batches_successful > 0
        result.complete_success = result.batches_failed == 0
        result.duration_ms = int((time.time() - start_time) * 1000)
        
        self.logger.info(
            f"Operation completed: success={result.success}, "
            f"complete_success={result.complete_success}, "
            f"rows_affected={result.rows_affected}, "
            f"batches={result.batches_successful}/{result.batches_total}, "
            f"duration={result.duration_ms}ms"
        )
        
        return result
    
    async def _execute_batch_with_retry(
        self,
        config: ODSConfig,
        batch: List[Dict[str, Any]],
        connection: asyncpg.Connection,
        batch_number: int
    ) -> Dict[str, Any]:
        """Execute a single batch with retry logic.
        
        Args:
            config: ODSConfig
            batch: List of records for this batch
            connection: asyncpg Connection
            batch_number: 1-indexed batch number for logging
        
        Returns:
            Dict with 'success' boolean and either row counts or error details
        """
        last_error = None
        
        for attempt in range(MAX_RETRIES):
            try:
                result = await self._execute_batch(config, batch, connection, batch_number)
                if attempt > 0:
                    self.logger.info(f"Batch {batch_number} succeeded on attempt {attempt + 1}")
                return result
            except Exception as e:
                last_error = e
                error_info = self._classify_error(e, batch_number)
                
                # Check if error is retryable
                if error_info.error_type in RETRYABLE_ERRORS and attempt < MAX_RETRIES - 1:
                    wait_time = RETRY_BACKOFF_SECONDS[attempt]
                    self.logger.warning(
                        f"Batch {batch_number} failed with {error_info.error_type} "
                        f"(attempt {attempt + 1}/{MAX_RETRIES}), retrying in {wait_time}s: "
                        f"{error_info.message}"
                    )
                    await asyncio.sleep(wait_time)
                else:
                    # Not retryable or exhausted retries
                    break
        
        # All retries exhausted or non-retryable error
        if last_error is None:
            # Should not happen, but handle gracefully
            last_error = Exception("Unknown error occurred")
        error_info = self._classify_error(last_error, batch_number)
        self.logger.error(
            f"Batch {batch_number} failed permanently: {error_info.error_type}: "
            f"{error_info.message}"
        )
        return {'success': False, 'error': error_info}
    
    async def _execute_batch(
        self,
        config: ODSConfig,
        batch: List[Dict[str, Any]],
        connection: asyncpg.Connection,
        batch_number: int
    ) -> Dict[str, Any]:
        """Execute a single batch within a transaction.
        
        Each batch runs in its own transaction, providing isolation.
        Failed batches roll back without affecting other batches.
        
        Args:
            config: ODSConfig
            batch: List of records for this batch
            connection: asyncpg Connection
            batch_number: 1-indexed batch number
        
        Returns:
            Dict with operation results
        """
        # Set statement timeout for this operation
        timeout_value = config.statement_timeout or STATEMENT_TIMEOUTS.get(config.write_mode, '5min')
        
        async with connection.transaction():
            # Set timeout for this transaction
            await connection.execute(f"SET LOCAL statement_timeout = '{timeout_value}'")
            
            # Route to appropriate operation handler
            if config.write_mode == WriteMode.APPEND:
                return await self._execute_append(config, batch, connection, batch_number)
            elif config.write_mode == WriteMode.OVERWRITE:
                return await self._execute_overwrite(config, batch, connection, batch_number)
            elif config.write_mode == WriteMode.UPSERT:
                return await self._execute_upsert(config, batch, connection, batch_number)
            else:
                raise ValueError(f"Unsupported write_mode: {config.write_mode}")
    
    async def _execute_append(
        self,
        config: ODSConfig,
        batch: List[Dict[str, Any]],
        connection: asyncpg.Connection,
        batch_number: int
    ) -> Dict[str, Any]:
        """Execute append (INSERT) operation for a batch.
        
        Args:
            config: ODSConfig
            batch: List of records to insert
            connection: asyncpg Connection
            batch_number: 1-indexed batch number
        
        Returns:
            Dict with 'success', 'rows_inserted'
        """
        if not batch:
            return {'success': True, 'rows_inserted': 0}
        
        query, column_names = self._build_insert_query(config, batch[0].keys())
        
        # Prepare values as list of tuples
        values = [
            tuple(record.get(col) for col in column_names)
            for record in batch
        ]
        
        # Execute batch insert
        result = await connection.executemany(query, values)
        
        # executemany returns number of rows affected
        rows_inserted = len(batch) if result else 0
        
        self.logger.debug(f"Batch {batch_number}: Appended {rows_inserted} rows")
        return {'success': True, 'rows_inserted': rows_inserted}
    
    async def _execute_overwrite(
        self,
        config: ODSConfig,
        batch: List[Dict[str, Any]],
        connection: asyncpg.Connection,
        batch_number: int
    ) -> Dict[str, Any]:
        """Execute overwrite (TRUNCATE + INSERT) operation for a batch.
        
        Only the first batch performs TRUNCATE. Subsequent batches just append.
        
        Args:
            config: ODSConfig
            batch: List of records to insert
            connection: asyncpg Connection
            batch_number: 1-indexed batch number
        
        Returns:
            Dict with 'success', 'rows_inserted'
        """
        # Only truncate on the first batch
        if batch_number == 1:
            quoted_schema = self._quote_identifier(config.schema)
            quoted_table = self._quote_identifier(config.table)
            truncate_sql = f'TRUNCATE TABLE {quoted_schema}.{quoted_table} RESTART IDENTITY'
            await connection.execute(truncate_sql)
            self.logger.info(f"Table {config.schema}.{config.table} truncated for overwrite")
        
        # Then append the records
        return await self._execute_append(config, batch, connection, batch_number)
    
    async def _execute_upsert(
        self,
        config: ODSConfig,
        batch: List[Dict[str, Any]],
        connection: asyncpg.Connection,
        batch_number: int
    ) -> Dict[str, Any]:
        """Execute upsert (INSERT ON CONFLICT DO UPDATE) for a batch.
        
        Args:
            config: ODSConfig
            batch: List of records to upsert
            connection: asyncpg Connection
            batch_number: 1-indexed batch number
        
        Returns:
            Dict with 'success', 'rows_inserted', 'rows_updated'
        """
        if not batch:
            return {'success': True, 'rows_inserted': 0, 'rows_updated': 0}
        
        query, column_names = self._build_upsert_query(config, list(batch[0].keys()))
        
        # Prepare values
        values = [
            tuple(record.get(col) for col in column_names)
            for record in batch
        ]
        
        # Execute upsert using executemany
        # Note: executemany doesn't return detailed counts for upsert
        # We estimate based on the batch size, but actual counts may differ
        await connection.executemany(query, values)
        
        # Since executemany doesn't give us precise insert vs update counts for upsert,
        # we return the batch size as potentially affected
        # For accurate counts, we'd need to use INSERT...RETURNING but that has
        # performance implications for large batches
        estimated_affected = len(batch)
        
        self.logger.debug(f"Batch {batch_number}: Upserted {estimated_affected} rows")
        return {
            'success': True,
            'rows_inserted': estimated_affected,  # Best estimate
            'rows_updated': 0  # Cannot determine from executemany
        }
    
    def _build_insert_query(self, config: ODSConfig, columns: Any) -> Tuple[str, List[str]]:
        """Build INSERT query with proper quoting.
        
        Args:
            config: ODSConfig with schema and table
            columns: Iterable of column names
        
        Returns:
            Tuple of (sql_query, column_names_list)
        """
        column_list = list(columns)
        quoted_schema = self._quote_identifier(config.schema)
        quoted_table = self._quote_identifier(config.table)
        quoted_columns = [self._quote_identifier(col) for col in column_list]
        
        # Generate placeholders ($1, $2, ...)
        placeholders = [f"${i+1}" for i in range(len(column_list))]
        
        sql = (
            f"INSERT INTO {quoted_schema}.{quoted_table} "
            f"({', '.join(quoted_columns)}) "
            f"VALUES ({', '.join(placeholders)})"
        )
        
        return sql, column_list
    
    def _build_upsert_query(self, config: ODSConfig, columns: List[str]) -> Tuple[str, List[str]]:
        """Build INSERT ON CONFLICT DO UPDATE query.
        
        Args:
            config: ODSConfig with schema, table, and identity_fields
            columns: List of column names
        
        Returns:
            Tuple of (sql_query, column_names_list)
        """
        # Build base INSERT
        quoted_schema = self._quote_identifier(config.schema)
        quoted_table = self._quote_identifier(config.table)
        quoted_columns = [self._quote_identifier(col) for col in columns]
        
        placeholders = [f"${i+1}" for i in range(len(columns))]
        
        # Build conflict target (identity fields)
        quoted_identity = [self._quote_identifier(col) for col in config.identity_fields]
        conflict_target = ', '.join(quoted_identity)
        
        # Build UPDATE SET clause for non-identity columns
        update_columns = [col for col in columns if col not in config.identity_fields]
        if update_columns:
            set_clauses = [f"{self._quote_identifier(col)} = EXCLUDED.{self._quote_identifier(col)}" 
                          for col in update_columns]
            update_clause = f"DO UPDATE SET {', '.join(set_clauses)}"
        else:
            # All columns are identity fields - just do nothing on conflict
            update_clause = "DO NOTHING"
        
        sql = (
            f"INSERT INTO {quoted_schema}.{quoted_table} "
            f"({', '.join(quoted_columns)}) "
            f"VALUES ({', '.join(placeholders)}) "
            f"ON CONFLICT ({conflict_target}) "
            f"{update_clause}"
        )
        
        return sql, columns
    
    def _quote_identifier(self, identifier: str) -> str:
        """Quote a SQL identifier (table/column name) safely.
        
        Validates that the identifier contains only safe characters,
        then wraps it in double quotes.
        
        Args:
            identifier: Table or column name
        
        Returns:
            Properly quoted identifier
        
        Raises:
            ValueError: If identifier contains unsafe characters
        """
        # Validate identifier matches safe pattern
        # Allow letters, digits, underscores (PostgreSQL standard)
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', identifier):
            raise ValueError(
                f"Invalid SQL identifier: '{identifier}'. "
                f"Identifiers must start with a letter or underscore and contain only "
                f"letters, digits, and underscores."
            )
        
        return f'"{identifier}"'
    
    def _sort_records_for_upsert(
        self,
        records: List[Dict[str, Any]],
        identity_fields: List[str]
    ) -> List[Dict[str, Any]]:
        """Sort records by identity fields to prevent deadlocks.
        
        When multiple transactions perform upserts concurrently, deadlocks can
        occur if they acquire locks in different orders. Sorting records by
        the conflict target ensures consistent lock ordering.
        
        Args:
            records: List of record dictionaries
            identity_fields: Fields to sort by
        
        Returns:
            Sorted list of records
        """
        if not identity_fields or len(records) <= 1:
            return records
        
        def sort_key(record: Dict[str, Any]) -> tuple:
            """Generate sort key from identity fields."""
            return tuple(record.get(field) for field in identity_fields)
        
        return sorted(records, key=sort_key)
    
    def _split_into_batches(
        self,
        records: List[Dict[str, Any]],
        batch_size: int
    ) -> List[List[Dict[str, Any]]]:
        """Split records into batches of specified size.
        
        Args:
            records: List of all records
            batch_size: Maximum batch size
        
        Returns:
            List of batches (each batch is a list of records)
        """
        if batch_size <= 0:
            raise ValueError(f"batch_size must be positive, got {batch_size}")
        
        batches = []
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            batches.append(batch)
        
        return batches
    
    def _classify_error(self, error: Exception, batch_number: int) -> ODSError:
        """Classify an exception into an ODSError.
        
        Maps asyncpg exceptions to ODSError with proper classification.
        
        Args:
            error: The exception that occurred
            batch_number: The batch number where the error occurred
        
        Returns:
            ODSError with classification and details
        """
        import asyncpg
        
        # Default error info
        error_type = 'UNKNOWN'
        message = str(error)
        sqlstate = None
        
        # Extract SQLSTATE and classify
        if isinstance(error, asyncpg.PostgresError):
            sqlstate = getattr(error, 'sqlstate', None)
            if sqlstate:
                error_type = ERROR_CODES.get(sqlstate, 'POSTGRES_ERROR')
        
        # Map specific exception types
        if isinstance(error, asyncpg.ConnectionDoesNotExistError):
            error_type = 'CONNECTION_ERROR'
        elif isinstance(error, asyncpg.ConnectionFailureError):
            error_type = 'CONNECTION_ERROR'
        elif isinstance(error, asyncpg.UniqueViolationError):
            error_type = 'UNIQUE_VIOLATION'
            sqlstate = '23505'
        elif isinstance(error, asyncpg.ForeignKeyViolationError):
            error_type = 'FK_VIOLATION'
            sqlstate = '23503'
        elif isinstance(error, asyncpg.DeadlockDetectedError):
            error_type = 'DEADLOCK'
            sqlstate = '40P01'
        elif isinstance(error, asyncpg.QueryCanceledError):
            error_type = 'TIMEOUT'
            sqlstate = '57014'
        elif isinstance(error, asyncpg.PostgresError):
            # Try to extract SQLSTATE from error message as fallback
            if not sqlstate:
                sqlstate_match = re.search(r'SQLSTATE[\s=]+(\w+)', str(error))
                if sqlstate_match:
                    sqlstate = sqlstate_match.group(1)
                    error_type = ERROR_CODES.get(sqlstate, 'POSTGRES_ERROR')
        
        return ODSError(
            batch_number=batch_number,
            error_type=error_type,
            message=message,
            sqlstate=sqlstate
        )
    
    @staticmethod
    async def create_connection(dsn: str) -> asyncpg.Connection:
        """Create a new connection with sensible defaults for ODS operations.
        
        This is a convenience factory method. The connection is still managed
        by the caller (caller must close it).
        
        Args:
            dsn: PostgreSQL connection string
        
        Returns:
            asyncpg Connection
        
        Example:
            conn = await ODSExecutor.create_connection("postgresql://user:pass@host/db")
            try:
                result = await executor.execute(config, records, conn)
            finally:
                await conn.close()
        """
        return await asyncpg.connect(
            dsn=dsn,
            command_timeout=300,  # 5 minutes
            server_settings={
                'application_name': 'dashboard_studio_ods_executor',
                'jit': 'off'  # Disable JIT for short OLTP queries
            }
        )


# Singleton instance for convenience
ods_executor = ODSExecutor()
