"""
Parquet Metadata Reader

Reads schema and statistics directly from Parquet files using PyArrow.
For plain Parquet tables (no Delta/Iceberg/Hudi), reads metadata directly from .parquet files.

References:
- PyArrow Parquet: https://arrow.apache.org/docs/python/parquet.html
"""

import io
from typing import Dict, List, Optional, Any
from datetime import datetime
import boto3
from botocore.exceptions import ClientError

try:
    import pyarrow.parquet as pq
    PYARROW_AVAILABLE = True
except ImportError:
    PYARROW_AVAILABLE = False

from app.core.logger import get_logger
from app.core.settings import settings

logger = get_logger()


class ParquetReader:
    """Read plain Parquet table metadata."""
    
    def __init__(self, bucket: str, path: str, storage_type: str = "aws"):
        """
        Initialize Parquet reader.
        
        Args:
            bucket: S3/MinIO bucket name
            path: Path to Parquet files
            storage_type: "aws" or "minio"
        """
        if not PYARROW_AVAILABLE:
            raise ImportError("PyArrow is required for Parquet reading. Install with: pip install pyarrow")
        
        self.bucket = bucket
        self.path = path.rstrip('/')
        self.storage_type = storage_type
        
        # Initialize S3 client
        if storage_type == "minio":
            self.s3_client = boto3.client(
                's3',
                endpoint_url=settings.minio_endpoint,
                aws_access_key_id=settings.minio_access_key,
                aws_secret_access_key=settings.minio_secret_key
            )
        else:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
                region_name=settings.aws_region
            )
        
        logger.info(f"Initialized ParquetReader for {bucket}/{path}")
    
    def _list_parquet_files(self) -> List[Dict[str, Any]]:
        """List all .parquet files in the path."""
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket,
                Prefix=f"{self.path}/",
                MaxKeys=1000
            )
            
            files = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    key = obj['Key']
                    if key.endswith('.parquet'):
                        files.append({
                            'key': key,
                            'size': obj['Size'],
                            'last_modified': obj['LastModified'].isoformat()
                        })
            
            return files
            
        except ClientError as e:
            logger.error(f"Error listing Parquet files: {e}")
            return []
    
    def _read_parquet_metadata(self, key: str) -> Optional[Any]:
        """Read Parquet file metadata using PyArrow."""
        try:
            response = self.s3_client.get_object(Bucket=self.bucket, Key=key)
            parquet_data = response['Body'].read()
            
            # Read metadata using PyArrow
            parquet_file = pq.ParquetFile(io.BytesIO(parquet_data))
            return parquet_file.metadata
            
        except ClientError as e:
            logger.error(f"Error reading Parquet file {key}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error parsing Parquet metadata from {key}: {e}")
            return None
    
    def _read_parquet_schema(self, key: str) -> Optional[Any]:
        """Read Parquet file schema using PyArrow."""
        try:
            response = self.s3_client.get_object(Bucket=self.bucket, Key=key)
            parquet_data = response['Body'].read()
            
            # Read schema using PyArrow
            parquet_file = pq.ParquetFile(io.BytesIO(parquet_data))
            return parquet_file.schema_arrow
            
        except ClientError as e:
            logger.error(f"Error reading Parquet file {key}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error parsing Parquet schema from {key}: {e}")
            return None
    
    def get_schema(self) -> Dict[str, Any]:
        """
        Extract schema from a Parquet file.
        
        Reads the first Parquet file to get schema.
        """
        logger.info(f"Reading schema for Parquet files in {self.bucket}/{self.path}")
        
        files = self._list_parquet_files()
        if not files:
            return {
                "success": False,
                "error": "No Parquet files found",
                "table_format": "parquet"
            }
        
        # Read schema from first file
        first_file = files[0]
        schema = self._read_parquet_schema(first_file['key'])
        
        if not schema:
            return {
                "success": False,
                "error": "Could not read Parquet schema",
                "table_format": "parquet"
            }
        
        # Convert PyArrow schema to dict
        fields = []
        for i in range(len(schema)):
            field = schema.field(i)
            fields.append({
                "name": field.name,
                "type": str(field.type),
                "nullable": field.nullable,
                "metadata": dict(field.metadata) if field.metadata else {}
            })
        
        return {
            "success": True,
            "table_format": "parquet",
            "schema": {
                "fields": fields,
                "metadata": dict(schema.metadata) if schema.metadata else {}
            },
            "file_count": len(files),
            "sample_file": first_file['key']
        }
    
    def get_snapshots(self) -> Dict[str, Any]:
        """
        Get file history (no real snapshots for plain Parquet).
        
        Plain Parquet doesn't have snapshots - just list files by modification time.
        """
        logger.info(f"Reading file history for Parquet files in {self.bucket}/{self.path}")
        
        files = self._list_parquet_files()
        
        # Sort by last modified
        files.sort(key=lambda x: x['last_modified'])
        
        return {
            "success": True,
            "table_format": "parquet",
            "file_count": len(files),
            "files_by_date": files,
            "note": "Plain Parquet tables don't have snapshots - this shows files by modification time"
        }
    
    def get_partitions(self) -> Dict[str, Any]:
        """
        Detect partitions from directory structure.
        
        Hive-style partitioning: column=value/
        """
        logger.info(f"Detecting partitions for Parquet files in {self.bucket}/{self.path}")
        
        files = self._list_parquet_files()
        if not files:
            return {
                "success": False,
                "error": "No Parquet files found",
                "table_format": "parquet"
            }
        
        # Check for Hive-style partitioning (column=value)
        partition_keys = set()
        for file in files:
            path_parts = file['key'].split('/')
            for part in path_parts:
                if '=' in part:
                    # Hive partition: year=2023, month=01, etc.
                    partition_keys.add(part.split('=')[0])
        
        is_partitioned = len(partition_keys) > 0
        
        return {
            "success": True,
            "table_format": "parquet",
            "is_partitioned": is_partitioned,
            "partition_columns": list(partition_keys),
            "note": "Detected from Hive-style directory structure (column=value)"
        }
    
    def get_files(self) -> Dict[str, Any]:
        """
        Get list of all Parquet files with metadata.
        """
        logger.info(f"Reading files for Parquet table in {self.bucket}/{self.path}")
        
        files = self._list_parquet_files()
        
        # Read metadata from each file (limited to first 10 for performance)
        files_with_metadata = []
        total_size = 0
        total_rows = 0
        
        for i, file in enumerate(files):
            file_info = {
                "path": file['key'],
                "size": file['size'],
                "last_modified": file['last_modified']
            }
            
            # Read metadata for first 10 files only
            if i < 10:
                metadata = self._read_parquet_metadata(file['key'])
                if metadata:
                    file_info['num_rows'] = metadata.num_rows
                    file_info['num_row_groups'] = metadata.num_row_groups
                    total_rows += metadata.num_rows
            
            files_with_metadata.append(file_info)
            total_size += file['size']
        
        return {
            "success": True,
            "table_format": "parquet",
            "file_count": len(files_with_metadata),
            "total_size_bytes": total_size,
            "total_rows": total_rows,
            "files": files_with_metadata,
            "note": "Detailed metadata available for first 10 files only"
        }
