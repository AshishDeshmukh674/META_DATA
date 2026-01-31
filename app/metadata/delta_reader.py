"""
Delta Lake Metadata Reader

Reads metadata directly from Delta Lake's transaction log (_delta_log/).
Delta stores JSON files with schema, statistics, and transaction history.

References:
- Delta Transaction Log Protocol: https://github.com/delta-io/delta/blob/master/PROTOCOL.md
"""

import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import boto3
from botocore.exceptions import ClientError

from app.core.logger import get_logger
from app.core.settings import settings

logger = get_logger()


class DeltaReader:
    """Read Delta Lake table metadata from transaction log."""
    
    def __init__(self, bucket: str, path: str, storage_type: str = "aws"):
        """
        Initialize Delta reader.
        
        Args:
            bucket: S3/MinIO bucket name
            path: Path to Delta table (contains _delta_log/)
            storage_type: "aws" or "minio"
        """
        self.bucket = bucket
        self.path = path.rstrip('/')
        self.delta_log_path = f"{self.path}/_delta_log"
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
        
        logger.info(f"Initialized DeltaReader for {bucket}/{path}")
    
    def _list_log_files(self) -> List[str]:
        """List all transaction log files in order."""
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket,
                Prefix=f"{self.delta_log_path}/",
                MaxKeys=1000
            )
            
            files = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    key = obj['Key']
                    # Only .json files (not .checkpoint.parquet)
                    if key.endswith('.json') and not 'checkpoint' in key:
                        files.append(key)
            
            # Sort by version number (000000000000000000.json, 000000000000000001.json, etc.)
            files.sort()
            return files
            
        except ClientError as e:
            logger.error(f"Error listing Delta log files: {e}")
            return []
    
    def _read_log_file(self, key: str) -> Optional[Dict[str, Any]]:
        """Read and parse a single Delta log JSON file."""
        try:
            response = self.s3_client.get_object(Bucket=self.bucket, Key=key)
            content = response['Body'].read().decode('utf-8')
            
            # Delta log files contain newline-delimited JSON
            # Each line is a separate action
            actions = []
            for line in content.strip().split('\n'):
                if line:
                    actions.append(json.loads(line))
            
            return {
                'version': self._extract_version(key),
                'key': key,
                'actions': actions
            }
            
        except ClientError as e:
            logger.error(f"Error reading Delta log file {key}: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON from {key}: {e}")
            return None
    
    def _extract_version(self, key: str) -> int:
        """Extract version number from log file name."""
        # Extract from "path/_delta_log/000000000000000005.json"
        filename = key.split('/')[-1]
        version_str = filename.replace('.json', '')
        return int(version_str)
    
    def get_schema(self) -> Dict[str, Any]:
        """
        Extract table schema from Delta transaction log.
        
        Returns schema with column names, types, and metadata.
        """
        logger.info(f"Reading schema for Delta table {self.bucket}/{self.path}")
        
        log_files = self._list_log_files()
        if not log_files:
            return {
                "success": False,
                "error": "No Delta transaction log files found",
                "table_format": "delta"
            }
        
        # Read the latest log file first (has most recent schema)
        for log_file in reversed(log_files):
            log_data = self._read_log_file(log_file)
            if not log_data:
                continue
            
            # Look for metaData action (contains schema)
            for action in log_data['actions']:
                if 'metaData' in action:
                    metadata = action['metaData']
                    schema_string = metadata.get('schemaString', '{}')
                    schema_json = json.loads(schema_string)
                    
                    return {
                        "success": True,
                        "table_format": "delta",
                        "schema": schema_json,
                        "partition_columns": metadata.get('partitionColumns', []),
                        "configuration": metadata.get('configuration', {}),
                        "created_time": metadata.get('createdTime'),
                        "version": log_data['version']
                    }
        
        return {
            "success": False,
            "error": "No schema metadata found in transaction log",
            "table_format": "delta"
        }
    
    def get_snapshots(self) -> Dict[str, Any]:
        """
        Get version history (snapshots) from Delta transaction log.
        
        Each JSON file represents a version/snapshot.
        """
        logger.info(f"Reading snapshots for Delta table {self.bucket}/{self.path}")
        
        log_files = self._list_log_files()
        if not log_files:
            return {
                "success": False,
                "error": "No Delta transaction log files found",
                "table_format": "delta"
            }
        
        snapshots = []
        for log_file in log_files:
            log_data = self._read_log_file(log_file)
            if not log_data:
                continue
            
            version = log_data['version']
            actions = log_data['actions']
            
            # Extract commit info if available
            commit_info = {}
            for action in actions:
                if 'commitInfo' in action:
                    commit_info = action['commitInfo']
                    break
            
            # Count add/remove actions
            adds = sum(1 for a in actions if 'add' in a)
            removes = sum(1 for a in actions if 'remove' in a)
            
            snapshots.append({
                "version": version,
                "timestamp": commit_info.get('timestamp'),
                "operation": commit_info.get('operation', 'UNKNOWN'),
                "files_added": adds,
                "files_removed": removes,
                "user_metadata": commit_info.get('userMetadata', {}),
                "job": commit_info.get('job', {}),
                "notebook": commit_info.get('notebook', {})
            })
        
        return {
            "success": True,
            "table_format": "delta",
            "snapshot_count": len(snapshots),
            "latest_version": snapshots[-1]['version'] if snapshots else None,
            "snapshots": snapshots
        }
    
    def get_partitions(self) -> Dict[str, Any]:
        """
        Get partition information from Delta table.
        
        Reads schema to get partition columns, then scans data files for values.
        """
        logger.info(f"Reading partitions for Delta table {self.bucket}/{self.path}")
        
        # First get schema to know partition columns
        schema_info = self.get_schema()
        if not schema_info.get('success'):
            return schema_info
        
        partition_columns = schema_info.get('partition_columns', [])
        if not partition_columns:
            return {
                "success": True,
                "table_format": "delta",
                "is_partitioned": False,
                "partition_columns": [],
                "partitions": []
            }
        
        # Scan log files to collect partition values from add actions
        log_files = self._list_log_files()
        partition_values = set()
        
        for log_file in log_files:
            log_data = self._read_log_file(log_file)
            if not log_data:
                continue
            
            for action in log_data['actions']:
                if 'add' in action:
                    add_action = action['add']
                    path = add_action.get('path', '')
                    partition_vals = add_action.get('partitionValues', {})
                    
                    if partition_vals:
                        # Convert to tuple for set uniqueness
                        partition_values.add(tuple(sorted(partition_vals.items())))
        
        # Convert back to list of dicts
        partitions = [dict(pv) for pv in partition_values]
        
        return {
            "success": True,
            "table_format": "delta",
            "is_partitioned": True,
            "partition_columns": partition_columns,
            "partition_count": len(partitions),
            "partitions": partitions
        }
    
    def get_files(self) -> Dict[str, Any]:
        """
        Get list of data files from Delta table.
        
        Reconstructs current table state by replaying add/remove actions.
        """
        logger.info(f"Reading files for Delta table {self.bucket}/{self.path}")
        
        log_files = self._list_log_files()
        if not log_files:
            return {
                "success": False,
                "error": "No Delta transaction log files found",
                "table_format": "delta"
            }
        
        # Track current state of files (path -> file info)
        active_files = {}
        
        # Replay transaction log
        for log_file in log_files:
            log_data = self._read_log_file(log_file)
            if not log_data:
                continue
            
            for action in log_data['actions']:
                # Add action: file added to table
                if 'add' in action:
                    add_action = action['add']
                    path = add_action['path']
                    active_files[path] = {
                        "path": path,
                        "size": add_action.get('size', 0),
                        "modification_time": add_action.get('modificationTime'),
                        "data_change": add_action.get('dataChange', True),
                        "partition_values": add_action.get('partitionValues', {}),
                        "stats": add_action.get('stats', '{}')
                    }
                
                # Remove action: file removed from table
                elif 'remove' in action:
                    remove_action = action['remove']
                    path = remove_action['path']
                    if path in active_files:
                        del active_files[path]
        
        files = list(active_files.values())
        total_size = sum(f['size'] for f in files)
        
        return {
            "success": True,
            "table_format": "delta",
            "file_count": len(files),
            "total_size_bytes": total_size,
            "files": files
        }
