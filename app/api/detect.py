"""
Table Format Detection API Router.

Provides endpoints to automatically detect lakehouse table formats.

Why This Matters:
- Auto-detection means users don't specify format
- Routes to correct metadata reader
- Prevents misconfiguration errors
"""

from fastapi import APIRouter, status, HTTPException

from app.api.schemas import DetectFormatRequest, DetectFormatResponse
from app.metadata.format_detector import FormatDetector
from app.core.logger import get_logger

logger = get_logger()
router = APIRouter()


@router.post(
    "",
    response_model=DetectFormatResponse,
    status_code=status.HTTP_200_OK,
    summary="Detect table format automatically",
    description=(
        "Automatically detects lakehouse table format by inspecting storage layout.\n\n"
        "Supported formats:\n"
        "- **Delta Lake**: Looks for `_delta_log/` directory\n"
        "- **Apache Iceberg**: Looks for `metadata/` directory\n"
        "- **Apache Hudi**: Looks for `.hoodie/` directory\n"
        "- **Parquet**: Plain .parquet files\n\n"
        "Returns format type, confidence level, and metadata location."
    )
)
async def detect_format(request: DetectFormatRequest):
    """
    Detect table format from storage layout.
    
    This endpoint inspects the file structure at the specified path
    to determine which lakehouse format is being used.
    
    Args:
        request: Detection request with storage location
        
    Returns:
        DetectFormatResponse with format details
        
    Raises:
        HTTPException if storage is inaccessible
    """
    logger.info(
        "Starting format detection",
        extra={
            "bucket": request.bucket,
            "path": request.path,
            "storage_type": request.storage_type
        }
    )
    
    # Create detector
    detector = FormatDetector(
        bucket=request.bucket,
        path=request.path,
        storage_type=request.storage_type,
        access_key=request.access_key,
        secret_key=request.secret_key,
        endpoint=request.endpoint,
        region=request.region
    )
    
    # Run detection
    success, result = detector.detect()
    
    if success:
        return DetectFormatResponse(**result)
    else:
        # Storage access error
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result
        )
