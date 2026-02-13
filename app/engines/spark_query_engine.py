"""
Spark Query Engine for SQL Operations on Delta Tables.

Uses Apache Spark to execute SQL queries, especially for Delta Lake time travel.

Why Spark for Write & Time Travel?
- Native Delta Lake support
- ACID transactions
- Time travel (VERSION AS OF, TIMESTAMP AS OF)
- Production-ready

Usage:
    engine = SparkQueryEngine()
    results = engine.execute_query(
        storage_type="aws",
        bucket="bucket",
        table_path="tables/sales_delta",
        sql="SELECT * FROM {table} WHERE region = 'us-east'",
        version=5  # Optional: query specific version
    )
"""

import os
from typing import Dict, Any, List, Optional
from pyspark.sql import SparkSession

from app.core.settings import settings
from app.core.logger import get_logger

logger = get_logger()


class SparkQueryEngine:
    """
    Spark-based SQL query engine for Delta Lake operations.
    
    Supports time travel queries and write operations.
    """
    
    def __init__(self):
        """Initialize without creating SparkSession (per-request pattern)."""
        self.spark = None
        logger.info("Spark query engine initialized")
    
    def _create_spark_session(self, storage_type: str) -> SparkSession:
        """Create SparkSession with S3 configuration."""
        try:
            logger.info(f"Creating Spark session for storage_type={storage_type}")
            
            # Stop any existing session
            try:
                existing_spark = SparkSession.getActiveSession()
                if existing_spark:
                    logger.warning("Found existing Spark session, stopping it first")
                    existing_spark.stop()
            except:
                pass
            
            # Build Spark session
            spark_master = os.getenv("SPARK_MASTER_URL", "spark://spark-master:7077")
            logger.info(f"Connecting to Spark master at {spark_master}")
            
            builder = SparkSession.builder \
                .appName("LakehouseQueryEngine") \
                .master(spark_master) \
                .config("spark.jars.packages", "io.delta:delta-spark_2.12:3.2.0,org.apache.hadoop:hadoop-aws:3.3.4") \
                .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
                .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
                .config("spark.network.timeout", "600s") \
                .config("spark.executor.heartbeatInterval", "60s")
            
            # S3 Configuration
            if storage_type == "aws":
                builder = builder \
                    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
                    .config("spark.hadoop.fs.s3a.access.key", settings.aws_access_key_id) \
                    .config("spark.hadoop.fs.s3a.secret.key", settings.aws_secret_access_key) \
                    .config("spark.hadoop.fs.s3a.endpoint", f"s3.{settings.aws_region}.amazonaws.com") \
                    .config("spark.hadoop.fs.s3a.aws.credentials.provider", "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider")
                logger.info(f"Configured Spark for AWS S3 in region {settings.aws_region}")
            
            # Create session
            spark = builder.getOrCreate()
            spark.sparkContext.setLogLevel("WARN")
            logger.info("Spark session created successfully")
            return spark
            
        except Exception as e:
            logger.error(f"Failed to create Spark session: {e}", exc_info=True)
            raise
    
    def execute_query(
        self,
        storage_type: str,
        bucket: str,
        table_path: str,
        sql: str,
        version: Optional[int] = None,
        timestamp: Optional[str] = None,
        limit: int = 1000
    ) -> Dict[str, Any]:
        """
        Execute SQL query on Delta table.
        
        Args:
            storage_type: "aws" or "minio"
            bucket: S3 bucket name
            table_path: Path to table within bucket
            sql: SQL query (use {table} placeholder for table reference)
            version: Optional Delta version for time travel
            timestamp: Optional timestamp for time travel (e.g., "2024-01-01 00:00:00")
            limit: Maximum rows to return
            
        Returns:
            {
                "success": True,
                "row_count": 100,
                "columns": ["id", "name"],
                "data": [{...}, {...}],
                "execution_time_ms": 456
            }
        """
        import time
        start_time = time.time()
        
        try:
            # Build S3 path
            s3_path = f"s3a://{bucket}/{table_path}"
            logger.info(f"Executing query on {s3_path}")
            
            # Create Spark session
            self.spark = self._create_spark_session(storage_type)
            
            # Build table reference with time travel if specified
            if version is not None:
                table_ref = f"delta.`{s3_path}@v{version}`"
                logger.info(f"Using time travel: version {version}")
            elif timestamp:
                table_ref = f"delta.`{s3_path}@{timestamp}`"
                logger.info(f"Using time travel: timestamp {timestamp}")
            else:
                table_ref = f"delta.`{s3_path}`"
            
            # Replace {table} placeholder in SQL
            final_sql = sql.replace("{table}", table_ref)
            
            # Add LIMIT if not present and SQL is a SELECT
            if "LIMIT" not in final_sql.upper() and final_sql.strip().upper().startswith("SELECT"):
                final_sql += f" LIMIT {limit}"
            
            logger.info(f"Executing SQL: {final_sql[:200]}")
            
            # Execute query
            df = self.spark.sql(final_sql)
            
            # Collect results
            rows = df.collect()
            columns = df.columns
            
            # Convert to list of dicts
            data = []
            for row in rows:
                data.append(row.asDict())
            
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
                extra={"row_count": len(data), "execution_time_ms": execution_time_ms}
            )
            
            return result
            
        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            logger.error(f"Query execution failed: {e}", exc_info=True)
            raise
        
        finally:
            # Always cleanup Spark session
            if self.spark:
                logger.info("Stopping Spark session")
                self.spark.stop()
                self.spark = None
