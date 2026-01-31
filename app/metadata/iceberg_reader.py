"""
Apache Iceberg Metadata Reader

Reads metadata from Iceberg tables stored in metadata/*.json files.
Iceberg uses a tree structure: metadata files → manifest lists → manifests → data files.

References:
- Iceberg Table Spec: https://iceberg.apache.org/spec/
"""

import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import boto3
from botocore.exceptions import ClientError

from app.core.logger import get_logger
from app.core.settings import settings

logger = get_logger()


class IcebergReader:
    """Read Apache Iceberg table metadata."""
    
    def __init__(self, bucket: str, path: str, storage_type: str = "aws"):
        """
        Initialize Iceberg reader.
        
        Args:
            bucket: S3/MinIO bucket name
            path: Path to Iceberg table (contains metadata/)
            storage_type: "aws" or "minio"
        """
        self.bucket = bucket
        self.path = path.rstrip('/')
        self.metadata_path = f"{self.path}/metadata"
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
        
        logger.info(f"Initialized IcebergReader for {bucket}/{path}")
    
    def _list_metadata_files(self) -> List[str]:
        """List all metadata JSON files."""
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket,
                Prefix=f"{self.metadata_path}/",
                MaxKeys=1000
            )
            
            files = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    key = obj['Key']
                    # Metadata files: v1.metadata.json, v2.metadata.json, etc.
                    if 'metadata.json' in key and not key.endswith('/'):
                        files.append(key)
            
            # Sort by version
            files.sort()
            return files
            
        except ClientError as e:
            logger.error(f"Error listing Iceberg metadata files: {e}")
            return []
    
    def _read_metadata_file(self, key: str) -> Optional[Dict[str, Any]]:
        """Read and parse an Iceberg metadata JSON file."""
        try:
            response = self.s3_client.get_object(Bucket=self.bucket, Key=key)
            content = response['Body'].read().decode('utf-8')
            return json.loads(content)
            
        except ClientError as e:
            logger.error(f"Error reading Iceberg metadata file {key}: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON from {key}: {e}")
            return None
    
    def _get_latest_metadata(self) -> Optional[Dict[str, Any]]:
        """Get the latest metadata file."""
        metadata_files = self._list_metadata_files()
        if not metadata_files:
            return None
        
        # Return the last one (highest version)
        return self._read_metadata_file(metadata_files[-1])
    
    def get_schema(self) -> Dict[str, Any]:
        """
        Extract table schema from Iceberg metadata.
        
        Returns schema with column names, types, and IDs.
        """
        logger.info(f"Reading schema for Iceberg table {self.bucket}/{self.path}")
        
        metadata = self._get_latest_metadata()
        if not metadata:
            return {
                "success": False,
                "error": "No Iceberg metadata files found",
                "table_format": "iceberg"
            }
        
        # Iceberg schema structure
        current_schema = metadata.get('current-schema-id')
        schemas = metadata.get('schemas', [])
        
        # Find current schema
        schema = None
        for s in schemas:
            if s.get('schema-id') == current_schema:
                schema = s
                break
        
        if not schema:
            schema = schemas[0] if schemas else {}
        
        return {
            "success": True,
            "table_format": "iceberg",
            "schema": schema,
            "current_schema_id": current_schema,
            "format_version": metadata.get('format-version', 1),
            "location": metadata.get('location'),
            "last_updated_ms": metadata.get('last-updated-ms')
        }
    
    def get_snapshots(self) -> Dict[str, Any]:
        """
        Get snapshot history from Iceberg metadata.
        
        Iceberg maintains explicit snapshots with manifest lists.
        """
        logger.info(f"Reading snapshots for Iceberg table {self.bucket}/{self.path}")
        
        metadata = self._get_latest_metadata()
        if not metadata:
            return {
                "success": False,
                "error": "No Iceberg metadata files found",
                "table_format": "iceberg"
            }
        
        snapshots = metadata.get('snapshots', [])
        current_snapshot_id = metadata.get('current-snapshot-id')
        
        # Enrich snapshot info
        snapshot_info = []
        for snap in snapshots:
            snapshot_info.append({
                "snapshot_id": snap.get('snapshot-id'),
                "timestamp_ms": snap.get('timestamp-ms'),
                "operation": snap.get('summary', {}).get('operation', 'UNKNOWN'),
                "manifest_list": snap.get('manifest-list'),
                "summary": snap.get('summary', {}),
                "is_current": snap.get('snapshot-id') == current_snapshot_id
            })
        
        return {
            "success": True,
            "table_format": "iceberg",
            "snapshot_count": len(snapshot_info),
            "current_snapshot_id": current_snapshot_id,
            "snapshots": snapshot_info
        }
    
    def get_partitions(self) -> Dict[str, Any]:
        """
        Get partition spec from Iceberg metadata.
        
        Iceberg uses partition specs with transform functions.
        """
        logger.info(f"Reading partitions for Iceberg table {self.bucket}/{self.path}")
        
        metadata = self._get_latest_metadata()
        if not metadata:
            return {
                "success": False,
                "error": "No Iceberg metadata files found",
                "table_format": "iceberg"
            }
        
        # Iceberg partition specs
        partition_specs = metadata.get('partition-specs', [])
        default_spec_id = metadata.get('default-spec-id', 0)
        
        # Find default spec
        default_spec = None
        for spec in partition_specs:
            if spec.get('spec-id') == default_spec_id:
                default_spec = spec
                break
        
        if not default_spec:
            default_spec = partition_specs[0] if partition_specs else {}
        
        fields = default_spec.get('fields', [])
        is_partitioned = len(fields) > 0
        
        return {
            "success": True,
            "table_format": "iceberg",
            "is_partitioned": is_partitioned,
            "default_spec_id": default_spec_id,
            "partition_specs": partition_specs,
            "partition_fields": fields
        }
    
    def get_files(self) -> Dict[str, Any]:
        """
        Get data file list from Iceberg manifests.
        
        Note: This is simplified - full implementation would parse manifest lists and manifests.
        """
        logger.info(f"Reading files for Iceberg table {self.bucket}/{self.path}")
        
        metadata = self._get_latest_metadata()
        if not metadata:
            return {
                "success": False,
                "error": "No Iceberg metadata files found",
                "table_format": "iceberg"
            }
        
        # Get current snapshot
        current_snapshot_id = metadata.get('current-snapshot-id')
        snapshots = metadata.get('snapshots', [])
        
        current_snapshot = None
        for snap in snapshots:
            if snap.get('snapshot-id') == current_snapshot_id:
                current_snapshot = snap
                break
        
        if not current_snapshot:
            return {
                "success": False,
                "error": "No current snapshot found",
                "table_format": "iceberg"
            }
        
        manifest_list_path = current_snapshot.get('manifest-list', '')
        
        # Extract summary statistics
        summary = current_snapshot.get('summary', {})
        
        return {
            "success": True,
            "table_format": "iceberg",
            "snapshot_id": current_snapshot_id,
            "manifest_list": manifest_list_path,
            "total_records": summary.get('total-records', 0),
            "total_data_files": summary.get('total-data-files', 0),
            "total_delete_files": summary.get('total-delete-files', 0),
            "summary": summary,
            "note": "Full file listing requires parsing manifest files (not implemented in this phase)"
        }
