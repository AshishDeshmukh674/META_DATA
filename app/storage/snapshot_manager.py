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
        
        Automatically detects which snapshot is older based on timestamps
        and correctly labels them as "old" and "new".
        
        Args:
            snapshot1: First snapshot metadata
            snapshot2: Second snapshot metadata
            
        Returns:
            Dictionary with differences:
            {
                "schema_changes": {
                    "added_columns": [...],
                    "removed_columns": [...],
                    "type_changes": [...]
                },
                "data_changes": {
                    "row_count_change": int,
                    "old_row_count": int,
                    "new_row_count": int
                },
                "file_changes": {
                    "file_count_change": int,
                    "size_change_bytes": int
                },
                "version_changes": {
                    "old_version": ...,
                    "new_version": ...,
                    "operations": [...]
                },
                "partition_changes": {
                    "added_partitions": [...],
                    "removed_partitions": [...]
                }
            }
        """
        try:
            # Detect which snapshot is older based on timestamps
            timestamp1 = snapshot1.get('generated_at', '')
            timestamp2 = snapshot2.get('generated_at', '')
            
            # If snapshot1 is newer than snapshot2, swap them
            if timestamp1 > timestamp2:
                old_snapshot = snapshot2
                new_snapshot = snapshot1
                logger.info(f"Swapped snapshots: snapshot1 ({timestamp1}) is newer than snapshot2 ({timestamp2})")
            else:
                old_snapshot = snapshot1
                new_snapshot = snapshot2
                logger.info(f"Chronological order: snapshot1 ({timestamp1}) is older than snapshot2 ({timestamp2})")
            
            # Schema changes (old -> new)
            schema_old_fields = {f['name']: f['type'] for f in old_snapshot['schema']['fields']}
            schema_new_fields = {f['name']: f['type'] for f in new_snapshot['schema']['fields']}
            
            added_columns = [name for name in schema_new_fields if name not in schema_old_fields]
            removed_columns = [name for name in schema_old_fields if name not in schema_new_fields]
            type_changes = [
                {"column": name, "old_type": schema_old_fields[name], "new_type": schema_new_fields[name]}
                for name in schema_old_fields
                if name in schema_new_fields and schema_old_fields[name] != schema_new_fields[name]
            ]
            
            # Data changes (row count) - old -> new
            row_count_old = old_snapshot.get('row_count', 0)
            row_count_new = new_snapshot.get('row_count', 0)
            row_count_change = row_count_new - row_count_old
            
            # File changes - old -> new
            file_count_old = old_snapshot['files'].get('file_count', 0)
            file_count_new = new_snapshot['files'].get('file_count', 0)
            size_old = old_snapshot['files'].get('total_size_bytes', 0)
            size_new = new_snapshot['files'].get('total_size_bytes', 0)
            
            # Version changes (for Delta Lake) - old -> new
            version_changes = {}
            if old_snapshot.get('version_info') and new_snapshot.get('version_info'):
                version_old = old_snapshot['version_info']
                version_new = new_snapshot['version_info']
                
                if version_old.get('format') == 'delta' and version_new.get('format') == 'delta':
                    old_version_num = version_old.get('version', 'unknown')
                    new_version_num = version_new.get('version', 'unknown')
                    
                    version_changes = {
                        "old_version": old_version_num,
                        "new_version": new_version_num,
                        "version_difference": new_version_num - old_version_num if isinstance(new_version_num, int) and isinstance(old_version_num, int) else 0,
                        "old_operation": version_old.get('operation', 'UNKNOWN'),
                        "new_operation": version_new.get('operation', 'UNKNOWN'),
                        "old_timestamp": version_old.get('timestamp', 'unknown'),
                        "new_timestamp": version_new.get('timestamp', 'unknown')
                    }
            
            # Build comparison result (keep original snapshot IDs for reference)
            comparison = {
                "snapshot1_id": snapshot1['snapshot_id'],
                "snapshot2_id": snapshot2['snapshot_id'],
                "snapshot1_timestamp": snapshot1.get('generated_at', 'unknown'),
                "snapshot2_timestamp": snapshot2.get('generated_at', 'unknown'),
                "schema_changes": {
                    "added_columns": added_columns,
                    "removed_columns": removed_columns,
                    "type_changes": type_changes
                },
                "data_changes": {
                    "row_count_change": row_count_change,
                    "old_row_count": row_count_old,
                    "new_row_count": row_count_new,
                    "percentage_change": round((row_count_change / row_count_old * 100), 2) if row_count_old > 0 else 0
                },
                "file_changes": {
                    "file_count_change": file_count_new - file_count_old,
                    "old_file_count": file_count_old,
                    "new_file_count": file_count_new,
                    "size_change_bytes": size_new - size_old,
                    "old_size_bytes": size_old,
                    "new_size_bytes": size_new
                },
                "version_changes": version_changes if version_changes else None
            }
            
            logger.info(
                f"Compared snapshots",
                extra={
                    "snapshot1": snapshot1['snapshot_id'],
                    "snapshot2": snapshot2['snapshot_id'],
                    "columns_added": len(added_columns),
                    "columns_removed": len(removed_columns),
                    "row_count_change": row_count_change
                }
            )
            
            return comparison
            
        except Exception as e:
            logger.error(f"Failed to compare snapshots: {e}", exc_info=True)
            raise
