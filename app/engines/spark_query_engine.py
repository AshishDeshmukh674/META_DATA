"""
Spark Query Engine

Executes SQL queries against lakehouse tables using PySpark.
Supports Delta Lake, Iceberg, Hudi, and Parquet.
"""

from typing import Dict, Any, List
from pyspark.sql import SparkSession, DataFrame
import time

from app.core.logger import get_logger
from app.core.settings import settings

logger = get_logger()


class SparkQueryEngine:
    """
    Execute SQL queries against lakehouse tables using Spark.
    """
    
    def __init__(self):
        """Initialize query engine."""
        self.spark: SparkSession = None
    
    def execute_query(
        self,
        storage_type: str,
        bucket: str,
        table_path: str,
        query: str,
        table_format: str = "delta"
    ) -> Dict[str, Any]:
        """
        Execute SQL query against a table.
        
        Args:
            storage_type: "aws" or "minio"
            bucket: S3/MinIO bucket name
            table_path: Path to table within bucket
            query: SQL query to execute
            table_format: Table format (delta, iceberg, hudi, parquet)
            
        Returns:
            {
                "success": bool,
                "data": List[Dict],
                "columns": List[str],
                "row_count": int,
                "execution_time_ms": int,
                "error": Optional[str]
            }
        """
        start_time = time.time()
        
        try:
            # Create Spark session
            self._create_spark_session(storage_type)
            
            # Build table path
            if storage_type == "aws":
                full_path = f"s3a://{bucket}/{table_path}"
            else:
                full_path = f"s3a://{bucket}/{table_path}"
            
            logger.info(f"Loading table from: {full_path}")
            
            # Load table as temporary view
            if table_format == "delta":
                df = self.spark.read.format("delta").load(full_path)
            elif table_format == "parquet":
                df =self.spark.read.parquet(full_path)
            elif table_format == "iceberg":
                df = self.spark.read.format("iceberg").load(full_path)
            elif table_format == "hudi":
                df = self.spark.read.format("hudi").load(full_path)
            else:
                raise ValueError(f"Unsupported table format: {table_format}")
            
            # Register as temp view
            df.createOrReplaceTempView("query_table")
            
            # Clean up SQL query:
            # 1. Remove catalog.schema prefixes like "delta.default."
            # 2. Ensure query_table is used
            import re
            processed_query = query
            
            # Remove catalog.schema. prefixes (e.g., delta.default.table_name -> table_name)
            processed_query = re.sub(r'\b\w+\.\w+\.(\w+)\b', r'\1', processed_query)
            
            # Replace any remaining table name references with query_table
            table_name = table_path.split('/')[-1]
            processed_query = processed_query.replace(table_name, "query_table")
            
            # Ensure it uses query_table if no FROM clause
            if "FROM" in processed_query.upper() and "query_table" not in processed_query.lower():
                if "SELECT" in processed_query.upper() and "FROM" not in processed_query.upper():
                    processed_query = processed_query + " FROM query_table"
            
            logger.info(f"Original query: {query}")
            logger.info(f"Processed query: {processed_query}")
            
            # Detect query type
            query_upper = processed_query.strip().upper()
            is_write_operation = any(
                query_upper.startswith(op) 
                for op in ['UPDATE', 'INSERT', 'DELETE', 'MERGE']
            )
            
            if is_write_operation:
                # Handle write operations (UPDATE/INSERT/DELETE/MERGE)
                logger.info(f"Executing WRITE operation on Delta table")
                
                if table_format != "delta":
                    raise ValueError(f"Write operations only supported for Delta tables. Current format: {table_format}")
                
                # For Delta Lake write operations, we need to use DeltaTable API
                from delta.tables import DeltaTable
                
                if query_upper.startswith('UPDATE'):
                    # Execute UPDATE via Spark SQL on Delta
                    # Note: UPDATE on temp views requires special handling
                    # We'll execute on the actual Delta path
                    delta_table = DeltaTable.forPath(self.spark, full_path)
                    
                    # Execute the update using SQL
                    # Replace query_table with the actual path reference
                    update_query = processed_query.replace("query_table", f"delta.`{full_path}`")
                    logger.info(f"Executing Delta UPDATE: {update_query}")
                    
                    self.spark.sql(update_query)
                    
                    # Get affected rows (approximate - Delta doesn't provide exact count)
                    affected_rows = "Updated successfully"
                    
                elif query_upper.startswith('DELETE'):
                    # Execute DELETE
                    delete_query = processed_query.replace("query_table", f"delta.`{full_path}`")
                    logger.info(f"Executing Delta DELETE: {delete_query}")
                    
                    self.spark.sql(delete_query)
                    affected_rows = "Deleted successfully"
                    
                elif query_upper.startswith('INSERT'):
                    # Execute INSERT
                    insert_query = processed_query.replace("query_table", f"delta.`{full_path}`")
                    logger.info(f"Executing Delta INSERT: {insert_query}")
                    
                    self.spark.sql(insert_query)
                    affected_rows = "Inserted successfully"
                    
                elif query_upper.startswith('MERGE'):
                    # Execute MERGE
                    merge_query = processed_query.replace("query_table", f"delta.`{full_path}`")
                    logger.info(f"Executing Delta MERGE: {merge_query}")
                    
                    self.spark.sql(merge_query)
                    affected_rows = "Merged successfully"
                
                execution_time_ms = int((time.time() - start_time) * 1000)
                
                logger.info(f"Write operation completed in {execution_time_ms}ms")
                
                # Stop Spark session
                if self.spark:
                    self.spark.stop()
                    self.spark = None
                
                return {
                    "success": True,
                    "data": [],
                    "columns": ["result"],
                    "row_count": 0,
                    "execution_time_ms": execution_time_ms,
                    "message": affected_rows
                }
            
            else:
                # Handle read operations (SELECT) - existing logic
                logger.info(f"Executing SELECT query")
                result_df = self.spark.sql(processed_query)
                
                # Convert to list of dicts
                rows = result_df.collect()
                columns = result_df.columns
                
                data = []
                for row in rows:
                    row_dict = {}
                    for col in columns:
                        value = row[col]
                        # Convert to JSON-serializable types
                        if value is not None:
                            row_dict[col] = str(value) if not isinstance(value, (int, float, str, bool)) else value
                        else:
                            row_dict[col] = None
                    data.append(row_dict)
                
                execution_time_ms = int((time.time() - start_time) * 1000)
                
                logger.info(f"Query executed: {len(data)} rows in {execution_time_ms}ms")
                
                # Stop Spark session
                if self.spark:
                    self.spark.stop()
                    self.spark = None
                
                return {
                    "success": True,
                    "data": data,
                    "columns": columns,
                    "row_count": len(data),
                    "execution_time_ms": execution_time_ms
                }
            
        except Exception as e:
            logger.error(f"Query execution failed: {e}", exc_info=True)
            
            # Stop Spark session on error
            if self.spark:
                try:
                    self.spark.stop()
                except:
                    pass
                self.spark = None
            
            execution_time_ms = int((time.time() - start_time) * 1000)
            
            return {
                "success": False,
                "data": [],
                "columns": [],
                "row_count": 0,
                "execution_time_ms": execution_time_ms,
                "error": str(e)
            }
    
    def _create_spark_session(self, storage_type: str):
        """Create Spark session with appropriate configuration."""
        if self.spark:
            return
        
        builder = SparkSession.builder \
            .appName("LakehouseQueryEngine") \
            .master(settings.spark_master) \
            .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
            .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
        
        # Add Delta dependencies
        builder = builder.config(
            "spark.jars.packages",
            "io.delta:delta-spark_2.12:3.2.0,org.apache.hadoop:hadoop-aws:3.3.4"
        )
        
        # AWS S3 configuration
        if storage_type == "aws":
            builder = builder \
                .config("spark.hadoop.fs.s3a.access.key", settings.aws_access_key_id) \
                .config("spark.hadoop.fs.s3a.secret.key", settings.aws_secret_access_key) \
                .config("spark.hadoop.fs.s3a.endpoint", f"s3.{settings.aws_region}.amazonaws.com") \
                .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
                .config("spark.hadoop.fs.s3a.aws.credentials.provider", "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider")
        
        # MinIO configuration
        elif storage_type == "minio":
            builder = builder \
                .config("spark.hadoop.fs.s3a.access.key", settings.minio_access_key) \
                .config("spark.hadoop.fs.s3a.secret.key", settings.minio_secret_key) \
                .config("spark.hadoop.fs.s3a.endpoint", settings.minio_endpoint) \
                .config("spark.hadoop.fs.s3a.path.style.access", "true") \
                .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
        
        self.spark = builder.getOrCreate()
        logger.info(f"Spark session created for {storage_type}")
