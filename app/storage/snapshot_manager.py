"""
Snapshot Manager for Metadata Storage.

Handles S3 operations for storing and retrieving metadata snapshots.

Storage Pattern:
    s3://bucket/path/to/table/
      └── .metadata-snapshots/
          ├── snapshot_20260207_173045_a1b2c3d4.json
          ├── snapshot_20260207_180000_def45678.json
          └── snapshot_20260208_090000_ghi78901.json

Why .metadata-snapshots/?
- Co-located with table data (portable)
- Hidden folder (like _delta_log/)
- No separate bucket needed
- User controls storage location

Usage:
    manager = SnapshotManager()
    
    # Save snapshot
    location = manager.save_snapshot(
        storage_type="aws",
        bucket="metadataproject",
        path="tables/sales",
        snapshot_id="snapshot_20260207_173045_a1b2c3d4",
        metadata={"schema": {...}, ...}
    )
    
    # Get latest snapshot
    snapshot = manager.get_latest_snapshot("aws", "bucket", "path")
    
    # List all snapshots
    snapshots = manager.list_snapshots("aws", "bucket", "path")
    
    # Compare two snapshots
    diff = manager.compare_snapshots(snapshot1, snapshot2)
"""

import json
import boto3
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.core.settings import settings
from app.core.logger import get_logger

logger = get_logger()


