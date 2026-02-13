"""
Trino Query Engine for SQL Read Operations.

Uses Trino to execute fast SQL queries on Delta Lake, Iceberg, Hudi, and Parquet tables.

Why Trino for Reads?
- Extremely fast SQL query execution (10-100x faster than Spark for reads)
- MPP (Massively Parallel Processing) architecture
- Native support for Delta Lake, Iceberg, Hudi, Parquet
- No data movement - queries data directly from S3
- ANSI SQL compliant

Architecture:
- Connects to Trino cluster in Docker
- Uses catalog-based table access (delta, hive catalogs)
- Returns query results as list of dictionaries

Usage:
    engine = TrinoQueryEngine()
    results = engine.execute_query(
        sql="SELECT * FROM delta.default.sales_delta WHERE region = 'us-east' LIMIT 100"
    )
"""

import os
from typing import Dict, Any, List, Optional
from trino.dbapi import connect
from trino.auth import BasicAuthentication

from app.core.settings import settings
from app.core.logger import get_logger

logger = get_logger()


class TrinoQueryEngine:
    """
    Trino-based SQL query engine for read operations.
    
    Executes SQL queries on lakehouse tables stored in S3.
    """
    
    def __init__(self):
        """Initialize Trino connection parameters."""
        self.host = os.getenv("TRINO_HOST", "localhost")
        self.port = int(os.getenv("TRINO_PORT", "8080"))
        self.user = os.getenv("TRINO_USER", "admin")
        
        logger.info(
            f"Trino query engine initialized",
            extra={"host": self.host, "port": self.port, "user": self.user}
        )
    
    def _create_connection(self):
        """
        Create Trino connection.
        
        Returns:
            Trino connection object
            
        Connection settings:
        - No authentication in development (can add BasicAuth for production)
        - Uses 'default' catalog by default
        - HTTP protocol (HTTPS for production)
        """
        try:
            logger.info(f"Connecting to Trino at {self.host}:{self.port}")
            
            connection = connect(
                host=self.host,
                port=self.port,
                user=self.user,
                catalog='delta',  # Default catalog (can be overridden in SQL)
                schema='default',
                http_scheme='http',  # Use 'https' for production
                # auth=BasicAuthentication("username", "password")  # Add for production
            )
            
            logger.info("Trino connection established successfully")
            return connection
            
        except Exception as e:
            logger.error(f"Failed to connect to Trino: {e}", exc_info=True)
            raise
    
    def execute_query(
        self,
        sql: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute SQL query and return results.
        
        Args:
            sql: SQL query string (can use ? placeholders for parameters)
            parameters: Optional dict of parameters for parameterized queries
            
        Returns:
            {
                "success": True,
                "row_count": 100,
                "columns": ["id", "name", "price"],
                "data": [
                    {"id": 1, "name": "Product A", "price": 19.99},
                    {"id": 2, "name": "Product B", "price": 29.99}
                ],
                "execution_time_ms": 234
            }
            
        Example Queries:
            # Query Delta Lake table
            SELECT * FROM delta.default.sales_delta 
            WHERE region = 'us-east' 
            LIMIT 100
            
            # Query Parquet files directly
            SELECT * FROM hive.default."s3://bucket/path/to/parquet/"
            
            # Join multiple tables
            SELECT s.*, c.customer_name 
            FROM delta.default.sales s
            JOIN delta.default.customers c ON s.customer_id = c.id
            WHERE s.date >= DATE '2024-01-01'
        """
        import time
        start_time = time.time()
        
        connection = None
        cursor = None
        
        try:
            logger.info(f"Executing SQL query", extra={"sql": sql[:200]})
            
            # Create connection
            connection = self._create_connection()
            cursor = connection.cursor()
            
            # Execute query
            if parameters:
                cursor.execute(sql, parameters)
            else:
                cursor.execute(sql)
            
            # Fetch results
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            rows = cursor.fetchall()
            
            # Convert rows to list of dictionaries
            data = []
            for row in rows:
                data.append(dict(zip(columns, row)))
            
            execution_time_ms = int((time.time() - start_time) * 1000)
            
            result = {
                "success": True,
                "row_count": len(data),
                "columns": columns,
                "data": data,
                "execution_time_ms": execution_time_ms
            }
            
            logger.info(
                f"Query executed successfully",
                extra={
                    "row_count": len(data),
                    "execution_time_ms": execution_time_ms
                }
            )
            
            return result
            
        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            logger.error(
                f"Query execution failed: {e}",
                extra={"sql": sql[:200], "execution_time_ms": execution_time_ms},
                exc_info=True
            )
            raise
        
        finally:
            # Always close cursor and connection
            if cursor:
                cursor.close()
            if connection:
                connection.close()
                logger.info("Trino connection closed")
    
    def execute_query_with_catalog(
        self,
        catalog: str,
        schema: str,
        table: str,
        sql_filter: Optional[str] = None,
        limit: int = 1000
    ) -> Dict[str, Any]:
        """
        Execute query with explicit catalog/schema/table.
        
        Args:
            catalog: Trino catalog name ('delta', 'hive', etc.)
            schema: Schema name (usually 'default' or database name)
            table: Table name or S3 path for external tables
            sql_filter: Optional WHERE clause (without 'WHERE' keyword)
            limit: Maximum rows to return (default 1000)
            
        Returns:
            Same as execute_query()
            
        Example:
            engine.execute_query_with_catalog(
                catalog='delta',
                schema='default',
                table='sales_delta',
                sql_filter="region = 'us-east' AND date >= '2024-01-01'",
                limit=500
            )
        """
        # Build SQL query
        sql = f"SELECT * FROM {catalog}.{schema}.{table}"
        
        if sql_filter:
            sql += f" WHERE {sql_filter}"
        
        sql += f" LIMIT {limit}"
        
        logger.info(
            f"Executing catalog query",
            extra={
                "catalog": catalog,
                "schema": schema,
                "table": table,
                "filter": sql_filter,
                "limit": limit
            }
        )
        
        return self.execute_query(sql)
    
    def get_table_info(self, catalog: str, schema: str, table: str) -> Dict[str, Any]:
        """
        Get table metadata (schema, column info).
        
        Args:
            catalog: Catalog name
            schema: Schema name
            table: Table name
            
        Returns:
            {
                "success": True,
                "catalog": "delta",
                "schema": "default",
                "table": "sales_delta",
                "columns": [
                    {"name": "id", "type": "integer", "nullable": True},
                    {"name": "name", "type": "varchar", "nullable": True}
                ]
            }
        """
        try:
            sql = f"DESCRIBE {catalog}.{schema}.{table}"
            result = self.execute_query(sql)
            
            # Transform DESCRIBE output to schema format
            columns = []
            for row in result['data']:
                columns.append({
                    "name": row.get('Column', row.get('column')),
                    "type": row.get('Type', row.get('type')),
                    "nullable": True,  # Trino doesn't provide nullability in DESCRIBE
                    "comment": row.get('Comment', row.get('comment', ''))
                })
            
            return {
                "success": True,
                "catalog": catalog,
                "schema": schema,
                "table": table,
                "columns": columns
            }
            
        except Exception as e:
            logger.error(f"Failed to get table info: {e}", exc_info=True)
            raise
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test Trino connection and return cluster info.
        
        Returns:
            {
                "success": True,
                "message": "Connected to Trino successfully",
                "version": "435",
                "catalogs": ["delta", "hive", "system"]
            }
        """
        try:
            logger.info("Testing Trino connection")
            
            # Test basic query
            result = self.execute_query("SELECT 1 AS test")
            
            # Get Trino version
            version_result = self.execute_query("SELECT version()")
            version = version_result['data'][0].get('_col0', 'unknown') if version_result['data'] else 'unknown'
            
            # Get available catalogs
            catalogs_result = self.execute_query("SHOW CATALOGS")
            catalogs = [row['Catalog'] for row in catalogs_result['data']]
            
            return {
                "success": True,
                "message": "Connected to Trino successfully",
                "version": version,
                "catalogs": catalogs,
                "host": self.host,
                "port": self.port
            }
            
        except Exception as e:
            logger.error(f"Trino connection test failed: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"Failed to connect to Trino: {str(e)}",
                "host": self.host,
                "port": self.port
            }
