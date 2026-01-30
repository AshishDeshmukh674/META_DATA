"""
Table Format Detection Service.

Automatically detects lakehouse table format by inspecting storage layout.
Supports Delta Lake, Apache Iceberg, Apache Hudi, and plain Parquet.

Detection Strategy:
- Delta: Look for _delta_log/ directory with JSON files
- Iceberg: Look for metadata/ directory with .metadata.json files  
- Hudi: Look for .hoodie/ directory with hoodie.properties
- Parquet: Look for .parquet files without metadata directories

Why Auto-Detection?
- User doesn't need to specify format
- Prevents misconfiguration
- Routes to correct metadata reader
"""

import boto3
from botocore.exceptions import ClientError
from typing import Dict, Any, Tuple, List
from datetime import datetime

from app.core.logger import get_logger
from app.core.settings import settings

logger = get_logger()


class FormatDetector:
    """
    Service for detecting lakehouse table formats.
    
    Inspects S3/MinIO storage to identify Delta, Iceberg, Hudi, or Parquet tables.
    """
    
    def __init__(
        self,
        bucket: str,
        path: str,
        storage_type: str = "minio",
        access_key: str = None,
        secret_key: str = None,
        endpoint: str = None,
        region: str = "us-east-1"
    ):
        """
        Initialize format detector.
        
        Args:
            bucket: S3 bucket name
            path: Path to table within bucket
            storage_type: 'aws' or 'minio'
            access_key: Access key (optional, uses settings if None)
            secret_key: Secret key (optional, uses settings if None)
            endpoint: MinIO endpoint (required if storage_type='minio')
            region: AWS region (for storage_type='aws')
        """
        self.bucket = bucket
        self.path = path.strip("/")  # Remove leading/trailing slashes
        self.storage_type = storage_type
        
        # Set credentials
        if storage_type == "minio":
            self.access_key = access_key or settings.minio_access_key
            self.secret_key = secret_key or settings.minio_secret_key
            self.endpoint = endpoint or settings.minio_endpoint
            self.region = None
        else:  # aws
            self.access_key = access_key or settings.aws_access_key_id
            self.secret_key = secret_key or settings.aws_secret_access_key
            self.endpoint = None
            self.region = region
        
        self.s3_client = None
    
    def create_client(self) -> boto3.client:
        """Create S3 client."""
        if not self.s3_client:
            if self.storage_type == "minio":
                self.s3_client = boto3.client(
                    's3',
                    endpoint_url=self.endpoint,
                    aws_access_key_id=self.access_key,
                    aws_secret_access_key=self.secret_key,
                    verify=False
                )
            else:  # aws
                self.s3_client = boto3.client(
                    's3',
                    aws_access_key_id=self.access_key,
                    aws_secret_access_key=self.secret_key,
                    region_name=self.region
                )
        return self.s3_client
    
    def detect(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Detect table format.
        
        Returns:
            Tuple of (success: bool, result: dict)
        """
        logger.info(
            "Detecting table format",
            extra={
                "bucket": self.bucket,
                "path": self.path,
                "storage_type": self.storage_type
            }
        )
        
        try:
            client = self.create_client()
            
            # List files at path
            files = self._list_files(client)
            
            if not files:
                return False, {
                    "success": False,
                    "format": "unknown",
                    "confidence": "low",
                    "message": f"No files found at path '{self.path}'",
                    "file_count": 0,
                    "markers_found": [],
                    "timestamp": datetime.utcnow().isoformat() + "Z".isoformat() + "Z"
                }
            
            # Count data files
            data_files = sum(1 for f in files if f.endswith('.parquet'))
            
            # Try detection in order of specificity
            # (Most specific formats first)
            
            # 1. Check for Delta Lake
            delta_result = self._check_delta(files)
            if delta_result:
                logger.info("Detected Delta Lake table")
                return True, {
                    "success": True,
                    "format": "delta",
                    "confidence": "high",
                    "metadata_location": f"s3://{self.bucket}/{self.path}/_delta_log/",
                    "markers_found": delta_result,
                    "file_count": len(files),
                    "data_files": data_files,
                    "message": "Detected Delta Lake table with transaction log",
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            
            # 2. Check for Iceberg
            iceberg_result = self._check_iceberg(files)
            if iceberg_result:
                logger.info("Detected Iceberg table")
                return True, {
                    "success": True,
                    "format": "iceberg",
                    "confidence": "high",
                    "metadata_location": f"s3://{self.bucket}/{self.path}/metadata/",
                    "markers_found": iceberg_result,
                    "file_count": len(files),
                    "data_files": data_files,
                    "message": "Detected Apache Iceberg table with metadata files",
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            
            # 3. Check for Hudi
            hudi_result = self._check_hudi(files)
            if hudi_result:
                logger.info("Detected Hudi table")
                return True, {
                    "success": True,
                    "format": "hudi",
                    "confidence": "high",
                    "metadata_location": f"s3://{self.bucket}/{self.path}/.hoodie/",
                    "markers_found": hudi_result,
                    "file_count": len(files),
                    "data_files": data_files,
                    "message": "Detected Apache Hudi table with timeline metadata",
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            
            # 4. Check for Parquet (fallback)
            if data_files > 0:
                logger.info("Detected plain Parquet files")
                return True, {
                    "success": True,
                    "format": "parquet",
                    "confidence": "medium",
                    "metadata_location": None,
                    "markers_found": [f"{data_files} .parquet files"],
                    "file_count": len(files),
                    "data_files": data_files,
                    "message": "Detected plain Parquet files (no lakehouse metadata)",
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            
            # Unknown format
            return True, {
                "success": True,
                "format": "unknown",
                "confidence": "low",
                "metadata_location": None,
                "markers_found": [],
                "file_count": len(files),
                "data_files": data_files,
                "message": f"Found {len(files)} files but could not determine table format",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            logger.error(
                "Format detection failed",
                extra={"error": error_code, "message": str(e)}
            )
            return False, {
                "success": False,
                "format": "unknown",
                "confidence": "low",
                "message": f"Error accessing storage: {error_code}",
                "file_count": 0,
                "markers_found": [],
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        
        except Exception as e:
            logger.exception("Unexpected error during format detection")
            return False, {
                "success": False,
                "format": "unknown",
                "confidence": "low",
                "message": f"Unexpected error: {str(e)}",
                "file_count": 0,
                "markers_found": [],
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
    
    def _list_files(self, client: boto3.client, max_keys: int = 1000) -> List[str]:
        """
        List all files at the table path.
        
        Returns:
            List of file keys (paths)
        """
        prefix = self.path + "/" if self.path else ""
        files = []
        
        try:
            paginator = client.get_paginator('list_objects_v2')
            pages = paginator.paginate(
                Bucket=self.bucket,
                Prefix=prefix,
                MaxKeys=max_keys
            )
            
            for page in pages:
                if 'Contents' in page:
                    files.extend([obj['Key'] for obj in page['Contents']])
            
            return files
        
        except ClientError:
            return []
    
    def _check_delta(self, files: List[str]) -> List[str]:
        """
        Check for Delta Lake markers.
        
        Delta signature:
        - _delta_log/ directory
        - JSON files like 00000000000000000000.json
        """
        markers = []
        
        # Check for _delta_log directory
        delta_log_files = [f for f in files if '/_delta_log/' in f]
        if delta_log_files:
            markers.append("_delta_log/")
            
            # Check for JSON transaction files
            json_files = [f for f in delta_log_files if f.endswith('.json')]
            if json_files:
                markers.append(f"{len(json_files)} transaction log files")
            
            # Check for checkpoint files
            checkpoint_files = [f for f in delta_log_files if '.checkpoint.parquet' in f]
            if checkpoint_files:
                markers.append(f"{len(checkpoint_files)} checkpoint files")
        
        return markers if markers else None
    
    def _check_iceberg(self, files: List[str]) -> List[str]:
        """
        Check for Iceberg markers.
        
        Iceberg signature:
        - metadata/ directory
        - .metadata.json files (version files)
        - .avro manifest files
        """
        markers = []
        
        # Check for metadata directory
        metadata_files = [f for f in files if '/metadata/' in f]
        if metadata_files:
            markers.append("metadata/")
            
            # Check for metadata.json files
            json_files = [f for f in metadata_files if '.metadata.json' in f]
            if json_files:
                markers.append(f"{len(json_files)} metadata version files")
            
            # Check for manifest files
            avro_files = [f for f in metadata_files if '.avro' in f]
            if avro_files:
                markers.append(f"{len(avro_files)} manifest files")
        
        return markers if markers else None
    
    def _check_hudi(self, files: List[str]) -> List[str]:
        """
        Check for Hudi markers.
        
        Hudi signature:
        - .hoodie/ directory
        - hoodie.properties file
        - .commit or .inflight files
        """
        markers = []
        
        # Check for .hoodie directory
        hoodie_files = [f for f in files if '/.hoodie/' in f]
        if hoodie_files:
            markers.append(".hoodie/")
            
            # Check for hoodie.properties
            if any('hoodie.properties' in f for f in hoodie_files):
                markers.append("hoodie.properties")
            
            # Check for commit files
            commit_files = [f for f in hoodie_files if '.commit' in f]
            if commit_files:
                markers.append(f"{len(commit_files)} commit files")
        
        return markers if markers else None
