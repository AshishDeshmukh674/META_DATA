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
