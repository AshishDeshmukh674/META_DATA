"""
Metadata API Router

Endpoints for exploring table metadata:
- GET /metadata/schema - Get table schema
- GET /metadata/partitions - Get partition information  
- GET /metadata/snapshots - Get snapshot/version history
- GET /metadata/files - Get data file listing

Supports all formats: Delta Lake, Iceberg, Hudi, Parquet
"""

from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any

from app.api.schemas import MetadataRequest, MetadataResponse
from app.metadata.format_detector import FormatDetector
from app.metadata.delta_reader import DeltaReader
from app.metadata.iceberg_reader import IcebergReader
from app.metadata.hudi_reader import HudiReader
from app.metadata.parquet_reader import ParquetReader
from app.core.logger import get_logger

logger = get_logger()
router = APIRouter(prefix="/metadata", tags=["metadata"])


def get_reader(format: str, bucket: str, path: str, storage_type: str):
    """Factory function to get the appropriate metadata reader."""
    readers = {
        "delta": DeltaReader,
        "iceberg": IcebergReader,
        "hudi": HudiReader,
        "parquet": ParquetReader
    }
    
    reader_class = readers.get(format.lower())
    if not reader_class:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported table format: {format}. Supported: delta, iceberg, hudi, parquet"
        )
    
    return reader_class(bucket=bucket, path=path, storage_type=storage_type)


@router.post("/schema", response_model=MetadataResponse)
async def get_schema(
    request: MetadataRequest = Body(
        ...,
        example={
            "storage_type": "aws",
            "bucket": "metadataproject",
            "path": "test-data/sample-data/delta/sales_delta",
            "format": "delta"
        }
    )
) -> MetadataResponse:
    """
    Get table schema (column names, types, etc.)
    
    If format is not provided, will auto-detect from storage.
    
    **Supported Formats:**
    - **Delta Lake**: Reads from `_delta_log/*.json` files
    - **Iceberg**: Reads from `metadata/*.json` files
    - **Hudi**: Reads from `.hoodie/hoodie.properties`
    - **Parquet**: Reads directly from `.parquet` files using PyArrow
    
    **Example Request (Delta Lake):**
    ```json
    {
      "storage_type": "aws",
      "bucket": "metadataproject",
      "path": "test-data/sample-data/delta/sales_delta",
      "format": "delta"
    }
    ```
    """
    logger.info(f"Schema request for {request.storage_type}://{request.bucket}/{request.path}")
    
    try:
        # Auto-detect format if not provided
        if not request.format:
            logger.info("Format not provided, auto-detecting...")
            detector = FormatDetector(
                bucket=request.bucket,
                path=request.path,
                storage_type=request.storage_type
            )
            success, detection_result = detector.detect()
            
            if not success or detection_result.get('format') == 'unknown':
                raise HTTPException(
                    status_code=404,
                    detail="Could not detect table format. Please specify format explicitly."
                )
            
            request.format = detection_result['format']
            logger.info(f"Auto-detected format: {request.format}")
        
        # Get appropriate reader
        reader = get_reader(
            format=request.format,
            bucket=request.bucket,
            path=request.path,
            storage_type=request.storage_type
        )
        
        # Read schema
        schema_data = reader.get_schema()
        
        if not schema_data.get('success'):
            raise HTTPException(
                status_code=500,
                detail=schema_data.get('error', 'Failed to read schema')
            )
        
        return MetadataResponse(
            success=True,
            table_format=request.format,
            data=schema_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reading schema: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to read schema: {str(e)}"
        )


