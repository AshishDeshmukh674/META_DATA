"""
Metadata Generation API Router (Phase 6).

Endpoints for generating and managing metadata snapshots using Spark.

Why Phase 6?
- Generates NEW metadata snapshots (vs Phase 5 which reads existing metadata)
- Uses Spark for production-grade extraction
- Stores snapshots at table location (co-located, portable)
- Enables snapshot comparison and version tracking

Endpoints:
1. POST /metadata/generate - Generate metadata snapshot using Spark
2. GET /metadata/snapshots/latest - Get latest snapshot for a table
3. GET /metadata/snapshots/list - List all snapshots for a table
4. POST /metadata/snapshots/diff - Compare two snapshots

Usage Flow:
1. User calls /metadata/generate
2. System auto-detects format (if not provided)
3. Spark engine extracts metadata
4. Snapshot manager saves to S3 at <table_path>/.metadata-snapshots/
5. Returns snapshot_id and location
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from app.api.schemas import (
    MetadataGenerateRequest,
    MetadataGenerateResponse,
    SnapshotListResponse,
    SnapshotInfo,
    SnapshotDiffRequest,
    SnapshotDiffResponse
)
from app.engines.spark_metadata_engine import SparkMetadataEngine
from app.storage.snapshot_manager import SnapshotManager
from app.metadata.format_detector import FormatDetector
from app.core.logger import get_logger

logger = get_logger()

router = APIRouter(prefix="/metadata")


@router.post("/generate", response_model=MetadataGenerateResponse)
async def generate_metadata(request: MetadataGenerateRequest) -> MetadataGenerateResponse:
    """
    Generate metadata snapshot using Spark.
    
    Process:
    1. Auto-detect table format if not provided (using Phase 4 detector)
    2. Use Spark to load table and extract metadata:
       - Schema (columns, types, nullability)
       - Partition information
       - File statistics (count, size)
       - Version info (Delta version, Iceberg snapshot, etc.)
    3. Generate unique snapshot_id (timestamp + uuid)
    4. Save metadata as JSON to S3 at:
       <table_path>/.metadata-snapshots/<snapshot_id>.json
    5. Return snapshot_id and storage location
    
    Why Spark?
    - Delta Lake: Native Spark support
    - Iceberg: Official Spark integration
    - Hudi: Spark is primary engine
    - Production-ready and battle-tested
    
    Example Request:
    ```json
    {
      "storage_type": "aws",
      "bucket": "metadataproject",
      "path": "test-data/sample-data/delta/sales_delta",
      "table_format": "delta",
      "force_refresh": false
    }
    ```
    
    Example Response:
    ```json
    {
      "success": true,
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
    ```
    """
    logger.info(
        f"Metadata generation requested",
        extra={
            "storage_type": request.storage_type,
            "bucket": request.bucket,
            "path": request.path,
            "format": request.table_format or "auto-detect",
            "convert_to_lakehouse": request.convert_to_lakehouse
        }
    )
    
    try:
        actual_path = request.path  # Path to use for metadata extraction
        table_format = request.table_format
        needs_conversion = False
        
        # Step 1: Determine if conversion is needed
        if request.convert_to_lakehouse:
            # User explicitly requested conversion
            logger.info("Explicit conversion requested")
            needs_conversion = True
            
            # Validate conversion parameters
            if not request.target_format:
                raise HTTPException(
                    status_code=400,
                    detail="target_format is required when convert_to_lakehouse=True"
                )
            if not request.source_format:
                raise HTTPException(
                    status_code=400,
                    detail="source_format is required when convert_to_lakehouse=True"
                )
            
            table_format = request.target_format
            
        elif request.table_format:
            # User specified desired format - check if it exists
            logger.info(f"Checking if {request.table_format} table exists at path")
            
            detector = FormatDetector(
                bucket=request.bucket,
                path=request.path,
                storage_type=request.storage_type
            )
            
            # Check if path is a direct file (ends with known extension)
            file_extensions = ['.csv', '.json', '.parquet', '.avro', '.orc']
            is_file_path = any(request.path.lower().endswith(ext) for ext in file_extensions)
            
            if is_file_path:
                # Direct file path - skip format check, go to raw data detection
                logger.info(f"Direct file path detected - checking for convertible raw data")
                raw_success, raw_result = detector.detect_raw_data()
                
                if raw_success:
                    logger.info(
                        f"Found raw {raw_result['format']} file - will auto-convert to {request.table_format}",
                        extra={"file_counts": raw_result.get('file_counts')}
                    )
                    needs_conversion = True
                    table_format = request.table_format
                    # Auto-detect source format from raw data
                    if not request.source_format:
                        request.source_format = raw_result['format']
                    if not request.target_format:
                        request.target_format = request.table_format
                else:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Could not read file at path '{request.path}'"
                    )
            else:
                # Directory path - check if table format exists
                format_exists = detector.check_format_exists(request.table_format)
                
                if format_exists:
                    logger.info(f"{request.table_format.upper()} table already exists - will generate new metadata snapshot")
                    table_format = request.table_format
                else:
                    logger.info(f"{request.table_format.upper()} table not found - checking for raw data to convert")
                    
                    # Check for raw data that can be converted
                    raw_success, raw_result = detector.detect_raw_data()
                    
                    if raw_success:
                        logger.info(
                            f"Found raw data in {raw_result['format']} format - will auto-convert to {request.table_format}",
                            extra={"file_counts": raw_result.get('file_counts')}
                        )
                        needs_conversion = True
                        table_format = request.table_format
                        # Auto-detect source format from raw data
                        if not request.source_format:
                            request.source_format = raw_result['format']
                        if not request.target_format:
                            request.target_format = request.table_format
                    else:
                        raise HTTPException(
                            status_code=404,
                            detail=f"No {request.table_format} table or convertible raw data found at path '{request.path}'"
                        )
        else:
            # No format specified - try auto-detection
            logger.info("No format specified - attempting auto-detection")
            detector = FormatDetector(
                bucket=request.bucket,
                path=request.path,
                storage_type=request.storage_type
            )
            success, detection_result = detector.detect()
            
            if success and detection_result.get('format') != 'unknown':
                table_format = detection_result['format']
                logger.info(f"Auto-detected format: {table_format}")
            else:
                raise HTTPException(
                    status_code=400,
                    detail="Could not detect table format. Please specify format explicitly."
                )
        
        # Step 1.5: Perform conversion if needed
        if needs_conversion:
            logger.info(
                f"Converting {request.source_format} to {table_format}",
                extra={
                    "source_path": request.path,
                    "target_format": table_format,
                    "partitions": request.partition_columns
                }
            )
            
            # Perform conversion
            engine = SparkMetadataEngine()
            conversion_result = engine.convert_to_lakehouse(
                storage_type=request.storage_type,
                bucket=request.bucket,
                source_path=request.path,
                source_format=request.source_format,
                target_format=table_format,
                target_path=None,  # Auto-generate target path
                partition_columns=request.partition_columns
            )
            
            logger.info(
                f"Conversion completed successfully",
                extra={
                    "target_path": conversion_result['target_path'],
                    "row_count": conversion_result['row_count']
                }
            )
            
            # Update path for metadata extraction
            # Extract bucket-relative path from s3a:// URL
            target_s3a = conversion_result['target_path']
            actual_path = target_s3a.split(f"s3a://{request.bucket}/")[1]
            
            logger.info(f"Will extract metadata from converted table at: {actual_path}")
            
        # Step 2: Extract metadata using Spark
        logger.info(f"Starting Spark metadata extraction for format: {table_format}")
        engine = SparkMetadataEngine()
        
        metadata = engine.extract_metadata(
            storage_type=request.storage_type,
            bucket=request.bucket,
            path=actual_path,
            table_format=table_format
        )
        
        logger.info(f"Metadata extracted successfully, snapshot_id: {metadata['snapshot_id']}")
        
        # Step 3: Save snapshot to S3
        logger.info("Saving snapshot to S3...")
        snapshot_manager = SnapshotManager()
        
        snapshot_location = snapshot_manager.save_snapshot(
            storage_type=request.storage_type,
            bucket=request.bucket,
            path=actual_path,
            snapshot_id=metadata['snapshot_id'],
            metadata=metadata
        )
        
        logger.info(f"Snapshot saved to: {snapshot_location}")
        
        # Step 4: Build response with summary
        metadata_summary = {
            "column_count": len(metadata['schema']['fields']),
            "file_count": metadata['files'].get('file_count', 0),
            "total_size_bytes": metadata['files'].get('total_size_bytes', 0)
        }
        
        return MetadataGenerateResponse(
            success=True,
            snapshot_id=metadata['snapshot_id'],
            table_path=metadata['table_path'],
            table_format=metadata['table_format'],
            generated_at=metadata['generated_at'],
            snapshot_location=snapshot_location,
            metadata_summary=metadata_summary
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Metadata generation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate metadata: {str(e)}"
        )


@router.get("/snapshots/latest", response_model=dict)
async def get_latest_snapshot(
    storage_type: str = Query(..., description="Storage type (aws or minio)", regex="^(aws|minio)$"),
    bucket: str = Query(..., description="S3 bucket name", min_length=3),
    path: str = Query(..., description="Path to table within bucket")
):
    """
    Get the most recent metadata snapshot for a table.
    
    Returns the full metadata JSON from the latest snapshot.
    
    Example:
    ```
    GET /metadata/snapshots/latest?storage_type=aws&bucket=metadataproject&path=test-data/sample-data/delta/sales_delta
    ```
    
    Response:
    ```json
    {
      "success": true,
      "snapshot_id": "snapshot_20260208_090000_ghi78901",
      "table_path": "s3a://metadataproject/test-data/sample-data/delta/sales_delta",
      "generated_at": "2026-02-08T09:00:00Z",
      "schema": {...},
      "partitions": {...},
      "files": {...},
      "version_info": {...}
    }
    ```
    """
    logger.info(
        f"Latest snapshot requested",
        extra={
            "storage_type": storage_type,
            "bucket": bucket,
            "path": path
        }
    )
    
    try:
        snapshot_manager = SnapshotManager()
        snapshot = snapshot_manager.get_latest_snapshot(
            storage_type=storage_type,
            bucket=bucket,
            path=path
        )
        
        if not snapshot:
            raise HTTPException(
                status_code=404,
                detail=f"No snapshots found for table at {bucket}/{path}"
            )
        
        logger.info(f"Latest snapshot retrieved: {snapshot['snapshot_id']}")
        return {"success": True, **snapshot}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get latest snapshot: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve latest snapshot: {str(e)}"
        )


@router.get("/snapshots/list", response_model=SnapshotListResponse)
async def list_snapshots(
    storage_type: str = Query(..., description="Storage type (aws or minio)", regex="^(aws|minio)$"),
    bucket: str = Query(..., description="S3 bucket name", min_length=3),
    path: str = Query(..., description="Path to table within bucket")
) -> SnapshotListResponse:
    """
    List all metadata snapshots for a table.
    
    Returns snapshots sorted by timestamp (newest first).
    
    Example:
    ```
    GET /metadata/snapshots/list?storage_type=aws&bucket=metadataproject&path=test-data/sample-data/delta/sales_delta
    ```
    
    Response:
    ```json
    {
      "success": true,
      "table_path": "s3://metadataproject/test-data/sample-data/delta/sales_delta",
      "snapshot_count": 3,
      "snapshots": [
        {
          "snapshot_id": "snapshot_20260208_090000_ghi78901",
          "timestamp": "2026-02-08T09:00:00Z",
          "size_bytes": 15234,
          "s3_key": "test-data/sample-data/delta/sales_delta/.metadata-snapshots/snapshot_20260208_090000_ghi78901.json"
        },
        ...
      ]
    }
    ```
    """
    logger.info(
        f"Snapshot list requested",
        extra={
            "storage_type": storage_type,
            "bucket": bucket,
            "path": path
        }
    )
    
    try:
        snapshot_manager = SnapshotManager()
        snapshots = snapshot_manager.list_snapshots(
            storage_type=storage_type,
            bucket=bucket,
            path=path
        )
        
        table_path = f"s3://{bucket}/{path}"
        
        logger.info(f"Found {len(snapshots)} snapshots")
        
        return SnapshotListResponse(
            success=True,
            table_path=table_path,
            snapshot_count=len(snapshots),
            snapshots=[SnapshotInfo(**snap) for snap in snapshots]
        )
        
    except Exception as e:
        logger.error(f"Failed to list snapshots: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list snapshots: {str(e)}"
        )


@router.post("/snapshots/diff", response_model=SnapshotDiffResponse)
async def compare_snapshots(request: SnapshotDiffRequest) -> SnapshotDiffResponse:
    """
    Compare two metadata snapshots to see what changed.
    
    Shows differences in:
    - Schema: Added/removed columns, type changes
    - Files: File count changes, size changes
    - Partitions: Added/removed partitions (future)
    
    Example Request:
    ```json
    {
      "storage_type": "aws",
      "bucket": "metadataproject",
      "path": "test-data/sample-data/delta/sales_delta",
      "snapshot_id_1": "snapshot_20260207_173045_a1b2c3d4",
      "snapshot_id_2": "snapshot_20260208_090000_ghi78901"
    }
    ```
    
    Example Response:
    ```json
    {
      "success": true,
      "snapshot1_id": "snapshot_20260207_173045_a1b2c3d4",
      "snapshot2_id": "snapshot_20260208_090000_ghi78901",
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
      "file_changes": {
        "file_count_change": 15,
        "size_change_bytes": 234567890
      }
    }
    ```
    
    Use Cases:
    - Track schema evolution over time
    - See data growth (file count, size)
    - Audit table changes
    - Detect breaking changes before deployment
    """
    logger.info(
        f"Snapshot comparison requested",
        extra={
            "snapshot_id_1": request.snapshot_id_1,
            "snapshot_id_2": request.snapshot_id_2
        }
    )
    
    try:
        snapshot_manager = SnapshotManager()
        
        # Load both snapshots
        snapshot1 = snapshot_manager._load_snapshot_content(
            storage_type=request.storage_type,
            bucket=request.bucket,
            path=request.path,
            snapshot_id=request.snapshot_id_1
        )
        
        snapshot2 = snapshot_manager._load_snapshot_content(
            storage_type=request.storage_type,
            bucket=request.bucket,
            path=request.path,
            snapshot_id=request.snapshot_id_2
        )
        
        # Compare snapshots
        comparison = snapshot_manager.compare_snapshots(snapshot1, snapshot2)
        
        logger.info("Snapshot comparison completed successfully")
        
        return SnapshotDiffResponse(
            success=True,
            snapshot1_id=comparison['snapshot1_id'],
            snapshot2_id=comparison['snapshot2_id'],
            snapshot1_timestamp=comparison.get('snapshot1_timestamp'),
            snapshot2_timestamp=comparison.get('snapshot2_timestamp'),
            schema_changes=comparison['schema_changes'],
            data_changes=comparison.get('data_changes'),
            file_changes=comparison['file_changes'],
            version_changes=comparison.get('version_changes')
        )
        
    except Exception as e:
        logger.error(f"Snapshot comparison failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to compare snapshots: {str(e)}"
        )