class SnapshotManager:
    """
    Manages metadata snapshot storage in S3.
    
    Snapshots are stored at: <table_path>/.metadata-snapshots/<snapshot_id>.json
    """
    
    SNAPSHOT_FOLDER = ".metadata-snapshots"
    
    def __init__(self):
        """Initialize snapshot manager."""
        logger.info("Snapshot manager initialized")
    
    def _get_s3_client(self, storage_type: str):
        """
        Get boto3 S3 client based on storage type.
        
        Args:
            storage_type: "aws" or "minio"
            
        Returns:
            boto3 S3 client
        """
        if storage_type == "aws":
            return boto3.client(
                's3',
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
                region_name=settings.aws_region
            )
        elif storage_type == "minio":
            return boto3.client(
                's3',
                endpoint_url=settings.minio_endpoint,
                aws_access_key_id=settings.minio_access_key,
                aws_secret_access_key=settings.minio_secret_key,
                region_name='us-east-1'  # MinIO doesn't care about region
            )
        else:
            raise ValueError(f"Unsupported storage type: {storage_type}")
    
    def _build_snapshot_key(self, table_path: str, snapshot_id: str) -> str:
        """
        Build S3 key for snapshot.
        
        Args:
            table_path: Path to table within bucket (e.g., "tables/sales")
            snapshot_id: Snapshot ID (e.g., "snapshot_20260207_173045_a1b2c3d4")
            
        Returns:
            Full S3 key: "tables/sales/.metadata-snapshots/snapshot_20260207_173045_a1b2c3d4.json"
        """
        # Remove leading/trailing slashes
        table_path = table_path.strip('/')
        
        # Build key
        key = f"{table_path}/{self.SNAPSHOT_FOLDER}/{snapshot_id}.json"
        return key
    
    def save_snapshot(
        self,
        storage_type: str,
        bucket: str,
        path: str,
        snapshot_id: str,
        metadata: Dict[str, Any]
    ) -> str:
        """
        Save metadata snapshot to S3.
        
        Args:
            storage_type: "aws" or "minio"
            bucket: S3 bucket name
            path: Path to table within bucket
            snapshot_id: Generated snapshot ID
            metadata: Metadata dictionary from Spark engine
            
        Returns:
            Full S3 URI of saved snapshot
            
        Example:
            location = manager.save_snapshot(
                storage_type="aws",
                bucket="metadataproject",
                path="tables/sales_delta",
                snapshot_id="snapshot_20260207_173045_a1b2c3d4",
                metadata={...}
            )
            # Returns: "s3://metadataproject/tables/sales_delta/.metadata-snapshots/snapshot_20260207_173045_a1b2c3d4.json"
        """
        try:
            # Build S3 key
            key = self._build_snapshot_key(path, snapshot_id)
            
            # Convert metadata to JSON
            json_data = json.dumps(metadata, indent=2)
            
            # Get S3 client
            s3_client = self._get_s3_client(storage_type)
            
            # Upload to S3
            s3_client.put_object(
                Bucket=bucket,
                Key=key,
                Body=json_data.encode('utf-8'),
                ContentType='application/json'
            )
            
            # Build full S3 URI
            s3_uri = f"s3://{bucket}/{key}"
            
            logger.info(
                f"Snapshot saved successfully",
                extra={
                    "snapshot_id": snapshot_id,
                    "s3_uri": s3_uri,
                    "size_bytes": len(json_data)
                }
            )
            
            return s3_uri
            
        except Exception as e:
            logger.error(f"Failed to save snapshot: {e}", exc_info=True)
            raise
    
    def get_latest_snapshot(
        self,
        storage_type: str,
        bucket: str,
        path: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get the most recent snapshot for a table.
        
        Args:
            storage_type: "aws" or "minio"
            bucket: S3 bucket name
            path: Path to table within bucket
            
        Returns:
            Metadata dictionary or None if no snapshots exist
            
        Process:
        1. List all snapshots in .metadata-snapshots/ folder
        2. Sort by timestamp (newest first)
        3. Load and return the latest one
        """
        try:
            snapshots = self.list_snapshots(storage_type, bucket, path)
            
            if not snapshots:
                logger.warning("No snapshots found")
                return None
            
            # Get latest snapshot (list is already sorted newest first)
            latest = snapshots[0]
            
            # Load the snapshot content
            snapshot_data = self._load_snapshot_content(
                storage_type,
                bucket,
                path,
                latest['snapshot_id']
            )
            
            logger.info(f"Retrieved latest snapshot: {latest['snapshot_id']}")
            return snapshot_data
            
        except Exception as e:
            logger.error(f"Failed to get latest snapshot: {e}", exc_info=True)
            return None
    
    def get_snapshot_by_id(
        self,
        storage_type: str,
        bucket: str,
        path: str,
        snapshot_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get a specific snapshot by its ID.
        
        Args:
            storage_type: "aws" or "minio"
            bucket: S3 bucket name
            path: Path to table within bucket
            snapshot_id: Snapshot ID to retrieve
            
        Returns:
            Metadata dictionary or None if snapshot not found
        """
        try:
            logger.info(f"Retrieving snapshot: {snapshot_id}")
            
            snapshot_data = self._load_snapshot_content(
                storage_type,
                bucket,
                path,
                snapshot_id
            )
            
            if snapshot_data:
                logger.info(f"Retrieved snapshot: {snapshot_id}")
            else:
                logger.warning(f"Snapshot not found: {snapshot_id}")
            
            return snapshot_data
            
        except Exception as e:
            logger.error(f"Failed to get snapshot {snapshot_id}: {e}", exc_info=True)
            return None
    
    def list_snapshots(
        self,
        storage_type: str,
        bucket: str,
        path: str
    ) -> List[Dict[str, Any]]:
        """
        List all snapshots for a table.
        
        Args:
            storage_type: "aws" or "minio"
            bucket: S3 bucket name
            path: Path to table within bucket
            
        Returns:
            List of snapshot info dictionaries, sorted by time (newest first)
            [
                {
                    "snapshot_id": "snapshot_20260207_173045_a1b2c3d4",
                    "timestamp": "2026-02-07T17:30:45Z",
                    "size_bytes": 12345,
                    "s3_key": "tables/sales/.metadata-snapshots/snapshot_20260207_173045_a1b2c3d4.json"
                },
                ...
            ]
        """
        try:
            # Build prefix for snapshot folder
            table_path = path.strip('/')
            prefix = f"{table_path}/{self.SNAPSHOT_FOLDER}/"
            
            # Get S3 client
            s3_client = self._get_s3_client(storage_type)
            
            # List objects in snapshot folder
            response = s3_client.list_objects_v2(
                Bucket=bucket,
                Prefix=prefix
            )
            
            snapshots = []
            
            if 'Contents' in response:
                for obj in response['Contents']:
                    key = obj['Key']
                    
                    # Extract snapshot ID from key
                    # Key format: "tables/sales/.metadata-snapshots/snapshot_20260207_173045_a1b2c3d4.json"
                    filename = key.split('/')[-1]
                    snapshot_id = filename.replace('.json', '')
                    
                    # Extract timestamp from snapshot_id
                    # Format: snapshot_YYYYMMDD_HHMMSS_<uuid>
                    parts = snapshot_id.split('_')
                    if len(parts) >= 3:
                        date_str = parts[1]  # YYYYMMDD
                        time_str = parts[2]  # HHMMSS
                        
                        # Convert to ISO format
                        timestamp_str = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}T{time_str[:2]}:{time_str[2:4]}:{time_str[4:6]}Z"
                    else:
                        timestamp_str = obj['LastModified'].isoformat()
                    
                    snapshots.append({
                        "snapshot_id": snapshot_id,
                        "timestamp": timestamp_str,
                        "size_bytes": obj['Size'],
                        "s3_key": key
                    })
            
            # Sort by timestamp (newest first)
            snapshots.sort(key=lambda x: x['timestamp'], reverse=True)
            
            logger.info(f"Found {len(snapshots)} snapshots for table {path}")
            return snapshots
            
        except Exception as e:
            logger.error(f"Failed to list snapshots: {e}", exc_info=True)
            return []
    
    def _load_snapshot_content(
        self,
        storage_type: str,
        bucket: str,
        path: str,
        snapshot_id: str
    ) -> Dict[str, Any]:
        """
        Load snapshot content from S3.
        
        Args:
            storage_type: "aws" or "minio"
            bucket: S3 bucket name
            path: Path to table within bucket
            snapshot_id: Snapshot ID to load
            
        Returns:
            Metadata dictionary
        """
        try:
            # Build S3 key
            key = self._build_snapshot_key(path, snapshot_id)
            
            # Get S3 client
            s3_client = self._get_s3_client(storage_type)
            
            # Download from S3
            response = s3_client.get_object(Bucket=bucket, Key=key)
            content = response['Body'].read().decode('utf-8')
            
            # Parse JSON
            metadata = json.loads(content)
            
            logger.info(f"Loaded snapshot: {snapshot_id}")
            return metadata
            
        except Exception as e:
            logger.error(f"Failed to load snapshot: {e}", exc_info=True)
            raise
    
    def compare_snapshots(
        self,
        snapshot1: Dict[str, Any],
        snapshot2: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compare two snapshots and return differences.
        
        Args:
            snapshot1: First snapshot metadata (older)
            snapshot2: Second snapshot metadata (newer)
            
        Returns:
            Dictionary with differences:
            {
                "schema_changes": {
                    "added_columns": [...],
                    "removed_columns": [...],
                    "type_changes": [...]
                },
                "file_changes": {
                    "added_files": int,
                    "removed_files": int,
                    "size_change_bytes": int
                },
                "partition_changes": {
                    "added_partitions": [...],
                    "removed_partitions": [...]
                }
            }
        """
        try:
            # Schema changes
            schema1_fields = {f['name']: f['type'] for f in snapshot1['schema']['fields']}
            schema2_fields = {f['name']: f['type'] for f in snapshot2['schema']['fields']}
            
            added_columns = [name for name in schema2_fields if name not in schema1_fields]
            removed_columns = [name for name in schema1_fields if name not in schema2_fields]
            type_changes = [
                {"column": name, "old_type": schema1_fields[name], "new_type": schema2_fields[name]}
                for name in schema1_fields
                if name in schema2_fields and schema1_fields[name] != schema2_fields[name]
            ]
            
            # File changes
            file_count1 = snapshot1['files'].get('file_count', 0)
            file_count2 = snapshot2['files'].get('file_count', 0)
            size1 = snapshot1['files'].get('total_size_bytes', 0)
            size2 = snapshot2['files'].get('total_size_bytes', 0)
            
            # Build comparison result
            comparison = {
                "snapshot1_id": snapshot1['snapshot_id'],
                "snapshot2_id": snapshot2['snapshot_id'],
                "schema_changes": {
                    "added_columns": added_columns,
                    "removed_columns": removed_columns,
                    "type_changes": type_changes
                },
                "file_changes": {
                    "file_count_change": file_count2 - file_count1,
                    "size_change_bytes": size2 - size1
                }
            }
            
            logger.info(
                f"Compared snapshots",
                extra={
                    "snapshot1": snapshot1['snapshot_id'],
                    "snapshot2": snapshot2['snapshot_id'],
                    "columns_added": len(added_columns),
                    "columns_removed": len(removed_columns)
                }
            )
            
            return comparison
            
        except Exception as e:
            logger.error(f"Failed to compare snapshots: {e}", exc_info=True)
            raise
