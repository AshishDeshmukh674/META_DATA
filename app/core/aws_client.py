"""
AWS S3 Connection Service.

This module handles AWS credential validation and S3 connectivity testing.
It uses boto3 (AWS SDK for Python) to interact with S3.

Why This Design?
- Separate business logic from API routes
- Reusable across multiple endpoints
- Easy to mock for testing
- Clear error handling
"""

import boto3
from botocore.exceptions import (
    ClientError,
    NoCredentialsError,
    PartialCredentialsError,
    EndpointConnectionError,
)
from typing import Dict, Any, Tuple
from datetime import datetime

from app.core.logger import get_logger
from app.api.schemas import ConnectionTestResult, ConnectionError

logger = get_logger()


class AWSConnectionService:
    """
    Service for testing AWS S3 connectivity.
    
    Validates credentials and performs comprehensive S3 access tests.
    """
    
    def __init__(
        self,
        access_key_id: str,
        secret_access_key: str,
        region: str = "us-east-1"
    ):
        """
        Initialize AWS connection service.
        
        Args:
            access_key_id: AWS Access Key ID
            secret_access_key: AWS Secret Access Key
            region: AWS region
        """
        self.access_key_id = access_key_id
        self.secret_access_key = secret_access_key
        self.region = region
        self.s3_client = None
    
    def create_client(self) -> boto3.client:
        """
        Create and return an S3 client.
        
        Returns:
            Configured boto3 S3 client
        """
        if not self.s3_client:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=self.access_key_id,
                aws_secret_access_key=self.secret_access_key,
                region_name=self.region
            )
        return self.s3_client
    
    def test_connection(self, bucket: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Test S3 connection with comprehensive checks.
        
        Performs these checks:
        1. Credentials are valid
        2. Bucket exists
        3. Can list objects
        4. Can read objects (if any exist)
        
        Args:
            bucket: S3 bucket name to test
            
        Returns:
            Tuple of (success: bool, result: dict)
        """
        logger.info(
            "Testing AWS S3 connection",
            extra={
                "bucket": bucket,
                "region": self.region,
                "access_key_id": self.access_key_id[:8] + "..."  # Log partial key only
            }
        )
        
        try:
            client = self.create_client()
            
            # Test 1: Check if bucket exists
            bucket_exists = self._check_bucket_exists(client, bucket)
            if not bucket_exists:
                return False, {
                    "success": False,
                    "error": "BucketNotFound",
                    "message": f"Bucket '{bucket}' does not exist or you don't have access to it",
                    "suggestion": "Verify the bucket name and ensure your IAM user has s3:ListBucket permission",
                    "bucket": bucket,
                    "bucket_exists": False,
                    "can_list": False,
                    "timestamp": datetime.utcnow()
                }
            
            # Test 2: Try to list objects
            can_list, object_count = self._test_list_objects(client, bucket)
            
            # Test 3: Try to read an object (if any exist)
            can_read = False
            if object_count > 0:
                can_read = self._test_read_object(client, bucket)
            
            # Success!
            logger.info(
                "AWS S3 connection successful",
                extra={
                    "bucket": bucket,
                    "object_count": object_count,
                    "can_read": can_read
                }
            )
            
            return True, {
                "success": True,
                "message": f"Successfully connected to AWS S3 bucket '{bucket}'",
                "bucket": bucket,
                "bucket_exists": True,
                "can_list": can_list,
                "can_read": can_read,
                "object_count": object_count,
                "timestamp": datetime.utcnow()
            }
            
        except NoCredentialsError:
            return self._error_response(
                "NoCredentials",
                "No AWS credentials provided",
                "Provide access_key_id and secret_access_key in the request"
            )
        
        except PartialCredentialsError:
            return self._error_response(
                "PartialCredentials",
                "Incomplete AWS credentials",
                "Both access_key_id and secret_access_key are required"
            )
        
        except ClientError as e:
            error_code = e.response['Error']['Code']
            
            if error_code == 'InvalidAccessKeyId':
                return self._error_response(
                    "InvalidCredentials",
                    "The AWS Access Key ID you provided does not exist",
                    "Check your AWS_ACCESS_KEY_ID - it should be 20 characters starting with 'AKIA'"
                )
            
            elif error_code == 'SignatureDoesNotMatch':
                return self._error_response(
                    "InvalidCredentials",
                    "The AWS Secret Access Key you provided is incorrect",
                    "Check your AWS_SECRET_ACCESS_KEY - it should be 40 characters"
                )
            
            elif error_code == 'AccessDenied':
                return self._error_response(
                    "AccessDenied",
                    f"Access denied to bucket '{bucket}'",
                    "Verify your IAM user has the required S3 permissions (s3:ListBucket, s3:GetObject)"
                )
            
            else:
                return self._error_response(
                    error_code,
                    str(e),
                    "Check AWS service status and your credentials"
                )
        
        except EndpointConnectionError:
            return self._error_response(
                "ConnectionError",
                f"Could not connect to AWS S3 in region '{self.region}'",
                "Check your internet connection and verify the region is correct"
            )
        
        except Exception as e:
            logger.exception("Unexpected error during AWS connection test")
            return self._error_response(
                "UnexpectedError",
                str(e),
                "Check logs for details"
            )
    
    def _check_bucket_exists(self, client: boto3.client, bucket: str) -> bool:
        """Check if bucket exists and is accessible."""
        try:
            client.head_bucket(Bucket=bucket)
            return True
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code in ['404', 'NoSuchBucket']:
                return False
            raise  # Re-raise other errors
    
    def _test_list_objects(self, client: boto3.client, bucket: str) -> Tuple[bool, int]:
        """Test listing objects in bucket."""
        try:
            response = client.list_objects_v2(Bucket=bucket, MaxKeys=1000)
            object_count = response.get('KeyCount', 0)
            return True, object_count
        except ClientError:
            return False, 0
    
    def _test_read_object(self, client: boto3.client, bucket: str) -> bool:
        """Test reading first object in bucket."""
        try:
            # List first object
            response = client.list_objects_v2(Bucket=bucket, MaxKeys=1)
            if 'Contents' not in response:
                return False
            
            first_key = response['Contents'][0]['Key']
            
            # Try to read metadata (head_object is cheaper than get_object)
            client.head_object(Bucket=bucket, Key=first_key)
            return True
        except ClientError:
            return False
    
    def _error_response(
        self,
        error: str,
        message: str,
        suggestion: str
    ) -> Tuple[bool, Dict[str, Any]]:
        """Format error response."""
        logger.error(
            "AWS connection test failed",
            extra={
                "error": error,
                "message": message
            }
        )
        
        return False, {
            "success": False,
            "error": error,
            "message": message,
            "suggestion": suggestion,
            "timestamp": datetime.utcnow()
        }
