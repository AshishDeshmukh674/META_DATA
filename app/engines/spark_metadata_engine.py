"""
Spark Metadata Engine for Lakehouse Tables.

Uses Apache Spark to extract metadata from Delta, Iceberg, Hudi, and Parquet tables.

Why Spark?
- Delta Lake: Native Spark integration
- Iceberg: Official Spark support
- Hudi: Spark is the primary engine
- Production-ready: Battle-tested by thousands of companies

Architecture:
- Per-request SparkSession (safer, no memory leaks)
- S3 configuration from settings
- Comprehensive error handling

Usage:
    engine = SparkMetadataEngine()
    metadata = engine.extract_metadata(
        storage_type="aws",
        bucket="metadataproject",
        path="tables/sales_delta",
        table_format="delta"
    )
"""

import os
import json
import uuid
import time
from datetime import datetime

# No need for JAVA_HOME/HADOOP_HOME - Spark runs in Docker now!
from typing import Dict, Any, Optional
from pyspark.sql import SparkSession

from app.core.settings import settings
from app.core.logger import get_logger

logger = get_logger()


class SparkMetadataEngine:
    """
    Spark-based metadata extraction engine.
    
    Extracts schema, partitions, files, and version info from lakehouse tables.
    """
    
    def __init__(self):
        """Initialize without creating SparkSession (per-request pattern)."""
        self.spark = None
        logger.info("Spark metadata engine initialized (per-request mode)")
    
    def _create_spark_session(self, storage_type: str) -> SparkSession:
        """
        Create SparkSession with S3 configuration.
        
        Args:
            storage_type: "aws" or "minio"
            
        Returns:
            Configured SparkSession
            
        Why per-request?
        - No memory leaks from long-running sessions
        - Clean state for each request
        - Easier to debug issues
        - Auto-cleanup when done
        """
        try:
            logger.info(f"Creating Spark session for storage_type={storage_type}")
            
            # CRITICAL: Stop any existing Spark session first
            try:
                existing_spark = SparkSession.getActiveSession()
                if existing_spark:
                    logger.warning("Found existing Spark session, stopping it first")
                    existing_spark.stop()
            except:
                pass  # No existing session
            
            # Build Spark session with Delta Lake packages
            # Connect to Spark cluster (uses environment variable or defaults to Docker network)
            spark_master = os.getenv("SPARK_MASTER_URL", "spark://spark-master:7077")
            logger.info(f"Connecting to Spark master at {spark_master}")
            
            builder = SparkSession.builder \
                .appName("LakehouseMetadataExtractor") \
                .master(spark_master) \
                .config("spark.jars.packages", "io.delta:delta-spark_2.12:3.2.0,org.apache.hadoop:hadoop-aws:3.3.4") \
                .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
                .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
                .config("spark.network.timeout", "600s") \
                .config("spark.executor.heartbeatInterval", "60s") \
                .config("spark.rpc.askTimeout", "600s") \
                .config("spark.rpc.lookupTimeout", "600s")
            
            # S3 Configuration based on storage type
            if storage_type == "aws":
                # AWS S3 configuration - simplified since Spark runs in properly configured Docker
                builder = builder \
                    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
                    .config("spark.hadoop.fs.s3a.access.key", settings.aws_access_key_id) \
                    .config("spark.hadoop.fs.s3a.secret.key", settings.aws_secret_access_key) \
                    .config("spark.hadoop.fs.s3a.endpoint", f"s3.{settings.aws_region}.amazonaws.com") \
                    .config("spark.hadoop.fs.s3a.aws.credentials.provider", "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider")
                logger.info(f"Configured Spark for AWS S3 in region {settings.aws_region}")
            
            elif storage_type == "minio":
                # MinIO configuration (S3-compatible) - for Phase 7
                builder = builder \
                    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
                    .config("spark.hadoop.fs.s3a.access.key", settings.minio_access_key) \
                    .config("spark.hadoop.fs.s3a.secret.key", settings.minio_secret_key) \
                    .config("spark.hadoop.fs.s3a.endpoint", settings.minio_endpoint) \
                    .config("spark.hadoop.fs.s3a.path.style.access", "true") \
                    .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false")
                logger.info(f"Configured Spark for MinIO at {settings.minio_endpoint}")
            
            # Create Spark session with retry logic to handle transient gateway errors
            max_retries = 3
            retry_delay = 2  # seconds
            last_error = None
            
            for attempt in range(1, max_retries + 1):
                try:
                    logger.info(f"Creating Spark session (attempt {attempt}/{max_retries})")
                    spark = builder.getOrCreate()
                    spark.sparkContext.setLogLevel("WARN")  # Reduce Spark logging noise
                    logger.info("Spark session created successfully (connected to Docker cluster)")
                    return spark
                except Exception as session_error:
                    last_error = session_error
                    error_msg = str(session_error)
                    
                    # Check if it's a gateway error that might be transient
                    if "JAVA_GATEWAY_EXITED" in error_msg or "gateway" in error_msg.lower():
                        if attempt < max_retries:
                            logger.warning(
                                f"Gateway error on attempt {attempt}, retrying in {retry_delay}s: {error_msg}"
                            )
                            time.sleep(retry_delay)
                            continue
                        else:
                            logger.error(f"Failed to create Spark session after {max_retries} attempts")
                            raise
                    else:
                        # Non-gateway error, don't retry
                        raise
            
            # If we get here, all retries failed
            raise last_error if last_error else Exception("Failed to create Spark session")
            
        except Exception as e:
            logger.error(f"Failed to create Spark session: {e}", exc_info=True)
            raise
    
    def _generate_snapshot_id(self) -> str:
        """
        Generate unique snapshot ID.
        
        Format: snapshot_YYYYMMDD_HHMMSS_<uuid4-8chars>
        Example: snapshot_20260207_173045_a1b2c3d4
        
        Why this format?
        - Sortable by timestamp
        - Unique (UUID suffix prevents collisions)
        - Human-readable (can see when it was created)
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        snapshot_id = f"snapshot_{timestamp}_{unique_id}"
        logger.info(f"Generated snapshot_id: {snapshot_id}")
        return snapshot_id
    
    def extract_metadata(
        self,
        storage_type: str,
        bucket: str,
        path: str,
        table_format: str
    ) -> Dict[str, Any]:
        """
        Extract metadata from lakehouse table using Spark.
        
        Args:
            storage_type: "aws" or "minio"
            bucket: S3/MinIO bucket name
            path: Path to table within bucket
            table_format: "delta", "iceberg", "hudi", or "parquet"
            
        Returns:
            Dictionary with extracted metadata:
            {
                "snapshot_id": "snapshot_20260207_173045_a1b2c3d4",
                "table_path": "s3a://bucket/path",
                "table_format": "delta",
                "generated_at": "2026-02-07T17:30:45Z",
                "schema": {...},
                "partitions": {...},
                "files": {...},
                "version_info": {...}
            }
            
        Process:
        1. Create Spark session
        2. Load table using format-specific reader
        3. Extract schema (columns, types)
        4. Extract partition info
        5. Extract file statistics
        6. Extract version info (format-specific)
        7. Generate snapshot ID
        8. Clean up Spark session
        """
        snapshot_id = self._generate_snapshot_id()
        
        try:
            # Build S3 path
            s3_path = f"s3a://{bucket}/{path}"
            logger.info(
                f"Starting metadata extraction",
                extra={
                    "snapshot_id": snapshot_id,
                    "storage_type": storage_type,
                    "table_path": s3_path,
                    "table_format": table_format
                }
            )
            
            # Create Spark session
            self.spark = self._create_spark_session(storage_type)
            
            # Load table based on format
            if table_format == "delta":
                df = self.spark.read.format("delta").load(s3_path)
                version_info = self._get_delta_version_info(s3_path)
            
            elif table_format == "iceberg":
                df = self.spark.read.format("iceberg").load(s3_path)
                version_info = self._get_iceberg_version_info(s3_path)
            
            elif table_format == "hudi":
                df = self.spark.read.format("hudi").load(s3_path)
                version_info = self._get_hudi_version_info(s3_path)
            
            elif table_format == "parquet":
                df = self.spark.read.parquet(s3_path)
                version_info = {"format": "parquet", "note": "No versioning for Parquet"}
            
            else:
                raise ValueError(f"Unsupported table format: {table_format}")
            
            # Extract schema
            schema_json = json.loads(df.schema.json())
            logger.info(f"Extracted schema with {len(schema_json['fields'])} columns")
            
            # Extract partition information
            partition_info = self._get_partition_info(df)
            
            # Extract file statistics
            file_stats = self._get_file_statistics(s3_path, table_format)
            
            # Build metadata dictionary
            metadata = {
                "snapshot_id": snapshot_id,
                "table_path": s3_path,
                "table_format": table_format,
                "generated_at": datetime.utcnow().isoformat() + "Z",
                "schema": schema_json,
                "partitions": partition_info,
                "files": file_stats,
                "version_info": version_info
            }
            
            logger.info(
                f"Metadata extraction completed successfully",
                extra={
                    "snapshot_id": snapshot_id,
                    "column_count": len(schema_json['fields']),
                    "file_count": file_stats.get('file_count', 0)
                }
            )
            
            return metadata
            
        except Exception as e:
            logger.error(
                f"Metadata extraction failed: {e}",
                extra={"snapshot_id": snapshot_id},
                exc_info=True
            )
            raise
        
        finally:
            # Always cleanup Spark session (per-request pattern)
            if self.spark:
                logger.info("Stopping Spark session")
                self.spark.stop()
                self.spark = None
    
    def convert_to_lakehouse(
        self,
        storage_type: str,
        bucket: str,
        source_path: str,
        source_format: str,
        target_format: str,
        target_path: Optional[str] = None,
        partition_columns: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Convert raw data files (CSV/JSON/Parquet) to lakehouse format (Delta/Iceberg/Hudi).
        
        Args:
            storage_type: "aws" or "minio"
            bucket: S3/MinIO bucket name
            source_path: Path to source data file(s)
            source_format: "csv", "json", "parquet", "avro", "orc"
            target_format: "delta", "iceberg", or "hudi"
            target_path: Output path (defaults to source_path with format suffix if file)
            partition_columns: List of columns to partition by
            
        Returns:
            {
                "success": True,
                "source_path": "s3a://bucket/data.csv",
                "target_path": "s3a://bucket/data_delta/",
                "target_format": "delta",
                "row_count": 1000,
                "partition_columns": ["year", "month"]
            }
            
        Example:
            CSV to Delta:
            engine.convert_to_lakehouse(
                storage_type="aws",
                bucket="mybucket",
                source_path="raw/customer_data.csv",
                source_format="csv",
                target_format="delta",
                target_path="tables/customer_data_delta"
            )
        """
        try:
            # Build S3 paths
            s3_source = f"s3a://{bucket}/{source_path}"
            
            # Auto-generate target path if not provided
            if target_path is None:
                # If source is a file (ends with extension), create folder with format suffix
                if '.' in source_path.split('/')[-1]:
                    base_path = source_path.rsplit('.', 1)[0]
                    target_path = f"{base_path}_{target_format}"
                else:
                    target_path = f"{source_path}_{target_format}"
            
            s3_target = f"s3a://{bucket}/{target_path}"
            
            logger.info(
                f"Starting lakehouse conversion",
                extra={
                    "source": s3_source,
                    "target": s3_target,
                    "source_format": source_format,
                    "target_format": target_format,
                    "partitions": partition_columns
                }
            )
            
            # Create Spark session
            self.spark = self._create_spark_session(storage_type)
            
            # Read source data
            logger.info(f"Reading source data from {s3_source}")
            
            if source_format == "csv":
                df = self.spark.read \
                    .option("header", "true") \
                    .option("inferSchema", "true") \
                    .csv(s3_source)
            elif source_format == "json":
                df = self.spark.read.json(s3_source)
            elif source_format == "parquet":
                df = self.spark.read.parquet(s3_source)
            elif source_format == "avro":
                df = self.spark.read.format("avro").load(s3_source)
            elif source_format == "orc":
                df = self.spark.read.orc(s3_source)
            else:
                raise ValueError(f"Unsupported source format: {source_format}")
            
            row_count = df.count()
            logger.info(f"Source data loaded: {row_count} rows")
            
            # Write to target format
            logger.info(f"Writing to {target_format} format at {s3_target}")
            
            writer = df.write.mode("overwrite")
            
            # Add partitioning if specified
            if partition_columns:
                logger.info(f"Partitioning by: {partition_columns}")
                writer = writer.partitionBy(*partition_columns)
            
            # Write based on target format
            if target_format == "delta":
                writer.format("delta").save(s3_target)
                logger.info(f"Delta table created successfully")
                
            elif target_format == "iceberg":
                # Iceberg requires catalog configuration
                # For simplicity, using Hadoop catalog with path-based tables
                writer.format("iceberg").save(s3_target)
                logger.info(f"Iceberg table created successfully")
                
            elif target_format == "hudi":
                # Hudi requires additional configurations
                writer.format("hudi") \
                    .option("hoodie.table.name", target_path.split('/')[-1]) \
                    .option("hoodie.datasource.write.recordkey.field", "id") \
                    .option("hoodie.datasource.write.precombine.field", "id") \
                    .save(s3_target)
                logger.info(f"Hudi table created successfully")
            else:
                raise ValueError(f"Unsupported target format: {target_format}")
            
            result = {
                "success": True,
                "source_path": s3_source,
                "target_path": s3_target,
                "target_format": target_format,
                "row_count": row_count,
                "partition_columns": partition_columns or []
            }
            
            logger.info(
                f"Lakehouse conversion completed successfully",
                extra=result
            )
            
            return result
            
        except Exception as e:
            logger.error(
                f"Lakehouse conversion failed: {e}",
                exc_info=True
            )
            raise
        
        finally:
            # Always cleanup Spark session
            if self.spark:
                logger.info("Stopping Spark session")
                self.spark.stop()
                self.spark = None
    
    def _get_partition_info(self, df) -> Dict[str, Any]:
        """
        Extract partition information from DataFrame.
        
        Returns:
            {
                "is_partitioned": bool,
                "partition_columns": list,
                "partition_count": int (if partitioned)
            }
        """
        try:
            # Check if table is partitioned
            # In Spark, partition columns are stored in the table metadata
            # For now, we'll check if there are any partition-like columns
            # (This is simplified - in production you'd query the table's metadata)
            
            # Try to get partition columns from the catalog
            # Since we're reading directly without a catalog, we'll infer from schema
            partition_columns = []
            
            # Note: This is a simplified approach
            # In production, you'd use: spark.sql(f"DESCRIBE EXTENDED {table}").collect()
            # to get actual partition columns
            
            return {
                "is_partitioned": len(partition_columns) > 0,
                "partition_columns": partition_columns,
                "partition_count": 0  # Would need catalog query for accurate count
            }
        except Exception as e:
            logger.warning(f"Could not extract partition info: {e}")
            return {
                "is_partitioned": False,
                "partition_columns": [],
                "partition_count": 0
            }
    
    def _get_file_statistics(self, table_path: str, format: str) -> Dict[str, Any]:
        """
        Get file statistics for the table.
        
        Returns:
            {
                "file_count": int,
                "total_size_bytes": int,
                "sample_files": list (first 10 files)
            }
        """
        try:
            # Use Spark to list files
            # This gives us access to file sizes and paths
            hadoop_conf = self.spark.sparkContext._jsc.hadoopConfiguration()
            fs = self.spark._jvm.org.apache.hadoop.fs.FileSystem.get(
                self.spark._jvm.java.net.URI(table_path),
                hadoop_conf
            )
            
            path = self.spark._jvm.org.apache.hadoop.fs.Path(table_path)
            
            # List all files recursively
            files = []
            total_size = 0
            
            file_iterator = fs.listFiles(path, True)  # recursive=True
            while file_iterator.hasNext():
                file_status = file_iterator.next()
                file_path = str(file_status.getPath())
                file_size = file_status.getLen()
                
                # Skip metadata directories
                if not any(x in file_path for x in ['_delta_log', '_SUCCESS', '.hoodie', 'metadata']):
                    if file_path.endswith('.parquet'):
                        files.append({
                            "path": file_path.split(table_path)[-1].lstrip('/'),
                            "size": file_size
                        })
                        total_size += file_size
            
            logger.info(f"Found {len(files)} data files, total size: {total_size} bytes")
            
            return {
                "file_count": len(files),
                "total_size_bytes": total_size,
                "sample_files": files[:10]  # First 10 files as sample
            }
            
        except Exception as e:
            logger.warning(f"Could not get file statistics: {e}")
            return {
                "file_count": 0,
                "total_size_bytes": 0,
                "sample_files": []
            }
    
    def _get_delta_version_info(self, table_path: str) -> Dict[str, Any]:
        """Get Delta Lake version information."""
        try:
            from delta.tables import DeltaTable
            delta_table = DeltaTable.forPath(self.spark, table_path)
            history = delta_table.history(1).collect()  # Get latest version
            
            if history:
                latest = history[0]
                return {
                    "format": "delta",
                    "version": latest["version"],
                    "timestamp": str(latest["timestamp"]),
                    "operation": latest.get("operation", "UNKNOWN")
                }
        except Exception as e:
            logger.warning(f"Could not get Delta version info: {e}")
        
        return {"format": "delta", "version": "unknown"}
    
    def _get_iceberg_version_info(self, table_path: str) -> Dict[str, Any]:
        """Get Iceberg snapshot information."""
        try:
            # Iceberg snapshot info would come from querying metadata tables
            # This is format-specific and complex
            return {
                "format": "iceberg",
                "snapshot_id": "not_implemented",
                "note": "Iceberg snapshot tracking requires catalog integration"
            }
        except Exception as e:
            logger.warning(f"Could not get Iceberg version info: {e}")
        
        return {"format": "iceberg", "snapshot_id": "unknown"}
    
    def _get_hudi_version_info(self, table_path: str) -> Dict[str, Any]:
        """Get Hudi commit information."""
        try:
            # Hudi commit info from timeline
            return {
                "format": "hudi",
                "commit_time": "not_implemented",
                "note": "Hudi commit tracking requires timeline parsing"
            }
        except Exception as e:
            logger.warning(f"Could not get Hudi version info: {e}")
        
        return {"format": "hudi", "commit_time": "unknown"}
