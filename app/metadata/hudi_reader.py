"""
Apache Hudi Metadata Reader

Reads metadata from Hudi tables stored in .hoodie/ directory.
Hudi uses timeline for tracking commits and maintains metadata in .hoodie/

References:
- Hudi Documentation: https://hudi.apache.org/docs/overview
"""

import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import boto3
from botocore.exceptions import ClientError

from app.core.logger import get_logger
from app.core.settings import settings

logger = get_logger()


class HudiReader:
    """Read Apache Hudi table metadata."""
    
    def __init__(self, bucket: str, path: str, storage_type: str = "aws"):
        """
        Initialize Hudi reader.
        
        Args:
            bucket: S3/MinIO bucket name
            path: Path to Hudi table (contains .hoodie/)
            storage_type: "aws" or "minio"
        """
        self.bucket = bucket
        self.path = path.rstrip('/')
        self.hoodie_path = f"{self.path}/.hoodie"
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
        
        logger.info(f"Initialized HudiReader for {bucket}/{path}")
    
    def _list_hoodie_files(self) -> List[Dict[str, Any]]:
        """List all files in .hoodie directory."""
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket,
                Prefix=f"{self.hoodie_path}/",
                MaxKeys=1000
            )
            
            files = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    files.append({
                        'key': obj['Key'],
                        'size': obj['Size'],
                        'last_modified': obj['LastModified'].isoformat()
                    })
            
            return files
            
        except ClientError as e:
            logger.error(f"Error listing Hudi .hoodie files: {e}")
            return []
    
    def _read_properties_file(self) -> Optional[Dict[str, str]]:
        """Read hoodie.properties file."""
        try:
            key = f"{self.hoodie_path}/hoodie.properties"
            response = self.s3_client.get_object(Bucket=self.bucket, Key=key)
            content = response['Body'].read().decode('utf-8')
            
            # Parse Java properties format
            props = {}
            for line in content.split('\n'):
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key_val = line.split('=', 1)
                        props[key_val[0].strip()] = key_val[1].strip()
            
            return props
            
        except ClientError as e:
            logger.warning(f"hoodie.properties not found: {e}")
            return {}
    
    def get_schema(self) -> Dict[str, Any]:
        """
        Extract table schema from Hudi metadata.
        
        Note: Hudi doesn't store schema in .hoodie/ - it's in Parquet files.
        This is a simplified implementation.
        """
        logger.info(f"Reading schema for Hudi table {self.bucket}/{self.path}")
        
        props = self._read_properties_file()
        if not props:
            return {
                "success": False,
                "error": "No hoodie.properties found",
                "table_format": "hudi"
            }
        
        return {
            "success": True,
            "table_format": "hudi",
            "table_name": props.get('hoodie.table.name'),
            "table_type": props.get('hoodie.table.type'),
            "table_version": props.get('hoodie.table.version'),
            "base_path": props.get('hoodie.table.base.path'),
            "properties": props,
            "note": "Hudi schema is stored in Parquet files, not in .hoodie/ metadata"
        }
    
    def get_snapshots(self) -> Dict[str, Any]:
        """
        Get commit timeline from Hudi.
        
        Hudi timeline is stored as .commit, .deltacommit, etc. files.
        """
        logger.info(f"Reading snapshots for Hudi table {self.bucket}/{self.path}")
        
        files = self._list_hoodie_files()
        
        # Filter timeline files
        commits = []
        for file in files:
            key = file['key']
            filename = key.split('/')[-1]
            
            # Hudi commit files: <timestamp>.commit, <timestamp>.deltacommit, etc.
            if any(ext in filename for ext in ['.commit', '.deltacommit', '.replacecommit', '.clean']):
                timestamp = filename.split('.')[0]
                commit_type = filename.split('.')[1] if '.' in filename else 'unknown'
                
                commits.append({
                    "timestamp": timestamp,
                    "type": commit_type,
                    "file": filename,
                    "size": file['size']
                })
        
        # Sort by timestamp
        commits.sort(key=lambda x: x['timestamp'])
        
        return {
            "success": True,
            "table_format": "hudi",
            "commit_count": len(commits),
            "commits": commits
        }
    
    def get_partitions(self) -> Dict[str, Any]:
        """
        Get partition information from Hudi.
        
        Partitions are encoded in directory structure.
        """
        logger.info(f"Reading partitions for Hudi table {self.bucket}/{self.path}")
        
        props = self._read_properties_file()
        
        # Check if table is partitioned
        partition_fields = props.get('hoodie.table.partition.fields', '')
        is_partitioned = bool(partition_fields)
        
        return {
            "success": True,
            "table_format": "hudi",
            "is_partitioned": is_partitioned,
            "partition_fields": partition_fields.split(',') if partition_fields else [],
            "properties": props,
            "note": "Partition values require scanning data directory structure"
        }
    
    def get_files(self) -> Dict[str, Any]:
        """
        Get data file information from Hudi.
        
        Note: Simplified - full implementation would parse commit files.
        """
        logger.info(f"Reading files for Hudi table {self.bucket}/{self.path}")
        
        # List files in table path (excluding .hoodie)
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket,
                Prefix=f"{self.path}/",
                MaxKeys=1000
            )
            
            data_files = []
            total_size = 0
            
            if 'Contents' in response:
                for obj in response['Contents']:
                    key = obj['Key']
                    # Exclude .hoodie directory
                    if not '/.hoodie/' in key and key.endswith('.parquet'):
                        data_files.append({
                            "path": key,
                            "size": obj['Size'],
                            "last_modified": obj['LastModified'].isoformat()
                        })
                        total_size += obj['Size']
            
            return {
                "success": True,
                "table_format": "hudi",
                "file_count": len(data_files),
                "total_size_bytes": total_size,
                "files": data_files[:100],  # Limit to first 100
                "note": "Full file list requires parsing Hudi timeline and commit metadata"
            }
            
        except ClientError as e:
            logger.error(f"Error listing Hudi data files: {e}")
            return {
                "success": False,
                "error": str(e),
                "table_format": "hudi"
            }
