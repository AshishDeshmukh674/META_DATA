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
from typing import Optional
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
