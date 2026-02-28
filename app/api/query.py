"""
Query Execution API Endpoints.

Phase 7: SQL Read Queries (Trino)
Phase 8: SQL Write Queries (Spark SQL) with automatic metadata updates

Endpoints:
- POST /query/execute - Execute SQL read queries (SELECT)
- POST /query/write - Execute SQL write queries (INSERT/UPDATE/DELETE/MERGE)
- POST /query/test-connection - Test Trino connection
- GET /query/table-info - Get table metadata
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.engines.trino_query_engine import TrinoQueryEngine
from app.engines.spark_query_engine import SparkQueryEngine
from app.engines.nl_query_engine import NaturalLanguageQueryEngine, NLQueryResult
from app.storage.snapshot_manager import SnapshotManager
from app.core.logger import get_logger
from app.core.settings import settings

import sys
print(f"[QUERY.PY MODULE DEBUG] Loading query.py from: {__file__}", file=sys.stderr, flush=True)
print(f"[QUERY.PY MODULE DEBUG] Settings API key loaded: {bool(settings.groq_api_key)}", file=sys.stderr, flush=True)

logger = get_logger()
router = APIRouter(prefix="/query")


# Test endpoint for Groq API
@router.get("/test-groq")
async def test_groq():
    """Test if Groq API key is working."""
    try:
        nl_engine = NaturalLanguageQueryEngine()
        result = nl_engine.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": "Say 'API working'"}],
            max_tokens=10
        )
        return {
            "success": True,
            "message": "Groq API key is valid!",
            "response": result.choices[0].message.content,
            "api_key_prefix": settings.groq_api_key[:15] if settings.groq_api_key else None
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "api_key_set": bool(settings.groq_api_key),
            "api_key_prefix": settings.groq_api_key[:15] if settings.groq_api_key else None
        }


@router.get("/test-simple")
async def test_simple():
    """Ultra simple test endpoint."""
    print("[TEST] Simple endpoint called!", flush=True)
    return {
        "success": True,
        "message": "Server is working!",
        "settings_api_key_loaded": bool(settings.groq_api_key),
        "settings_instance_id": id(settings)
    }


# ============================================================================
# Request/Response Models
# ============================================================================

class QueryExecuteRequest(BaseModel):
    """Request model for SQL query execution."""
    sql: str = Field(
        ...,
        description="SQL query to execute (SELECT statements only)",
        example="SELECT * FROM delta.default.sales_delta WHERE region = 'us-east' LIMIT 100"
    )
    parameters: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional query parameters for parameterized queries"
    )
    limit: Optional[int] = Field(
        default=1000,
        description="Maximum rows to return (overrides SQL LIMIT if present)",
        ge=1,
        le=100000
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "sql": "SELECT * FROM delta.default.sales_delta WHERE region = 'us-east'",
                    "limit": 100
                },
                {
                    "sql": "SELECT customer_id, SUM(amount) as total FROM delta.default.orders GROUP BY customer_id",
                    "limit": 50
                }
            ]
        }


class SimpleQueryRequest(BaseModel):
    """Simplified query request using catalog/schema/table."""
    catalog: str = Field(..., description="Trino catalog name", example="delta")
    schema: str = Field(..., description="Schema/database name", example="default")
    table: str = Field(..., description="Table name", example="sales_delta")
    filter: Optional[str] = Field(
        default=None,
        description="WHERE clause filter (without 'WHERE' keyword)",
        example="region = 'us-east' AND date >= '2024-01-01'"
    )
    columns: Optional[List[str]] = Field(
        default=None,
        description="Columns to select (defaults to all columns)",
        example=["id", "name", "price"]
    )
    limit: int = Field(
        default=1000,
        description="Maximum rows to return",
        ge=1,
        le=100000
    )


class SnapshotQueryRequest(BaseModel):
    """Query data from a specific snapshot version (Time Travel)."""
    storage_type: str = Field(..., description="Storage type", example="aws")
    bucket: str = Field(..., description="S3 bucket name", example="metadataproject")
    table_path: str = Field(
        ...,
        description="Path to Delta table in bucket",
        example="test-data/customer_data/customer_data_delta"
    )
    snapshot_id: str = Field(
        ...,
        description="Snapshot ID to query",
        example="snapshot_20260213_044224_cf52ef3e"
    )
    sql_query: Optional[str] = Field(
        default=None,
        description="Custom SQL query (use {table} placeholder for table path)",
        example="SELECT * FROM {table} WHERE age > 25"
    )
    columns: Optional[List[str]] = Field(
        default=None,
        description="Columns to select (if no custom SQL provided)",
        example=["customer_id", "name", "age"]
    )
    filter: Optional[str] = Field(
        default=None,
        description="WHERE clause (if no custom SQL provided)",
        example="age > 25 AND city = 'New York'"
    )
    limit: int = Field(
        default=1000,
        description="Maximum rows to return",
        ge=1,
        le=100000
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "storage_type": "aws",
                    "bucket": "metadataproject",
                    "table_path": "test-data/customer_data/customer_data_delta",
                    "snapshot_id": "snapshot_20260213_044224_cf52ef3e",
                    "columns": ["customer_id", "name", "email"],
                    "filter": "age > 30",
                    "limit": 100
                }
            ]
        }


class TableInfoRequest(BaseModel):
    """Request model for table metadata."""
    catalog: str = Field(..., description="Catalog name", example="delta")
    schema: str = Field(..., description="Schema name", example="default")
    table: str = Field(..., description="Table name", example="sales_delta")


class QueryResponse(BaseModel):
    """Response model for query execution."""
    success: bool
    row_count: int
    columns: List[str]
    data: List[Dict[str, Any]]
    execution_time_ms: int
    timestamp: str


# ============================================================================
# Phase 7: SQL Read Queries (Trino)
# ============================================================================

@router.post("/execute", response_model=QueryResponse)
async def execute_query(request: QueryExecuteRequest):
    """
    Execute SQL SELECT query using Trino.
    
    **What this does:**
    - Executes SQL queries on Delta Lake, Iceberg, Hudi, and Parquet tables
    - Returns query results as JSON
    - Uses Trino for extremely fast read performance (10-100x faster than Spark)
    
    **Supported Catalogs:**
    - `delta` - Delta Lake tables
    - `hive` - Parquet, Iceberg, Hudi tables
    
    **Query Examples:**
    ```sql
    -- Query Delta Lake table
    SELECT * FROM delta.default.sales_delta 
    WHERE region = 'us-east' LIMIT 100
    
    -- Query Parquet files directly
    SELECT * FROM hive.default."s3://bucket/path/to/parquet/"
    
    -- Aggregate query
    SELECT region, COUNT(*) as count, SUM(amount) as total
    FROM delta.default.sales_delta
    GROUP BY region
    
    -- Join tables
    SELECT s.*, c.customer_name 
    FROM delta.default.sales s
    JOIN delta.default.customers c ON s.customer_id = c.id
    ```
    
    **Performance:**
    - Small queries (< 1MB): ~50-200ms
    - Medium queries (1-10MB): ~200-1000ms
    - Large queries (10-100MB): ~1-5s
    
    **Limits:**
    - Max rows per query: 100,000 (configurable)
    - Query timeout: 300s (5 minutes)
    """
    try:
        logger.info(
            "Received query execution request",
            extra={"sql": request.sql[:200], "limit": request.limit}
        )
        
        # Add LIMIT clause if not present (skip for SHOW, DESCRIBE, EXPLAIN commands)
        sql = request.sql.strip()
        sql_upper = sql.upper()
        skip_limit_commands = ['SHOW ', 'DESCRIBE ', 'EXPLAIN ', 'CREATE ', 'ALTER ', 'DROP ']
        should_add_limit = (
            request.limit and 
            "LIMIT" not in sql_upper and 
            not any(sql_upper.startswith(cmd) for cmd in skip_limit_commands)
        )
        if should_add_limit:
            sql = f"{sql} LIMIT {request.limit}"
        
        # Create Trino engine and execute query
        engine = TrinoQueryEngine()
        result = engine.execute_query(sql, request.parameters)
        
        # Add timestamp
        result['timestamp'] = datetime.utcnow().isoformat() + "Z"
        
        logger.info(
            "Query executed successfully",
            extra={
                "row_count": result['row_count'],
                "execution_time_ms": result['execution_time_ms']
            }
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Query execution failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Query execution failed: {str(e)}"
        )


@router.post("/execute/simple", response_model=QueryResponse)
async def execute_simple_query(request: SimpleQueryRequest):
    """
    Execute simplified query using catalog/schema/table.
    
    **What this does:**
    - Simpler alternative to writing full SQL
    - Automatically builds SELECT query from parameters
    - Good for basic table queries
    
    **Example:**
    ```json
    {
      "catalog": "delta",
      "schema": "default",
      "table": "sales_delta",
      "filter": "region = 'us-east' AND amount > 100",
      "columns": ["id", "customer_name", "amount"],
      "limit": 50
    }
    ```
    
    Translates to:
    ```sql
    SELECT id, customer_name, amount 
    FROM delta.default.sales_delta 
    WHERE region = 'us-east' AND amount > 100 
    LIMIT 50
    ```
    """
    try:
        logger.info(
            "Received simple query request",
            extra={
                "catalog": request.catalog,
                "schema": request.schema,
                "table": request.table
            }
        )
        
        # Build SQL query
        columns_str = ", ".join(request.columns) if request.columns else "*"
        sql = f"SELECT {columns_str} FROM {request.catalog}.{request.schema}.{request.table}"
        
        if request.filter:
            sql += f" WHERE {request.filter}"
        
        sql += f" LIMIT {request.limit}"
        
        logger.info(f"Generated SQL: {sql}")
        
        # Execute query
        engine = TrinoQueryEngine()
        result = engine.execute_query(sql)
        result['timestamp'] = datetime.utcnow().isoformat() + "Z"
        
        return result
        
    except Exception as e:
        logger.error(f"Simple query execution failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Query execution failed: {str(e)}"
        )


@router.post("/execute/snapshot", response_model=QueryResponse)
async def execute_snapshot_query(request: SnapshotQueryRequest):
    """
    Execute SQL query on a specific snapshot version (Time Travel).
    
    **What this does:**
    - Queries data from a specific point in time using snapshot ID
    - Uses Delta Lake time travel (VERSION AS OF)
    - Lets you explore historical data versions
    
    **Use Cases:**
    - Audit: "What did the data look like at version X?"
    - Debug: "When did this row change?"
    - Reproducibility: Run the same analysis on historical data
    - Compliance: Access data as it existed at a specific time
    
    **How it works:**
    1. Retrieves snapshot metadata using snapshot_id
    2. Extracts Delta Lake version number from snapshot
    3. Builds SQL query with `VERSION AS OF <version>`
    4. Executes query and returns results
    
    **Example Request:**
    ```json
    {
      "storage_type": "aws",
      "bucket": "metadataproject",
      "table_path": "test-data/customer_data/customer_data_delta",
      "snapshot_id": "snapshot_20260213_044224_cf52ef3e",
      "columns": ["customer_id", "name", "email"],
      "filter": "age > 30",
      "limit": 100
    }
    ```
    
    **Custom SQL Example:**
    ```json
    {
      "storage_type": "aws",
      "bucket": "metadataproject",
      "table_path": "tables/orders_delta",
      "snapshot_id": "snapshot_20260213_120000_abc123",
      "sql_query": "SELECT region, COUNT(*) as count, SUM(amount) as total FROM {table} GROUP BY region",
      "limit": 50
    }
    ```
    
    **Response:**
    ```json
    {
      "success": true,
      "row_count": 15,
      "columns": ["customer_id", "name", "email"],
      "data": [
        {"customer_id": 1, "name": "John Doe", "email": "john@example.com"},
        {"customer_id": 2, "name": "Jane Smith", "email": "jane@example.com"}
      ],
      "execution_time_ms": 456,
      "timestamp": "2026-02-13T10:30:00Z"
    }
    ```
    """
    try:
        logger.info(
            "Received snapshot query request",
            extra={
                "snapshot_id": request.snapshot_id,
                "table_path": request.table_path,
                "bucket": request.bucket
            }
        )
        
        # Step 1: Retrieve snapshot metadata
        snapshot_manager = SnapshotManager()
        snapshot = snapshot_manager.get_snapshot_by_id(
            storage_type=request.storage_type,
            bucket=request.bucket,
            path=request.table_path,
            snapshot_id=request.snapshot_id
        )
        
        if not snapshot:
            raise HTTPException(
                status_code=404,
                detail=f"Snapshot not found: {request.snapshot_id}"
            )
        
        # Step 2: Extract Delta version from snapshot
        version_info = snapshot.get('version_info', {})
        delta_version = version_info.get('version')
        
        # Handle "unknown" version by defaulting to 0 (initial version)
        if delta_version is None or delta_version == "unknown":
            logger.warning(
                f"Snapshot {request.snapshot_id} has unknown version, defaulting to version 0"
            )
            delta_version = 0
        
        logger.info(f"Found Delta version {delta_version} for snapshot {request.snapshot_id}")
        
        # Step 3: Build SQL query
        if request.sql_query:
            # User provided custom SQL
            sql = request.sql_query
        else:
            # Build query from parameters
            columns_str = ", ".join(request.columns) if request.columns else "*"
            sql = f"SELECT {columns_str} FROM {{table}}"
            
            if request.filter:
                sql += f" WHERE {request.filter}"
        
        logger.info(
            f"Executing time travel query",
            extra={
                "sql": sql[:200],
                "delta_version": delta_version,
                "snapshot_id": request.snapshot_id
            }
        )
        
        # Step 4: Execute query using Spark (supports Delta time travel)
        spark_engine = SparkQueryEngine()
        result = spark_engine.execute_query(
            storage_type=request.storage_type,
            bucket=request.bucket,
            table_path=request.table_path,
            sql=sql,
            version=delta_version,
            limit=request.limit
        )
        result['timestamp'] = datetime.utcnow().isoformat() + "Z"
        
        logger.info(
            f"Snapshot query executed successfully",
            extra={
                "snapshot_id": request.snapshot_id,
                "delta_version": delta_version,
                "row_count": result['row_count']
            }
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Snapshot query execution failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Snapshot query failed: {str(e)}"
        )


@router.get("/table-info")
async def get_table_info(
    catalog: str,
    schema: str,
    table: str
):
    """
    Get table metadata (columns, types).
    
    **What this does:**
    - Returns table schema information
    - Shows column names, data types, and comments
    - Uses Trino DESCRIBE command
    
    **Example:**
    ```
    GET /query/table-info?catalog=delta&schema=default&table=sales_delta
    ```
    
    **Response:**
    ```json
    {
      "success": true,
      "catalog": "delta",
      "schema": "default",
      "table": "sales_delta",
      "columns": [
        {"name": "id", "type": "integer", "nullable": true},
        {"name": "name", "type": "varchar", "nullable": true}
      ]
    }
    ```
    """
    try:
        logger.info(
            "Getting table info",
            extra={"catalog": catalog, "schema": schema, "table": table}
        )
        
        engine = TrinoQueryEngine()
        result = engine.get_table_info(catalog, schema, table)
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to get table info: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get table info: {str(e)}"
        )


@router.post("/test-connection")
async def test_trino_connection():
    """
    Test Trino connection and get cluster info.
    
    **What this does:**
    - Validates Trino is running and accessible
    - Returns Trino version and available catalogs
    - Use this to verify setup before running queries
    
    **Response:**
    ```json
    {
      "success": true,
      "message": "Connected to Trino successfully",
      "version": "435",
      "catalogs": ["delta", "hive", "system"],
      "host": "trino",
      "port": 8080
    }
    ```
    """
    try:
        logger.info("Testing Trino connection")
        
        engine = TrinoQueryEngine()
        result = engine.test_connection()
        
        return result
        
    except Exception as e:
        logger.error(f"Trino connection test failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Trino connection test failed: {str(e)}"
        )


@router.get("/snapshots/list")
async def list_table_snapshots(
    storage_type: str,
    bucket: str,
    table_path: str
):
    """
    List all available snapshots for a table.
    
    **What this does:**
    - Shows all snapshot versions available for time travel queries
    - Returns snapshot IDs, timestamps, and Delta versions
    - Use this to find which snapshot_id to query
    
    **Example:**
    ```
    GET /query/snapshots/list?storage_type=aws&bucket=metadataproject&table_path=test-data/customer_data/customer_data_delta
    ```
    
    **Response:**
    ```json
    {
      "success": true,
      "table_path": "test-data/customer_data/customer_data_delta",
      "snapshot_count": 4,
      "snapshots": [
        {
          "snapshot_id": "snapshot_20260213_044224_cf52ef3e",
          "timestamp": "2026-02-13T04:43:31Z",
          "delta_version": 0,
          "schema_columns": 4,
          "file_count": 1
        },
        {
          "snapshot_id": "snapshot_20260208_153954_06446497",
          "timestamp": "2026-02-08T15:40:12Z",
          "delta_version": 0,
          "schema_columns": 4,
          "file_count": 1
        }
      ]
    }
    ```
    
    **Use this to:**
    - Find snapshot IDs for time travel queries
    - See when data changed (different versions)
    - Verify snapshots exist before querying
    """
    try:
        logger.info(
            "Listing snapshots",
            extra={"bucket": bucket, "table_path": table_path}
        )
        
        # Get all snapshots
        snapshot_manager = SnapshotManager()
        snapshots_list = snapshot_manager.list_snapshots(
            storage_type=storage_type,
            bucket=bucket,
            path=table_path
        )
        
        # For each snapshot, extract key info
        result_snapshots = []
        for snapshot_info in snapshots_list:
            snapshot_id = snapshot_info['snapshot_id']
            
            # Load full snapshot to get version info
            snapshot_data = snapshot_manager.get_snapshot_by_id(
                storage_type=storage_type,
                bucket=bucket,
                path=table_path,
                snapshot_id=snapshot_id
            )
            
            if snapshot_data:
                version_info = snapshot_data.get('version_info', {})
                schema = snapshot_data.get('schema', {})
                files = snapshot_data.get('files', {})
                
                result_snapshots.append({
                    "snapshot_id": snapshot_id,
                    "timestamp": snapshot_data.get('generated_at'),
                    "delta_version": version_info.get('version'),
                    "table_format": snapshot_data.get('table_format'),
                    "schema_columns": len(schema.get('fields', [])),
                    "file_count": files.get('file_count', 0),
                    "total_size_bytes": files.get('total_size_bytes', 0)
                })
        
        response = {
            "success": True,
            "storage_type": storage_type,
            "bucket": bucket,
            "table_path": table_path,
            "snapshot_count": len(result_snapshots),
            "snapshots": result_snapshots
        }
        
        logger.info(f"Found {len(result_snapshots)} snapshots")
        return response
        
    except Exception as e:
        logger.error(f"Failed to list snapshots: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list snapshots: {str(e)}"
        )


# ============================================================================
# Phase 8: SQL Write Queries (Spark SQL) - Coming Soon
# ============================================================================

class QueryWriteRequest(BaseModel):
    """Request model for write queries (Phase 8)."""
    sql: str = Field(
        ...,
        description="SQL write query (INSERT/UPDATE/DELETE/MERGE)",
        example="INSERT INTO delta.`s3a://bucket/table` VALUES (1, 'John', 100)"
    )
    storage_type: str = Field(..., description="Storage type", example="aws")
    bucket: str = Field(..., description="S3 bucket name", example="metadataproject")
    target_path: str = Field(
        ...,
        description="Target table path in S3",
        example="tables/sales_delta"
    )
    auto_snapshot: bool = Field(
        default=True,
        description="Automatically generate metadata snapshot after write"
    )


@router.post("/sync-table")
async def sync_delta_table_to_trino(
    storage_type: str,
    bucket: str,
    table_path: str,
    schema_name: str = "default",
    table_name: Optional[str] = None
):
    """
    Auto-sync Delta table to Trino by reading _delta_log/ metadata.
    
    **What this does:**
    - Reads schema from Delta Lake transaction log (_delta_log/)
    - Automatically creates Trino schema if needed
    - Registers table in Trino catalog
    - Enables fast Trino queries on your data
    
    **Example:**
    ```
    POST /query/sync-table?storage_type=aws&bucket=metadataproject&table_path=test-data/customer_data/customer_data_delta&schema_name=default
    ```
    
    **Response:**
    ```json
    {
      "success": true,
      "message": "Table synced successfully",
      "catalog": "delta",
      "schema": "default",
      "table": "customer_data_delta",
      "location": "s3://metadataproject/test-data/customer_data/customer_data_delta/",
      "columns": ["CustomerID", "Name", "Email", "City"]
    }
    ```
    
    **After syncing, you can use fast Trino queries:**
    ```sql
    SELECT * FROM delta.default.customer_data_delta WHERE City = 'Mumbai'
    ```
    """
    try:
        logger.info(
            f"Syncing Delta table to Trino",
            extra={"bucket": bucket, "table_path": table_path}
        )
        
        # Extract table name from path if not provided
        if not table_name:
            table_name = table_path.rstrip('/').split('/')[-1]
            # Remove _delta suffix if present
            if table_name.endswith('_delta'):
                pass  # Keep as is
            else:
                table_name = table_name + "_delta"
        
        # Build S3 location
        s3_location = f"s3://{bucket}/{table_path.rstrip('/')}/"
        
        # Get snapshot to extract schema
        snapshot_manager = SnapshotManager()
        snapshots_list = snapshot_manager.list_snapshots(
            storage_type=storage_type,
            bucket=bucket,
            path=table_path
        )
        
        if not snapshots_list:
            raise HTTPException(
                status_code=404,
                detail=f"No snapshots found for table {table_path}. Generate metadata first using /metadata/generate"
            )
        
        # Get latest snapshot
        latest_snapshot_id = snapshots_list[0]['snapshot_id']
        snapshot_data = snapshot_manager.get_snapshot_by_id(
            storage_type=storage_type,
            bucket=bucket,
            path=table_path,
            snapshot_id=latest_snapshot_id
        )
        
        # Extract schema
        schema = snapshot_data.get('schema', {})
        fields = schema.get('fields', [])
        
        if not fields:
            raise HTTPException(
                status_code=400,
                detail="No schema found in Delta table metadata"
            )
        
        # Map Delta types to Trino types
        type_mapping = {
            'string': 'VARCHAR',
            'integer': 'INTEGER',
            'long': 'BIGINT',
            'double': 'DOUBLE',
            'float': 'REAL',
            'boolean': 'BOOLEAN',
            'timestamp': 'TIMESTAMP',
            'date': 'DATE',
            'binary': 'VARBINARY'
        }
        
        columns = []
        for field in fields:
            field_name = field.get('name')
            field_type = field.get('type', 'string').lower()
            trino_type = type_mapping.get(field_type, 'VARCHAR')
            columns.append(f"{field_name} {trino_type}")
        
        columns_def = ", ".join(columns)
        
        # Step 1: Create schema if not exists
        engine = TrinoQueryEngine()
        try:
            create_schema_sql = f"CREATE SCHEMA IF NOT EXISTS delta.{schema_name} WITH (location = 's3://{bucket}/{table_path.split('/')[0]}/')"
            logger.info(f"Creating schema: {create_schema_sql}")
            engine.execute_query(create_schema_sql)
        except Exception as schema_err:
            logger.warning(f"Schema creation skipped: {schema_err}")
        
        # Step 2: Unregister existing table if it exists (to refresh)
        try:
            unregister_sql = f"CALL delta.system.unregister_table(schema_name => '{schema_name}', table_name => '{table_name}')"
            logger.info(f"Unregistering existing table: {unregister_sql}")
            engine.execute_query(unregister_sql)
        except Exception as unreg_err:
            logger.warning(f"Table unregister skipped (may not exist): {unreg_err}")
        
        # Step 3: Register table using system procedure (for existing Delta data)
        register_sql = f"CALL delta.system.register_table(schema_name => '{schema_name}', table_name => '{table_name}', table_location => '{s3_location}')"
        
        logger.info(f"Registering table: {register_sql}")
        engine.execute_query(register_sql)
        
        # Step 4: Verify table exists
        verify_sql = f"SELECT COUNT(*) as row_count FROM delta.{schema_name}.{table_name} LIMIT 1"
        result = engine.execute_query(verify_sql)
        
        logger.info(
            f"Table synced successfully",
            extra={
                "schema": schema_name,
                "table": table_name,
                "location": s3_location
            }
        )
        
        return {
            "success": True,
            "message": "Table synced successfully to Trino",
            "catalog": "delta",
            "schema": schema_name,
            "table": table_name,
            "location": s3_location,
            "columns": [field.get('name') for field in fields],
            "trino_query_example": f"SELECT * FROM delta.{schema_name}.{table_name} LIMIT 10"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to sync table: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to sync table: {str(e)}"
        )


# ============================================================================
# Natural Language Query Endpoint (Phase 7.5)
# ============================================================================

class NaturalQueryRequest(BaseModel):
    """Request model for natural language queries."""
    query: str = Field(
        ...,
        description="Natural language question or command",
        example="Show me all customers from Mumbai"
    )
    storage_type: str = Field(
        default="aws",
        description="Storage backend (aws, minio)",
        example="aws"
    )
    bucket: str = Field(
        ...,
        description="S3 bucket name",
        example="metadataproject"
    )
    table_path: str = Field(
        ...,
        description="Path to table in bucket",
        example="test-data/customer_data/customer_data_delta"
    )
    catalog: str = Field(
        default="delta",
        description="Trino catalog name (for fast queries)",
        example="delta"
    )
    schema_name: str = Field(
        default="default",
        description="Trino schema name (for fast queries)",
        example="default"
    )
    use_trino: bool = Field(
        default=True,
        description="Use Trino for fast queries (False = use Spark for time travel)",
        example=True
    )
    auto_sync: bool = Field(
        default=True,
        description="Automatically sync table to Trino if not registered",
        example=True
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "query": "Show me all customers from Mumbai",
                    "storage_type": "aws",
                    "bucket": "metadataproject",
                    "table_path": "test-data/customer_data/customer_data_delta",
                    "use_trino": True
                },
                {
                    "query": "Count customers by city",
                    "storage_type": "aws",
                    "bucket": "metadataproject",
                    "table_path": "test-data/customer_data/customer_data_delta"
                },
                {
                    "query": "List all snapshots",
                    "storage_type": "aws",
                    "bucket": "metadataproject",
                    "table_path": "test-data/customer_data/customer_data_delta"
                }
            ]
        }


class ApprovedQueryRequest(BaseModel):
    """Request model for executing pre-approved queries."""
    operation: str = Field(
        ...,
        description="Operation type from preview",
        example="query"
    )
    sql: Optional[str] = Field(
        default=None,
        description="Generated SQL from preview",
        example="SELECT * FROM delta.default.customer_data_delta WHERE City = 'Mumbai' LIMIT 100"
    )
    storage_type: str = Field(
        default="aws",
        description="Storage backend",
        example="aws"
    )
    bucket: str = Field(
        ...,
        description="S3 bucket name",
        example="metadataproject"
    )
    table_path: str = Field(
        ...,
        description="Path to table in bucket",
        example="test-data/customer_data/customer_data_delta"
    )
    catalog: str = Field(
        default="delta",
        description="Trino catalog name",
        example="delta"
    )
    schema_name: str = Field(
        default="default",
        description="Trino schema name",
        example="default"
    )
    use_trino: bool = Field(
        default=True,
        description="Use Trino for execution",
        example=True
    )
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional parameters from preview"
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "operation": "query",
                    "sql": "SELECT * FROM delta.default.customer_data_delta WHERE City = 'Mumbai' LIMIT 100",
                    "storage_type": "aws",
                    "bucket": "metadataproject",
                    "table_path": "test-data/customer_data/customer_data_delta",
                    "use_trino": True
                }
            ]
        }


@router.post("/natural/preview", response_model=Dict[str, Any])
async def preview_natural_query(request: NaturalQueryRequest):
    """
    🔍 **Preview Natural Language Query** - See generated SQL before execution!
    
    **What this does:**
    1. Converts your natural language question into SQL
    2. Shows you the generated query
    3. Returns operation details WITHOUT executing
    4. Allows you to approve or modify before running
    
    **Use this when:**
    - You want to verify SQL before execution
    - Learning what SQL the AI generates
    - Need to modify the query before running
    - Want to ensure query is correct
    
    **Workflow:**
    1. POST /query/natural/preview → Get SQL
    2. Review the SQL
    3. POST /query/natural/execute → Run if approved
    
    **Example Request:**
    ```json
    {
      "query": "Show me all customers from Mumbai",
      "storage_type": "aws",
      "bucket": "metadataproject",
      "table_path": "test-data/customer_data/customer_data_delta"
    }
    ```
    
    **Example Response:**
    ```json
    {
      "success": true,
      "operation": "query",
      "sql": "SELECT * FROM delta.default.customer_data_delta WHERE City = 'Mumbai' LIMIT 100",
      "explanation": "Filtering customers by city Mumbai",
      "parameters": {"filter": "City = 'Mumbai'", "limit": 100},
      "ready_to_execute": true,
      "approval_required": true,
      "estimated_rows": "≤100"
    }
    ```
    
    **Next Step:**
    - If SQL looks good → Use POST /query/natural/execute with the response
    - If SQL needs changes → Modify and use POST /query/execute directly
    """
    try:
        logger.info(
            "Received natural language preview request",
            extra={"query": request.query[:100]}
        )
        
        # Step 1: Get table schema for better SQL generation
        table_schema = None
        table_name = request.table_path.split('/')[-1]
        
        if request.use_trino:
            try:
                trino_engine = TrinoQueryEngine()
                schema_result = trino_engine.get_table_info(
                    catalog=request.catalog,
                    schema=request.schema_name,
                    table=table_name
                )
                if schema_result['success']:
                    table_schema = {
                        col['name']: col['type']
                        for col in schema_result.get('columns', [])
                    }
            except Exception as e:
                logger.warning(f"Could not get table schema from Trino: {e}")
        
        # Step 2: Process natural language query
        nl_engine = NaturalLanguageQueryEngine()
        llm_result = nl_engine.process_query(
            natural_query=request.query,
            storage_type=request.storage_type,
            bucket=request.bucket,
            table_path=request.table_path,
            table_schema=table_schema
        )
        
        nl_result = NLQueryResult(llm_result)
        
        logger.info(
            "LLM generated query preview",
            extra={
                "operation": nl_result.operation,
                "has_sql": nl_result.sql is not None
            }
        )
        
        # Step 3: Return preview WITHOUT executing
        response = {
            "success": True,
            "operation": nl_result.operation,
            "sql": nl_result.sql,
            "explanation": nl_result.explanation,
            "parameters": nl_result.parameters,
            "natural_query": request.query,
            "ready_to_execute": True,
            "approval_required": True,
            "table_info": {
                "storage_type": request.storage_type,
                "bucket": request.bucket,
                "table_path": request.table_path,
                "catalog": request.catalog,
                "schema": request.schema_name,
                "table_name": table_name
            }
        }
        
        # Add helpful metadata
        if nl_result.operation in ["query", "query_snapshot"]:
            response["estimated_rows"] = f"≤{nl_result.parameters.get('limit', 1000)}"
            response["engine"] = "trino" if request.use_trino else "spark"
            response["execution_time_estimate"] = "100-500ms" if request.use_trino else "30-60s"
        
        if nl_result.needs_sync:
            response["warning"] = "Table needs to be synced to Trino first"
            response["auto_sync"] = request.auto_sync
        
        logger.info(
            "Natural language query preview generated",
            extra={"operation": nl_result.operation}
        )
        
        return response
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Natural language preview failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Preview failed: {str(e)}"
        )


@router.post("/natural/execute", response_model=Dict[str, Any])
async def execute_approved_query(request: ApprovedQueryRequest):
    """
    ✅ **Execute Pre-Approved Query** - Run query after user approval!
    
    **What this does:**
    - Executes SQL that was previewed and approved by user
    - Uses the exact SQL from /natural/preview response
    - Returns query results
    
    **Workflow:**
    1. User asks: "Show customers from Mumbai"
    2. POST /natural/preview → Returns SQL for review
    3. User approves SQL
    4. POST /natural/execute → Runs the query
    
    **Example Request:**
    ```json
    {
      "operation": "query",
      "sql": "SELECT * FROM delta.default.customer_data_delta WHERE City = 'Mumbai' LIMIT 100",
      "storage_type": "aws",
      "bucket": "metadataproject",
      "table_path": "test-data/customer_data/customer_data_delta",
      "use_trino": true
    }
    ```
    
    **Example Response:**
    ```json
    {
      "success": true,
      "operation": "query",
      "sql": "SELECT * FROM delta.default.customer_data_delta WHERE City = 'Mumbai' LIMIT 100",
      "row_count": 2,
      "columns": ["CustomerID", "Name", "Email", "City"],
      "data": [...],
      "execution_time_ms": 156,
      "engine": "trino"
    }
    ```
    """
    try:
        logger.info(
            "Executing approved query",
            extra={"operation": request.operation}
        )
        
        table_name = request.table_path.split('/')[-1]
        result = None
        
        # Route based on operation type
        if request.operation == "list_snapshots":
            snapshot_manager = SnapshotManager(
                storage_type=request.storage_type,
                bucket=request.bucket
            )
            snapshots = snapshot_manager.list_snapshots(request.table_path)
            
            result = {
                "success": True,
                "operation": "list_snapshots",
                "snapshot_count": len(snapshots),
                "snapshots": snapshots
            }
        
        elif request.operation == "table_info":
            if request.use_trino:
                trino_engine = TrinoQueryEngine()
                result = trino_engine.get_table_info(
                    catalog=request.catalog,
                    schema=request.schema_name,
                    table=table_name
                )
            else:
                snapshot_manager = SnapshotManager(
                    storage_type=request.storage_type,
                    bucket=request.bucket
                )
                snapshots = snapshot_manager.list_snapshots(request.table_path)
                if snapshots:
                    latest = snapshots[0]
                    result = {
                        "success": True,
                        "operation": "table_info",
                        "columns": latest.get('schema', {}).get('fields', []),
                        "file_count": latest.get('file_count', 0)
                    }
        
        elif request.operation in ["query", "query_snapshot"]:
            if not request.sql:
                raise HTTPException(
                    status_code=400,
                    detail="SQL is required for query execution"
                )
            
            # Check if table needs sync
            if request.use_trino:
                try:
                    trino_engine = TrinoQueryEngine()
                    test_sql = f"SELECT COUNT(*) FROM {request.catalog}.{request.schema_name}.{table_name}"
                    trino_engine.execute_query(test_sql)
                except Exception as e:
                    if "does not exist" in str(e).lower():
                        logger.info("Table not registered, syncing...")
                        # Sync table
                        snapshot_manager = SnapshotManager(
                            storage_type=request.storage_type,
                            bucket=request.bucket
                        )
                        snapshots = snapshot_manager.list_snapshots(request.table_path)
                        
                        if snapshots:
                            trino_engine = TrinoQueryEngine()
                            trino_engine.execute_query(
                                f"CREATE SCHEMA IF NOT EXISTS {request.catalog}.{request.schema_name}"
                            )
                            
                            try:
                                unregister_sql = f"""
                                CALL {request.catalog}.system.unregister_table(
                                    schema_name => '{request.schema_name}',
                                    table_name => '{table_name}'
                                )
                                """
                                trino_engine.execute_query(unregister_sql)
                            except:
                                pass
                            
                            s3_location = f"s3://{request.bucket}/{request.table_path}/"
                            register_sql = f"""
                            CALL {request.catalog}.system.register_table(
                                schema_name => '{request.schema_name}',
                                table_name => '{table_name}',
                                table_location => '{s3_location}'
                            )
                            """
                            trino_engine.execute_query(register_sql)
                            logger.info(f"Table {table_name} synced")
            
            # Execute query
            if request.use_trino:
                trino_engine = TrinoQueryEngine()
                result = trino_engine.execute_query(request.sql)
                result["sql"] = request.sql
                result["engine"] = "trino"
            else:
                spark_engine = SparkQueryEngine()
                result = spark_engine.execute_query(
                    storage_type=request.storage_type,
                    bucket=request.bucket,
                    table_path=request.table_path,
                    sql=request.sql,
                    limit=request.parameters.get('limit', 1000)
                )
                result["sql"] = request.sql
                result["engine"] = "spark"
        
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown operation: {request.operation}"
            )
        
        if result:
            result["operation"] = request.operation
        
        logger.info(
            "Approved query executed successfully",
            extra={"operation": request.operation}
        )
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Approved query execution failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Execution failed: {str(e)}"
        )


@router.post("/natural", response_model=Dict[str, Any])
async def execute_natural_query(request: NaturalQueryRequest):
    """
    🎯 **Natural Language Query Interface** - Ask questions in plain English!
    
    ⚠️ **NEW: Two-Step Workflow Available**
    - Use `/query/natural/preview` to see generated SQL first
    - Then use `/query/natural/execute` to run after approval
    - This endpoint executes immediately (use for trusted automated queries)
    
    **What this does:**
    - Converts your natural language question into SQL
    - Automatically determines the operation type
    - **Executes immediately** without confirmation
    - Returns results in a friendly format
    
    **Powered by:** Groq API (Llama 3.3 70B)
    
    ---
    
    **⚠️ RECOMMENDED WORKFLOW (with approval):**
    
    **Step 1: Preview Query**
    ```
    POST /query/natural/preview
    {
      "query": "Show customers from Mumbai",
      "bucket": "metadataproject",
      "table_path": "test-data/customer_data/customer_data_delta"
    }
    ```
    
    **Step 2: Review SQL**
    ```json
    {
      "sql": "SELECT * FROM delta.default.customer_data_delta WHERE City = 'Mumbai'",
      "explanation": "Filtering customers by city",
      "approval_required": true
    }
    ```
    
    **Step 3: Execute if Approved**
    ```
    POST /query/natural/execute
    (Use response from preview)
    ```
    
    ---
    
    **Example Queries:**
    
    **1. Simple Data Retrieval:**
    ```
    "Show me all customers"
    "Give me top 10 customers"
    "List customers from Mumbai"
    ```
    
    **2. Filtering:**
    ```
    "Show customers where city is Delhi"
    "Find customers with gmail email"
    "Get customers whose name starts with A"
    ```
    
    **3. Aggregations:**
    ```
    "Count customers by city"
    "How many customers are there?"
    "Show me cities with more than 100 customers"
    ```
    
    **4. Operations:**
    ```
    "List all snapshots"
    "What columns does this table have?"
    "Show me table schema"
    "Give me snapshots at this location"
    ```
    
    **5. Complex Queries:**
    ```
    "Show me customers from Mumbai with Gmail emails"
    "Count how many customers are in each city, sorted by count"
    "Find all customers added in the last 30 days"
    ```
    
    ---
    
    **How it works:**
    1. Your question → Groq LLM
    2. LLM generates SQL or determines operation
    3. Execute query (Trino for speed, Spark for time travel)
    4. Return results with explanation
    
    **Response includes:**
    - `operation`: What operation was performed
    - `sql`: Generated SQL (if applicable)
    - `explanation`: Human-readable explanation
    - `data`: Query results
    - `execution_time_ms`: How long it took
    
    **Settings:**
    - `use_trino=true`: Fast queries (100ms), current data only
    - `use_trino=false`: Slower (30-60s), supports time travel
    - `auto_sync=true`: Automatically register table if needed
    """
    try:
        logger.info(
            "Received natural language query",
            extra={"query": request.query[:100]}
        )
        
        # Step 1: Get table schema for better SQL generation
        table_schema = None
        table_name = request.table_path.split('/')[-1]
        
        if request.use_trino:
            try:
                # Try to get schema from Trino
                trino_engine = TrinoQueryEngine()
                schema_result = trino_engine.get_table_info(
                    catalog=request.catalog,
                    schema=request.schema_name,
                    table=table_name
                )
                if schema_result['success']:
                    table_schema = {
                        col['name']: col['type']
                        for col in schema_result.get('columns', [])
                    }
            except Exception as e:
                logger.warning(f"Could not get table schema from Trino: {e}")
                # Table might not be registered yet
        
        # Step 2: Process natural language query
        print(f"[ENDPOINT DEBUG] About to create NL engine", flush=True)
        print(f"[ENDPOINT DEBUG] Settings instance ID: {id(settings)}", flush=True)
        print(f"[ENDPOINT DEBUG] Settings API key: {settings.groq_api_key[:20] if settings.groq_api_key else 'NONE'}...", flush=True)
        nl_engine = NaturalLanguageQueryEngine()
        print(f"[ENDPOINT DEBUG] NL engine created successfully!", flush=True)
        llm_result = nl_engine.process_query(
            natural_query=request.query,
            storage_type=request.storage_type,
            bucket=request.bucket,
            table_path=request.table_path,
            table_schema=table_schema
        )
        
        nl_result = NLQueryResult(llm_result)
        
        logger.info(
            "LLM processed query",
            extra={
                "operation": nl_result.operation,
                "has_sql": nl_result.sql is not None
            }
        )
        
        # Step 3: Route to appropriate operation
        result = None
        
        if nl_result.operation == "list_snapshots":
            # List snapshots
            snapshot_manager = SnapshotManager(
                storage_type=request.storage_type,
                bucket=request.bucket
            )
            snapshots = snapshot_manager.list_snapshots(request.table_path)
            
            result = {
                "success": True,
                "operation": "list_snapshots",
                "explanation": nl_result.explanation,
                "snapshot_count": len(snapshots),
                "snapshots": snapshots
            }
        
        elif nl_result.operation == "table_info":
            # Get table info
            if request.use_trino:
                trino_engine = TrinoQueryEngine()
                result = trino_engine.get_table_info(
                    catalog=request.catalog,
                    schema=request.schema_name,
                    table=table_name
                )
                result["explanation"] = nl_result.explanation
            else:
                # Use snapshot metadata
                snapshot_manager = SnapshotManager(
                    storage_type=request.storage_type,
                    bucket=request.bucket
                )
                snapshots = snapshot_manager.list_snapshots(request.table_path)
                if snapshots:
                    latest = snapshots[0]
                    result = {
                        "success": True,
                        "operation": "table_info",
                        "explanation": nl_result.explanation,
                        "columns": latest.get('schema', {}).get('fields', []),
                        "file_count": latest.get('file_count', 0)
                    }
        
        elif nl_result.operation == "test_connection":
            # Test connection
            trino_engine = TrinoQueryEngine()
            result = trino_engine.test_connection()
            result["explanation"] = nl_result.explanation
        
        elif nl_result.operation in ["query", "query_snapshot"]:
            # Execute SQL query
            if not nl_result.sql:
                raise HTTPException(
                    status_code=400,
                    detail="LLM did not generate SQL for query operation"
                )
            
            # Check if table needs sync (for Trino queries)
            if request.use_trino and request.auto_sync:
                try:
                    # Try a simple query to test if table exists
                    trino_engine = TrinoQueryEngine()
                    test_sql = f"SELECT COUNT(*) FROM {request.catalog}.{request.schema_name}.{table_name}"
                    trino_engine.execute_query(test_sql)
                except Exception as e:
                    if "does not exist" in str(e).lower():
                        logger.info("Table not registered in Trino, syncing...")
                        # Sync table first
                        snapshot_manager = SnapshotManager(
                            storage_type=request.storage_type,
                            bucket=request.bucket
                        )
                        snapshots = snapshot_manager.list_snapshots(request.table_path)
                        
                        if snapshots:
                            latest_snapshot = snapshots[0]
                            schema_fields = latest_snapshot.get('schema', {}).get('fields', [])
                            
                            # Create schema
                            trino_engine = TrinoQueryEngine()
                            trino_engine.execute_query(
                                f"CREATE SCHEMA IF NOT EXISTS {request.catalog}.{request.schema_name}"
                            )
                            
                            # Unregister old version
                            try:
                                unregister_sql = f"""
                                CALL {request.catalog}.system.unregister_table(
                                    schema_name => '{request.schema_name}',
                                    table_name => '{table_name}'
                                )
                                """
                                trino_engine.execute_query(unregister_sql)
                            except:
                                pass  # Table might not exist
                            
                            # Register table
                            s3_location = f"s3://{request.bucket}/{request.table_path}/"
                            register_sql = f"""
                            CALL {request.catalog}.system.register_table(
                                schema_name => '{request.schema_name}',
                                table_name => '{table_name}',
                                table_location => '{s3_location}'
                            )
                            """
                            trino_engine.execute_query(register_sql)
                            logger.info(f"Table {table_name} synced to Trino")
            
            # Execute query
            if request.use_trino:
                # Use Trino for fast queries
                trino_engine = TrinoQueryEngine()
                result = trino_engine.execute_query(nl_result.sql)
                result["sql"] = nl_result.sql
                result["explanation"] = nl_result.explanation
                result["engine"] = "trino"
            else:
                # Use Spark for time travel support
                spark_engine = SparkQueryEngine()
                result = spark_engine.execute_query(
                    storage_type=request.storage_type,
                    bucket=request.bucket,
                    table_path=request.table_path,
                    sql=nl_result.sql,
                    limit=nl_result.parameters.get('limit', 1000)
                )
                result["sql"] = nl_result.sql
                result["explanation"] = nl_result.explanation
                result["engine"] = "spark"
        
        elif nl_result.operation == "sync_table":
            # Sync table to Trino
            # (Implementation similar to /sync-table endpoint)
            result = {
                "success": True,
                "operation": "sync_table",
                "explanation": nl_result.explanation,
                "message": "Please use POST /query/sync-table endpoint for manual sync"
            }
        
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown operation: {nl_result.operation}"
            )
        
        # Add metadata to result
        if result:
            result["natural_query"] = request.query
            result["operation"] = nl_result.operation
            if not result.get("explanation"):
                result["explanation"] = nl_result.explanation
        
        logger.info(
            "Natural language query executed successfully",
            extra={"operation": nl_result.operation}
        )
        
        return result
    
    except HTTPException:
        raise
    except ValueError as e:
        # Likely Groq API key not set
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Natural language query failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Query failed: {str(e)}"
        )


@router.post("/write")
async def execute_write_query(
    request: QueryWriteRequest,
    background_tasks: BackgroundTasks
):
    """
    Execute SQL write query using Spark SQL (Phase 8).
    
    **⚠️ Coming in Phase 8 - Not yet implemented**
    
    **What this will do:**
    - Execute INSERT/UPDATE/DELETE/MERGE operations
    - Use Spark SQL for ACID transactions
    - Automatically generate metadata snapshot after write
    - Support Delta Lake, Iceberg, Hudi formats
    
    **Example Queries:**
    ```sql
    -- Insert data
    INSERT INTO delta.`s3a://bucket/sales_delta`
    VALUES (1, 'Product A', 19.99, 'us-east')
    
    -- Update rows
    UPDATE delta.`s3a://bucket/sales_delta`
    SET price = price * 1.1
    WHERE region = 'us-east'
    
    -- Delete rows
    DELETE FROM delta.`s3a://bucket/sales_delta`
    WHERE date < '2023-01-01'
    
    -- Merge (Upsert)
    MERGE INTO delta.`s3a://bucket/sales_delta` t
    USING source s
    ON t.id = s.id
    WHEN MATCHED THEN UPDATE SET *
    WHEN NOT MATCHED THEN INSERT *
    ```
    
    **Auto Metadata Update:**
    - After successful write, automatically generates new metadata snapshot
    - Tracks schema changes, row count changes, new partitions
    - Snapshot stored in S3 for version history
    """
    raise HTTPException(
        status_code=501,
        detail="Write queries will be implemented in Phase 8"
    )