@router.post("/partitions", response_model=MetadataResponse)
async def get_partitions(
    request: MetadataRequest = Body(
        ...,
        example={
            "storage_type": "aws",
            "bucket": "metadataproject",
            "path": "test-data/sample-data/delta/sales_delta",
            "format": "delta"
        }
    )
) -> MetadataResponse:
    """
    Get table partition information.
    
    Returns partition columns and values (if available).
    
    **Delta Lake**: Reads partition info from transaction log  
    **Iceberg**: Reads partition specs from metadata  
    **Hudi**: Reads from hoodie.properties  
    **Parquet**: Detects from Hive-style directory structure
    """
    logger.info(f"Partitions request for {request.storage_type}://{request.bucket}/{request.path}")
    
    try:
        # Auto-detect format if not provided
        if not request.format:
            detector = FormatDetector(
                bucket=request.bucket,
                path=request.path,
                storage_type=request.storage_type
            )
            success, detection_result = detector.detect()
            
            if not success or detection_result.get('format') == 'unknown':
                raise HTTPException(
                    status_code=404,
                    detail="Could not detect table format. Please specify format explicitly."
                )
            
            request.format = detection_result['format']
        
        # Get appropriate reader
        reader = get_reader(
            format=request.format,
            bucket=request.bucket,
            path=request.path,
            storage_type=request.storage_type
        )
        
        # Read partitions
        partition_data = reader.get_partitions()
        
        if not partition_data.get('success'):
            raise HTTPException(
                status_code=500,
                detail=partition_data.get('error', 'Failed to read partitions')
            )
        
        return MetadataResponse(
            success=True,
            table_format=request.format,
            data=partition_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reading partitions: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to read partitions: {str(e)}"
        )


@router.post("/snapshots", response_model=MetadataResponse)
async def get_snapshots(
    request: MetadataRequest = Body(
        ...,
        example={
            "storage_type": "aws",
            "bucket": "metadataproject",
            "path": "test-data/sample-data/delta/sales_delta",
            "format": "delta"
        }
    )
) -> MetadataResponse:
    """
    Get table snapshot/version history.
    
    Shows evolution of the table over time.
    
    **Delta Lake**: Each JSON file = 1 version  
    **Iceberg**: Explicit snapshots with IDs  
    **Hudi**: Timeline of commits  
    **Parquet**: Files by modification time (no real snapshots)
    """
    logger.info(f"Snapshots request for {request.storage_type}://{request.bucket}/{request.path}")
    
    try:
        # Auto-detect format if not provided
        if not request.format:
            detector = FormatDetector(
                bucket=request.bucket,
                path=request.path,
                storage_type=request.storage_type
            )
            success, detection_result = detector.detect()
            
            if not success or detection_result.get('format') == 'unknown':
                raise HTTPException(
                    status_code=404,
                    detail="Could not detect table format. Please specify format explicitly."
                )
            
            request.format = detection_result['format']
        
        # Get appropriate reader
        reader = get_reader(
            format=request.format,
            bucket=request.bucket,
            path=request.path,
            storage_type=request.storage_type
        )
        
        # Read snapshots
        snapshot_data = reader.get_snapshots()
        
        if not snapshot_data.get('success'):
            raise HTTPException(
                status_code=500,
                detail=snapshot_data.get('error', 'Failed to read snapshots')
            )
        
        return MetadataResponse(
            success=True,
            table_format=request.format,
            data=snapshot_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reading snapshots: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to read snapshots: {str(e)}"
        )


@router.post("/files", response_model=MetadataResponse)
async def get_files(
    request: MetadataRequest = Body(
        ...,
        example={
            "storage_type": "aws",
            "bucket": "metadataproject",
            "path": "test-data/sample-data/delta/sales_delta",
            "format": "delta"
        }
    )
) -> MetadataResponse:
    """
    Get list of data files in the table.
    
    Returns file paths, sizes, and statistics.
    
    **Delta Lake**: Reconstructs state by replaying add/remove actions  
    **Iceberg**: Reads manifest lists (summary only in this phase)  
    **Hudi**: Lists .parquet files  
    **Parquet**: Lists all .parquet files with metadata
    """
    logger.info(f"Files request for {request.storage_type}://{request.bucket}/{request.path}")
    
    try:
        # Auto-detect format if not provided
        if not request.format:
            detector = FormatDetector(
                bucket=request.bucket,
                path=request.path,
                storage_type=request.storage_type
            )
            success, detection_result = detector.detect()
            
            if not success or detection_result.get('format') == 'unknown':
                raise HTTPException(
                    status_code=404,
                    detail="Could not detect table format. Please specify format explicitly."
                )
            
            request.format = detection_result['format']
        
        # Get appropriate reader
        reader = get_reader(
            format=request.format,
            bucket=request.bucket,
            path=request.path,
            storage_type=request.storage_type
        )
        
        # Read files
        files_data = reader.get_files()
        
        if not files_data.get('success'):
            raise HTTPException(
                status_code=500,
                detail=files_data.get('error', 'Failed to read files')
            )
        
        return MetadataResponse(
            success=True,
            table_format=request.format,
            data=files_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reading files: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to read files: {str(e)}"
        )
