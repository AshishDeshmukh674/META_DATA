"""
Connection Validation API Router.

Endpoints for testing cloud storage connectivity.
MUST be called before using any other lakehouse features.

Why Validate First?
- Fail-fast: Don't waste time if credentials are wrong
- User experience: Clear error messages
- Security: Test before storing credentials
"""

from fastapi import APIRouter, status, HTTPException
from fastapi.responses import JSONResponse

from app.api.schemas import (
    AWSCredentials,
    MinIOCredentials,
    ConnectionTestResult,
    ConnectionError
)
from app.core.aws_client import AWSConnectionService
from app.core.logger import get_logger

logger = get_logger()
router = APIRouter()


@router.post(
    "/aws",
    response_model=ConnectionTestResult,
    status_code=status.HTTP_200_OK,
    summary="Validate AWS credentials and S3 access",
    description=(
        "Tests AWS credentials by:\n"
        "1. Validating credentials format\n"
        "2. Checking if bucket exists\n"
        "3. Testing list permissions\n"
        "4. Testing read permissions (if objects exist)\n\n"
        "**IMPORTANT:** Call this endpoint before using any lakehouse features."
    ),
    responses={
        200: {
            "description": "Connection successful",
            "model": ConnectionTestResult
        },
        400: {
            "description": "Invalid credentials or bucket not accessible",
            "model": ConnectionError
        }
    }
)
async def test_aws_connection(credentials: AWSCredentials):
    """
    Test AWS S3 connection.
    
    This endpoint validates your AWS credentials and tests access to the specified bucket.
    It performs comprehensive checks without modifying any data.
    
    Args:
        credentials: AWS credentials and bucket information
        
    Returns:
        ConnectionTestResult if successful
        
    Raises:
        HTTPException with 400 if validation fails
    """
    logger.info(
        "Testing AWS connection",
        extra={
            "bucket": credentials.bucket,
            "region": credentials.region
        }
    )
    
    # Create connection service
    service = AWSConnectionService(
        access_key_id=credentials.access_key_id,
        secret_access_key=credentials.secret_access_key,
        region=credentials.region
    )
    
    # Test connection
    success, result = service.test_connection(credentials.bucket)
    
    if success:
        return ConnectionTestResult(**result)
    else:
        # Return 400 with error details
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result
        )


@router.post(
    "/minio",
    response_model=ConnectionTestResult,
    status_code=status.HTTP_200_OK,
    summary="Validate MinIO credentials and bucket access",
    description=(
        "Tests MinIO credentials (local S3-compatible storage).\n"
        "Same checks as /connect/aws but for MinIO endpoint.\n\n"
        "**Default MinIO credentials:** minioadmin / minioadmin"
    ),
    responses={
        200: {
            "description": "Connection successful",
            "model": ConnectionTestResult
        },
        400: {
            "description": "Invalid credentials or bucket not accessible",
            "model": ConnectionError
        }
    }
)
async def test_minio_connection(credentials: MinIOCredentials):
    """
    Test MinIO connection.
    
    This endpoint validates MinIO credentials and tests access to the specified bucket.
    MinIO is S3-compatible, so it uses the same underlying boto3 client.
    
    Args:
        credentials: MinIO credentials and bucket information
        
    Returns:
        ConnectionTestResult if successful
        
    Raises:
        HTTPException with 400 if validation fails
    """
    logger.info(
        "Testing MinIO connection",
        extra={
            "endpoint": credentials.endpoint,
            "bucket": credentials.bucket
        }
    )
    
    try:
        # MinIO uses boto3 S3 client with custom endpoint
        import boto3
        from botocore.exceptions import ClientError
        
        # Create S3 client pointing to MinIO
        s3_client = boto3.client(
            's3',
            endpoint_url=credentials.endpoint,
            aws_access_key_id=credentials.access_key,
            aws_secret_access_key=credentials.secret_key,
            verify=False  # MinIO might use self-signed certs in dev
        )
        
        # Test bucket exists
        try:
            s3_client.head_bucket(Bucket=credentials.bucket)
            bucket_exists = True
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code in ['404', 'NoSuchBucket']:
                # Bucket doesn't exist - try to create it
                logger.info(f"Bucket '{credentials.bucket}' not found, attempting to create")
                try:
                    s3_client.create_bucket(Bucket=credentials.bucket)
                    bucket_exists = True
                    logger.info(f"Created bucket '{credentials.bucket}'")
                except Exception as create_error:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail={
                            "success": False,
                            "error": "BucketCreationFailed",
                            "message": f"Bucket '{credentials.bucket}' does not exist and could not be created",
                            "suggestion": "Create the bucket manually in MinIO console (http://localhost:9001)"
                        }
                    )
            else:
                raise
        
        # Test list permissions
        try:
            response = s3_client.list_objects_v2(Bucket=credentials.bucket, MaxKeys=1000)
            object_count = response.get('KeyCount', 0)
            can_list = True
        except ClientError:
            can_list = False
            object_count = 0
        
        # Test read permissions (if objects exist)
        can_read = False
        if object_count > 0:
            try:
                response = s3_client.list_objects_v2(Bucket=credentials.bucket, MaxKeys=1)
                if 'Contents' in response:
                    first_key = response['Contents'][0]['Key']
                    s3_client.head_object(Bucket=credentials.bucket, Key=first_key)
                    can_read = True
            except ClientError:
                pass
        
        logger.info(
            "MinIO connection successful",
            extra={
                "bucket": credentials.bucket,
                "object_count": object_count
            }
        )
        
        return ConnectionTestResult(
            success=True,
            message=f"Successfully connected to MinIO bucket '{credentials.bucket}'",
            bucket=credentials.bucket,
            bucket_exists=bucket_exists,
            can_list=can_list,
            can_read=can_read,
            object_count=object_count
        )
        
    except Exception as e:
        logger.exception("MinIO connection test failed")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": "ConnectionFailed",
                "message": str(e),
                "suggestion": (
                    "1. Ensure MinIO is running (docker-compose up -d)\n"
                    "2. Check endpoint URL (default: http://localhost:9000)\n"
                    "3. Verify credentials (default: minioadmin/minioadmin)"
                )
            }
        )


@router.get(
    "/status",
    summary="Check storage connection status",
    description="Returns the current storage connection configuration (without sensitive data)"
)
async def connection_status():
    """
    Get current storage connection status.
    
    Returns configuration info without exposing credentials.
    Useful for debugging and status checks.
    """
    from app.core.settings import settings
    
    return {
        "aws_configured": settings.aws_access_key_id is not None,
        "aws_region": settings.aws_region if settings.aws_access_key_id else None,
        "aws_bucket": settings.aws_s3_bucket if settings.aws_access_key_id else None,
        "minio_configured": bool(settings.minio_endpoint),
        "minio_endpoint": settings.minio_endpoint,
        "minio_bucket": settings.minio_bucket,
    }
