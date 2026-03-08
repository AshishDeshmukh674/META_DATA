"""
Pydantic schemas for connection validation.

These models define the structure of API requests and responses.
They provide automatic validation, documentation, and type safety.

Why Pydantic Models?
- Automatic validation (reject invalid data)
- Auto-generated API documentation
- Type hints for IDE autocomplete
- Conversion & serialization
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime


def datetime_to_iso(dt: datetime) -> str:
    """Convert datetime to ISO 8601 string."""
    return dt.isoformat() + "Z" if dt else None


class AWSCredentials(BaseModel):
    """
    AWS credentials for S3 access.
    
    Used in POST /connect/aws request body.
    """
    access_key_id: str = Field(
        ...,
        description="AWS Access Key ID",
        min_length=16,
        max_length=128,
        example="AKIAIOSFODNN7EXAMPLE"
    )
    secret_access_key: str = Field(
        ...,
        description="AWS Secret Access Key",
        min_length=1,
        example="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
    )
    region: str = Field(
        default="us-east-1",
        description="AWS region",
        example="us-east-1"
    )
    bucket: str = Field(
        ...,
        description="S3 bucket name",
        min_length=3,
        max_length=63,
        example="my-lakehouse-bucket"
    )
    
    @validator('bucket')
    def validate_bucket_name(cls, v):
        """Validate S3 bucket naming rules."""
        if not v.islower():
            raise ValueError("Bucket name must be lowercase")
        if '..' in v:
            raise ValueError("Bucket name cannot contain consecutive dots")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "access_key_id": "AKIAIOSFODNN7EXAMPLE",
                "secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                "region": "us-east-1",
                "bucket": "my-lakehouse-bucket"
            }
        }


class MinIOCredentials(BaseModel):
    """
    MinIO credentials for local S3-compatible storage.
    
    Used in POST /connect/minio request body.
    """
    endpoint: str = Field(
        ...,
        description="MinIO endpoint URL",
        example="http://localhost:9000"
    )
    access_key: str = Field(
        ...,
        description="MinIO access key",
        example="minioadmin"
    )
    secret_key: str = Field(
        ...,
        description="MinIO secret key",
        example="minioadmin"
    )
    bucket: str = Field(
        ...,
        description="Bucket name",
        min_length=3,
        max_length=63,
        example="lakehouse"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "endpoint": "http://localhost:9000",
                "access_key": "minioadmin",
                "secret_key": "minioadmin",
                "bucket": "lakehouse"
            }
        }


class ConnectionTestResult(BaseModel):
    """
    Result of connection test.
    
    Returned by /connect/aws and /connect/minio endpoints.
    """
    success: bool = Field(
        ...,
        description="Whether connection was successful"
    )
    message: str = Field(
        ...,
        description="Human-readable status message"
    )
    bucket: str = Field(
        ...,
        description="Bucket that was tested"
    )
    bucket_exists: bool = Field(
        ...,
        description="Whether the bucket exists"
    )
    can_list: bool = Field(
        ...,
        description="Whether we can list objects in the bucket"
    )
    can_read: bool = Field(
        default=False,
        description="Whether we can read objects (tested if objects exist)"
    )
    object_count: Optional[int] = Field(
        None,
        description="Number of objects in bucket (limited to first 1000)"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the test was performed"
    )
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() + "Z"
        }
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Successfully connected to AWS S3",
                "bucket": "my-lakehouse-bucket",
                "bucket_exists": True,
                "can_list": True,
                "can_read": True,
                "object_count": 42,
                "timestamp": "2026-01-30T10:30:00Z"
            }
        }


class ConnectionError(BaseModel):
    """
    Error response for connection failures.
    """
    success: bool = False
    error: str = Field(
        ...,
        description="Error type"
    )
    message: str = Field(
        ...,
        description="Detailed error message"
    )
    suggestion: Optional[str] = Field(
        None,
        description="How to fix the error"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error": "InvalidCredentials",
                "message": "The AWS Access Key ID you provided does not exist in our records",
                "suggestion": "Check your AWS_ACCESS_KEY_ID in the .env file or request body",
                "timestamp": "2026-01-30T10:30:00Z"
            }
        }


class DetectFormatRequest(BaseModel):
    """
    Request to detect table format.
    
    Used in POST /detect-format endpoint.
    """
    storage_type: str = Field(
        ...,
        description="Storage backend type",
        pattern="^(aws|minio)$",
        example="minio"
    )
    bucket: str = Field(
        ...,
        description="Bucket name",
        min_length=3,
        example="lakehouse"
    )
    path: str = Field(
        ...,
        description="Path to table within bucket (without leading slash)",
        example="warehouse/sales"
    )
    
    # Optional: credentials (if not using .env)
    access_key: Optional[str] = Field(
        None,
        description="Access key (optional, uses .env if not provided)"
    )
    secret_key: Optional[str] = Field(
        None,
        description="Secret key (optional, uses .env if not provided)"
    )
    endpoint: Optional[str] = Field(
        None,
        description="MinIO endpoint (only for storage_type=minio)"
    )
    region: Optional[str] = Field(
        "us-east-1",
        description="AWS region (only for storage_type=aws)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "storage_type": "minio",
                "bucket": "lakehouse",
                "path": "warehouse/sales"
            }
        }


class DetectFormatResponse(BaseModel):
    """
    Result of format detection.
    
    Returned by /detect-format endpoint.
    """
    success: bool = Field(
        ...,
        description="Whether detection was successful"
    )
    format: str = Field(
        ...,
        description="Detected format: delta, iceberg, hudi, parquet, or unknown"
    )
    confidence: str = Field(
        ...,
        description="Confidence level: high, medium, low"
    )
    metadata_location: Optional[str] = Field(
        None,
        description="Location of metadata files (if applicable)"
    )
    markers_found: list[str] = Field(
        default_factory=list,
        description="Format signature markers found"
    )
    file_count: int = Field(
        ...,
        description="Total number of files found at path"
    )
    data_files: int = Field(
        default=0,
        description="Number of data files (.parquet)"
    )
    message: str = Field(
        ...,
        description="Human-readable detection result"
    )
    timestamp: str = Field(
        ...,
        description="ISO 8601 timestamp"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "format": "delta",
                "confidence": "high",
                "metadata_location": "s3://lakehouse/warehouse/sales/_delta_log/",
                "markers_found": ["_delta_log/", "00000000000000000000.json"],
                "file_count": 15,
                "data_files": 12,
                "message": "Detected Delta Lake table with transaction log",
                "timestamp": "2026-01-30T10:30:00Z"
            }
        }


# ============================================================================
# Phase 5: Metadata Exploration Schemas
# ============================================================================


class MetadataRequest(BaseModel):
    """
    Request for metadata operations (schema, partitions, snapshots, files).
    
    Used in POST /metadata/* endpoints.
    """
    storage_type: str = Field(
        ...,
        description="Storage backend type",
        pattern="^(aws|minio)$",
        example="aws"
    )
    bucket: str = Field(
        ...,
        description="Bucket name",
        min_length=3,
        example="metadataproject"
    )
    path: str = Field(
        ...,
        description="Path to table within bucket",
        example="test-data/sample-data/delta/sales_delta"
    )
    format: Optional[str] = Field(
        None,
        description="Table format (delta/iceberg/hudi/parquet). If not provided, will be auto-detected.",
        pattern="^(delta|iceberg|hudi|parquet)$",
        example="delta"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "storage_type": "aws",
                "bucket": "metadataproject",
                "path": "test-data/sample-data/delta/sales_delta",
                "format": "delta"
            }
        }


class MetadataResponse(BaseModel):
    """Generic metadata response wrapper."""
    success: bool = Field(..., description="Whether operation succeeded")
    table_format: str = Field(..., description="Table format: delta/iceberg/hudi/parquet")
    data: dict = Field(..., description="Format-specific metadata")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "table_format": "delta",
                "data": {
                    "schema": {"fields": []},
                    "version": 5
                },
                "timestamp": "2026-01-31T10:30:00Z"
            }
        }


# ============================================================================
# Phase 6: Metadata Generation & Snapshot Management Schemas
# ============================================================================


class MetadataGenerateRequest(BaseModel):
    """
    Request to generate metadata snapshot using Spark.
    
    Used in POST /metadata/generate endpoint.
    
    Process:
    1. If convert_to_lakehouse=True: Convert raw data (CSV/JSON/Parquet) to lakehouse format first
    2. Auto-detect format if not provided (using Phase 4 detector)
    3. Use Spark to load table
    4. Extract metadata (schema, partitions, files, version)
    5. Generate snapshot_id
    6. Save to S3 at <table_path>/.metadata-snapshots/<snapshot_id>.json
    
    Examples:
    - Existing Delta table: {"storage_type":"aws", "bucket":"mybucket", "path":"tables/delta_table", "table_format":"delta"}
    - Convert CSV to Delta: {"storage_type":"aws", "bucket":"mybucket", "path":"raw/data.csv", "convert_to_lakehouse":true, "target_format":"delta", "source_format":"csv"}
    """
    storage_type: str = Field(
        ...,
        description="Storage backend type",
        pattern="^(aws|minio)$",
        example="aws"
    )
    bucket: str = Field(
        ...,
        description="S3 bucket name",
        min_length=3,
        example="metadataproject"
    )
    path: str = Field(
        ...,
        description="Path to table within bucket (or path to raw data file if converting)",
        example="test-data/sample-data/delta/sales_delta"
    )
    table_format: Optional[str] = Field(
        None,
        description="Table format (delta/iceberg/hudi/parquet). Auto-detected if not provided and convert_to_lakehouse=False.",
        pattern="^(delta|iceberg|hudi|parquet)$",
        example="delta"
    )
    
    # NEW: Raw data conversion parameters
    convert_to_lakehouse: Optional[bool] = Field(
        False,
        description="If True, converts raw data files (CSV/JSON/Parquet) to lakehouse format before generating metadata"
    )
    target_format: Optional[str] = Field(
        None,
        description="Target lakehouse format for conversion (required if convert_to_lakehouse=True)",
        pattern="^(delta|iceberg|hudi)$",
        example="delta"
    )
    source_format: Optional[str] = Field(
        None,
        description="Source file format (required if convert_to_lakehouse=True)",
        pattern="^(csv|json|parquet|avro|orc)$",
        example="csv"
    )
    partition_columns: Optional[List[str]] = Field(
        None,
        description="Columns to partition by when converting to lakehouse format",
        example=["year", "month"]
    )
    
    force_refresh: Optional[bool] = Field(
        False,
        description="Force regeneration even if recent snapshot exists"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "storage_type": "aws",
                "bucket": "metadataproject",
                "path": "test-data/sample-data/delta/sales_delta",
                "table_format": "delta",
                "force_refresh": False
            }
        }


class MetadataGenerateResponse(BaseModel):
    """
    Response from metadata generation.
    
    Returned by POST /metadata/generate endpoint.
    """
    success: bool = Field(..., description="Whether generation succeeded")
    snapshot_id: str = Field(..., description="Generated snapshot ID")
    table_path: str = Field(..., description="Full S3 path to table")
    table_format: str = Field(..., description="Detected/provided table format")
    generated_at: str = Field(..., description="ISO8601 timestamp of generation")
    snapshot_location: str = Field(..., description="Full S3 URI of saved snapshot")
    metadata_summary: Optional[Dict[str, Any]] = Field(
        None,
        description="Summary of extracted metadata"
    )
    error: Optional[str] = Field(None, description="Error message if failed")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "snapshot_id": "snapshot_20260207_173045_a1b2c3d4",
                "table_path": "s3a://metadataproject/test-data/sample-data/delta/sales_delta",
                "table_format": "delta",
                "generated_at": "2026-02-07T17:30:45Z",
                "snapshot_location": "s3://metadataproject/test-data/sample-data/delta/sales_delta/.metadata-snapshots/snapshot_20260207_173045_a1b2c3d4.json",
                "metadata_summary": {
                    "column_count": 8,
                    "file_count": 127,
                    "total_size_bytes": 4589234567
                }
            }
        }


class SnapshotInfo(BaseModel):
    """Information about a single snapshot."""
    snapshot_id: str = Field(..., description="Snapshot ID")
    timestamp: str = Field(..., description="Snapshot creation timestamp")
    size_bytes: int = Field(..., description="Snapshot file size")
    s3_key: str = Field(..., description="S3 key for snapshot")


class SnapshotListResponse(BaseModel):
    """
    Response from listing snapshots.
    
    Returned by GET /metadata/snapshots/list endpoint.
    """
    success: bool = Field(..., description="Whether listing succeeded")
    table_path: str = Field(..., description="Full S3 path to table")
    snapshot_count: int = Field(..., description="Total number of snapshots")
    snapshots: List[SnapshotInfo] = Field(..., description="List of snapshots (newest first)")
    error: Optional[str] = Field(None, description="Error message if failed")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "table_path": "s3://metadataproject/test-data/sample-data/delta/sales_delta",
                "snapshot_count": 3,
                "snapshots": [
                    {
                        "snapshot_id": "snapshot_20260208_090000_ghi78901",
                        "timestamp": "2026-02-08T09:00:00Z",
                        "size_bytes": 15234,
                        "s3_key": "test-data/sample-data/delta/sales_delta/.metadata-snapshots/snapshot_20260208_090000_ghi78901.json"
                    },
                    {
                        "snapshot_id": "snapshot_20260207_180000_def45678",
                        "timestamp": "2026-02-07T18:00:00Z",
                        "size_bytes": 14890,
                        "s3_key": "test-data/sample-data/delta/sales_delta/.metadata-snapshots/snapshot_20260207_180000_def45678.json"
                    }
                ]
            }
        }


class SnapshotDiffRequest(BaseModel):
    """
    Request to compare two snapshots.
    
    Used in POST /metadata/snapshots/diff endpoint.
    """
    storage_type: str = Field(
        ...,
        description="Storage backend type",
        pattern="^(aws|minio)$",
        example="aws"
    )
    bucket: str = Field(
        ...,
        description="S3 bucket name",
        min_length=3,
        example="metadataproject"
    )
    path: str = Field(
        ...,
        description="Path to table within bucket",
        example="test-data/sample-data/delta/sales_delta"
    )
    snapshot_id_1: str = Field(
        ...,
        description="First snapshot ID (usually older)",
        example="snapshot_20260207_173045_a1b2c3d4"
    )
    snapshot_id_2: str = Field(
        ...,
        description="Second snapshot ID (usually newer)",
        example="snapshot_20260208_090000_ghi78901"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "storage_type": "aws",
                "bucket": "metadataproject",
                "path": "test-data/sample-data/delta/sales_delta",
                "snapshot_id_1": "snapshot_20260207_173045_a1b2c3d4",
                "snapshot_id_2": "snapshot_20260208_090000_ghi78901"
            }
        }


class SchemaChange(BaseModel):
    """Schema change details."""
    column: str = Field(..., description="Column name")
    old_type: str = Field(..., description="Old data type")
    new_type: str = Field(..., description="New data type")


class SnapshotDiffResponse(BaseModel):
    """
    Response from snapshot comparison.
    
    Returned by POST /metadata/snapshots/diff endpoint.
    """
    success: bool = Field(..., description="Whether comparison succeeded")
    snapshot1_id: str = Field(..., description="First snapshot ID")
    snapshot2_id: str = Field(..., description="Second snapshot ID")
    snapshot1_timestamp: Optional[str] = Field(None, description="First snapshot timestamp")
    snapshot2_timestamp: Optional[str] = Field(None, description="Second snapshot timestamp")
    schema_changes: Dict[str, Any] = Field(
        ...,
        description="Schema differences (added/removed columns, type changes)"
    )
    data_changes: Optional[Dict[str, Any]] = Field(
        None,
        description="Data differences (row count changes, percentage change)"
    )
    file_changes: Dict[str, Any] = Field(
        ...,
        description="File differences (count change, size change)"
    )
    version_changes: Optional[Dict[str, Any]] = Field(
        None,
        description="Version/transaction differences (Delta Lake version, operations, timestamps)"
    )
    error: Optional[str] = Field(None, description="Error message if failed")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "snapshot1_id": "snapshot_20260207_173045_a1b2c3d4",
                "snapshot2_id": "snapshot_20260208_090000_ghi78901",
                "snapshot1_timestamp": "2026-02-07T17:30:45Z",
                "snapshot2_timestamp": "2026-02-08T09:00:00Z",
                "schema_changes": {
                    "added_columns": ["new_feature_flag"],
                    "removed_columns": [],
                    "type_changes": [
                        {
                            "column": "price",
                            "old_type": "float",
                            "new_type": "double"
                        }
                    ]
                },
                "data_changes": {
                    "row_count_change": 1250,
                    "old_row_count": 10000,
                    "new_row_count": 11250,
                    "percentage_change": 12.5
                },
                "file_changes": {
                    "file_count_change": 15,
                    "old_file_count": 100,
                    "new_file_count": 115,
                    "size_change_bytes": 234567890,
                    "old_size_bytes": 1000000000,
                    "new_size_bytes": 1234567890
                },
                "version_changes": {
                    "old_version": 5,
                    "new_version": 8,
                    "version_difference": 3,
                    "old_operation": "WRITE",
                    "new_operation": "INSERT",
                    "old_timestamp": "2026-02-07T17:30:00Z",
                    "new_timestamp": "2026-02-08T09:00:00Z"
                }
            }
        }

