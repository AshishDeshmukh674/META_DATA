"""
Natural Language Query Engine using Groq API.

This module converts natural language queries into structured operations:
1. SQL queries (for data retrieval)
2. Snapshot operations (list, compare)
3. Table operations (schema, info)
4. Connection tests

Why Groq?
- Fast inference (100ms for SQL generation)
- Supports Llama 3.3 70B (excellent for SQL generation)
- Free tier available
- Simple API

Examples:
- "Show me all customers from Mumbai" → SQL query
- "List all snapshots for customer_data" → Snapshot list operation
- "What columns are in the customer table?" → Table info operation
"""

from typing import Dict, Any, Optional, List
import json
from groq import Groq
from app.core.settings import settings
from app.core.logger import get_logger

logger = get_logger()


class NaturalLanguageQueryEngine:
    """
    Converts natural language to structured database operations.
    
    Uses Groq LLM to:
    1. Understand user intent
    2. Extract entities (table names, columns, filters)
    3. Generate SQL or operation parameters
    4. Route to appropriate endpoint
    """
    
    def __init__(self):
        """Initialize Groq client."""
        api_key = settings.groq_api_key
        print(f"[NL ENGINE DEBUG] Settings API key from import: {bool(api_key)}", flush=True)
        if api_key:
            print(f"[NL ENGINE DEBUG] Key prefix: {api_key[:20]}...", flush=True)
        
        logger.info(f"Initializing Groq client with key: {api_key[:15] if api_key else 'NONE'}...")
        
        if not api_key:
            raise ValueError(
                "GROQ_API_KEY not set. Add it to .env file:\n"
                "GROQ_API_KEY=your_api_key_here\n\n"
                "Get your free API key from: https://console.groq.com/"
            )
        
        self.client = Groq(api_key=api_key)
        logger.info(f"Groq client initialized. API key starts with: {self.client.api_key[:15]}")
        self.model = settings.groq_model
        self.temperature = settings.groq_temperature
        self.max_tokens = settings.groq_max_tokens
    
    def process_query(
        self,
        natural_query: str,
        storage_type: str = "aws",
        bucket: str = None,
        table_path: str = None,
        available_tables: Optional[List[str]] = None,
        table_schema: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Process natural language query and return structured operation.
        
        Args:
            natural_query: User's question in natural language
            storage_type: Storage backend (aws, minio)
            bucket: S3 bucket name
            table_path: Path to table in bucket
            available_tables: List of available tables (optional)
            table_schema: Dict of column_name -> data_type (optional)
        
        Returns:
            Dict with:
            - operation: str (query, list_snapshots, table_info, etc.)
            - sql: str (if operation is query)
            - parameters: dict (additional parameters for operation)
            - explanation: str (human-readable explanation)
        """
        try:
            logger.info(
                "Processing natural language query",
                extra={"query": natural_query[:100]}
            )
            
            # Build context for LLM
            context = self._build_context(
                storage_type=storage_type,
                bucket=bucket,
                table_path=table_path,
                available_tables=available_tables,
                table_schema=table_schema
            )
            
            # Generate system prompt
            system_prompt = self._create_system_prompt(context)
            
            # Debug: verify API key before calling
            logger.info(f"About to call Groq API. Client API key: {self.client.api_key[:20]}...")
            
            # Call Groq API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": natural_query}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"}  # Force JSON output
            )
            
            # Parse response
            result = json.loads(response.choices[0].message.content)
            
            logger.info(
                "Natural language query processed",
                extra={
                    "operation": result.get("operation"),
                    "has_sql": "sql" in result
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Natural language processing failed: {e}", exc_info=True)
            raise
    
    def _build_context(
        self,
        storage_type: str,
        bucket: Optional[str],
        table_path: Optional[str],
        available_tables: Optional[List[str]],
        table_schema: Optional[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Build context information for LLM."""
        context = {
            "storage_type": storage_type,
            "bucket": bucket,
            "table_path": table_path
        }
        
        if available_tables:
            context["available_tables"] = available_tables
        
        if table_schema:
            context["table_schema"] = table_schema
            context["columns"] = list(table_schema.keys())
        
        return context
    
    def _create_system_prompt(self, context: Dict[str, Any]) -> str:
        """
        Create system prompt for Groq LLM.
        
        This prompt instructs the LLM to:
        1. Identify operation type
        2. Generate SQL if needed
        3. Extract parameters
        4. Return JSON response
        """
        
        schema_info = ""
        if context.get("table_schema"):
            schema_lines = [f"  - {col}: {dtype}" for col, dtype in context["table_schema"].items()]
            schema_info = f"""
Current Table Schema:
{chr(10).join(schema_lines)}

Use these exact column names in SQL queries.
"""
        
        available_tables_info = ""
        if context.get("available_tables"):
            available_tables_info = f"""
Available Tables:
{chr(10).join(f"  - {table}" for table in context["available_tables"])}
"""
        
        system_prompt = f"""You are a SQL expert for a data lakehouse platform. Convert natural language queries into structured operations.

CONTEXT:
- Storage: {context.get('storage_type', 'aws')}
- Bucket: {context.get('bucket', 'not specified')}
- Table Path: {context.get('table_path', 'not specified')}
{schema_info}
{available_tables_info}

OPERATION TYPES:
1. "query" - Execute SQL query on data
2. "list_snapshots" - List available data versions
3. "table_info" - Get table schema/metadata
4. "test_connection" - Test Trino connection
5. "sync_table" - Register table in Trino

RULES FOR SQL GENERATION:
1. For Trino queries: Use format "delta.default.table_name" or "delta.default.{{table}}"
2. For Spark snapshot queries: Use "{{table}}" placeholder (will be replaced with actual path)
3. Always use exact column names from schema (case-sensitive)
4. Use LIMIT clause for safety (default: 100)
5. For aggregations: always include GROUP BY
6. For time travel: set operation="query_snapshot" and include snapshot_id

RESPONSE FORMAT (JSON):
{{
  "operation": "query|list_snapshots|table_info|test_connection|sync_table|query_snapshot",
  "sql": "SELECT ... FROM ... WHERE ...",  // Only if operation is query or query_snapshot
  "parameters": {{
    "columns": ["col1", "col2"],  // For simple queries
    "filter": "age > 25",  // WHERE clause
    "limit": 100,
    "snapshot_id": "snapshot_xxx"  // For time travel queries
  }},
  "explanation": "I will execute a query to ...",
  "suggested_table": "table_name",  // If user didn't specify
  "needs_sync": true  // If table needs registration in Trino first
}}

EXAMPLES:

User: "Show me all customers from Mumbai"
Response:
{{
  "operation": "query",
  "sql": "SELECT * FROM delta.default.customer_data_delta WHERE City = 'Mumbai' LIMIT 100",
  "parameters": {{
    "filter": "City = 'Mumbai'",
    "limit": 100
  }},
  "explanation": "Selecting all customers where city is Mumbai"
}}

User: "Count customers by city"
Response:
{{
  "operation": "query",
  "sql": "SELECT City, COUNT(*) as count FROM delta.default.customer_data_delta GROUP BY City",
  "parameters": {{}},
  "explanation": "Counting customers grouped by city"
}}

User: "List all snapshots"
Response:
{{
  "operation": "list_snapshots",
  "parameters": {{}},
  "explanation": "Listing all available snapshots/versions of the table"
}}

User: "What columns does this table have?"
Response:
{{
  "operation": "table_info",
  "parameters": {{}},
  "explanation": "Retrieving table schema and column information"
}}

User: "Show me top 5 customers"
Response:
{{
  "operation": "query",
  "sql": "SELECT * FROM delta.default.customer_data_delta LIMIT 5",
  "parameters": {{"limit": 5}},
  "explanation": "Selecting first 5 customer records"
}}

User: "Give me customers with email containing gmail"
Response:
{{
  "operation": "query",
  "sql": "SELECT * FROM delta.default.customer_data_delta WHERE Email LIKE '%gmail%' LIMIT 100",
  "parameters": {{
    "filter": "Email LIKE '%gmail%'",
    "limit": 100
  }},
  "explanation": "Filtering customers whose email contains 'gmail'"
}}

NOW PROCESS THE USER'S QUERY AND RETURN JSON.
"""
        
        return system_prompt


class NLQueryResult:
    """Structured result from natural language processing."""
    
    def __init__(self, llm_response: Dict[str, Any]):
        """
        Parse LLM response into structured result.
        
        Args:
            llm_response: JSON response from Groq LLM
        """
        self.operation = llm_response.get("operation", "query")
        self.sql = llm_response.get("sql")
        self.parameters = llm_response.get("parameters", {})
        self.explanation = llm_response.get("explanation", "")
        self.suggested_table = llm_response.get("suggested_table")
        self.needs_sync = llm_response.get("needs_sync", False)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "operation": self.operation,
            "sql": self.sql,
            "parameters": self.parameters,
            "explanation": self.explanation,
            "suggested_table": self.suggested_table,
            "needs_sync": self.needs_sync
        }
    
    def is_query(self) -> bool:
        """Check if this is a SQL query operation."""
        return self.operation in ["query", "query_snapshot"]
    
    def is_snapshot_operation(self) -> bool:
        """Check if this is a snapshot-related operation."""
        return self.operation == "list_snapshots"
    
    def is_table_operation(self) -> bool:
        """Check if this is a table metadata operation."""
        return self.operation == "table_info"
