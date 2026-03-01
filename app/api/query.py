"""
Query API Router

Endpoints for executing queries:
- POST /query/natural-language - Natural language to SQL query
- POST /query/execute - Direct SQL execution (if needed)

Supports Delta Lake, Iceberg, Hudi, Parquet via Spark
"""

from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel, Field
from typing import Optional, Any, List
import time

from app.engines.nl_query_engine import NaturalLanguageQueryEngine
from app.engines.spark_query_engine import SparkQueryEngine
from app.core.logger import get_logger

logger = get_logger()
router = APIRouter(prefix="/query", tags=["query"])


# ============================================================================
# Request/Response Models
# ============================================================================

class NLQueryRequest(BaseModel):
    """Natural language query request."""
    storage_type: str = Field(..., description="Storage type: aws or minio")
    bucket: str = Field(..., description="S3 bucket name")
    table_path: str = Field(..., description="Path to table within bucket")
    question: str = Field(..., description="Natural language question")
    
    class Config:
        json_schema_extra = {
            "example": {
                "storage_type": "aws",
                "bucket": "metadataproject",
                "table_path": "test-data/customer_data/customer_data_delta",
                "question": "Show me the top 10 customers by total purchases"
            }
        }


class NLQueryResponse(BaseModel):
    """Natural language query response."""
    success: bool = Field(..., description="Whether query succeeded")
    question: str = Field(..., description="Original question")
    generated_sql: str = Field(..., description="Generated SQL query")
    data: List[Any] = Field(..., description="Query results")
    columns: List[str] = Field(..., description="Column names")
    row_count: int = Field(..., description="Number of rows returned")
    execution_time_ms: int = Field(..., description="Total execution time in milliseconds")
    explanation: str = Field(..., description="Explanation of results")
    error: Optional[str] = Field(None, description="Error message if failed")


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/natural-language", response_model=NLQueryResponse)
async def natural_language_query(
    request: NLQueryRequest = Body(..., description="Natural language query request")
) -> NLQueryResponse:
    """
    Execute a natural language query against a table.
    
    This endpoint:
    1. Converts natural language to SQL using Groq AI
    2. Executes the query via Spark
    3. Returns results with explanation
    
    Example:
    ```json
    {
      "storage_type": "aws",
      "bucket": "metadataproject",
      "table_path": "test-data/customer_data/customer_data_delta",
      "question": "Show me the top 10 customers by total purchases"
    }
    ```
    """
    start_time = time.time()
    
    logger.info(
        f"Natural language query received",
        extra={
            "storage_type": request.storage_type,
            "bucket": request.bucket,
            "table_path": request.table_path,
            "question": request.question[:100]  # Truncate for logging
        }
    )
    
    try:
        # Step 1: Convert natural language to SQL using NL engine
        nl_engine = NaturalLanguageQueryEngine()
        
        logger.info("Converting natural language to SQL...")
        nl_result = nl_engine.process_query(
            natural_query=request.question,
            storage_type=request.storage_type,
            bucket=request.bucket,
            table_path=request.table_path
        )
        
        # nl_result is already a dict
        operation_type = nl_result.get("operation")
        
        # Check if operation is supported
        supported_operations = ["query", "update", "insert", "delete"]
        if operation_type not in supported_operations:
            # Handle non-supported operations
            logger.warning(f"Unsupported operation detected: {operation_type}")
            return NLQueryResponse(
                success=False,
                question=request.question,
                generated_sql="",
                data=[],
                columns=[],
                row_count=0,
                execution_time_ms=int((time.time() - start_time) * 1000),
                explanation=nl_result.get("explanation", "This question requires a different type of operation."),
                error=f"Operation '{operation_type}' not supported. Supported: {', '.join(supported_operations)}"
            )
        
        generated_sql = nl_result.get("sql", "")
        
        if not generated_sql:
            raise HTTPException(
                status_code=400,
                detail="Failed to generate SQL from question. Please rephrase your question."
            )
        
        logger.info(f"Generated SQL: {generated_sql}")
        
        # Step 2: Execute SQL using Spark
        query_engine = SparkQueryEngine()
        
        logger.info("Executing SQL query...")
        query_result = query_engine.execute_query(
            storage_type=request.storage_type,
            bucket=request.bucket,
            table_path=request.table_path,
            query=generated_sql,
            table_format="delta"  # Default to delta, can be auto-detected if needed
        )
        
        execution_time_ms = int((time.time() - start_time) * 1000)
        
        if not query_result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=f"Query execution failed: {query_result.get('error', 'Unknown error')}"
            )
        
        logger.info(
            f"Query executed successfully",
            extra={
                "operation": operation_type,
                "row_count": query_result.get("row_count", 0),
                "execution_time_ms": execution_time_ms
            }
        )
        
        # Step 3: Return results
        # For write operations, include success message in explanation
        explanation = nl_result.get("explanation", "Query executed successfully")
        if operation_type in ["update", "insert", "delete"]:
            result_message = query_result.get("message", "Operation completed")
            explanation = f"{explanation}. {result_message}"
        
        return NLQueryResponse(
            success=True,
            question=request.question,
            generated_sql=generated_sql,
            data=query_result.get("data", []),
            columns=query_result.get("columns", []),
            row_count=query_result.get("row_count", 0),
            execution_time_ms=execution_time_ms,
            explanation=explanation
        )
        
    except HTTPException:
        raise
    except Exception as e:
        execution_time_ms = int((time.time() - start_time) * 1000)
        logger.error(f"Natural language query failed: {e}", exc_info=True)
        
        return NLQueryResponse(
            success=False,
            question=request.question,
            generated_sql="",
            data=[],
            columns=[],
            row_count=0,
            execution_time_ms=execution_time_ms,
            explanation="",
            error=str(e)
        )
