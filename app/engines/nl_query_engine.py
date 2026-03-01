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
        
        if not api_key:
            raise ValueError(
                "GROQ_API_KEY not set. Add it to .env file:\n"
                "GROQ_API_KEY=your_api_key_here\n"
                "Get a free key from: https://console.groq.com/keys"
            )
        
        self.client = Groq(api_key=api_key)
        logger.info(f"Groq client initialized successfully")
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
1. "query" - Execute SELECT query to retrieve data
2. "update" - Execute UPDATE query to modify existing data
3. "insert" - Execute INSERT query to add new data
4. "delete" - Execute DELETE query to remove data
5. "list_snapshots" - List available data versions
6. "table_info" - Get table schema/metadata
7. "test_connection" - Test Trino connection
8. "sync_table" - Register table in Trino

RULES FOR SQL GENERATION:
1. ALWAYS use "query_table" as the table name in SQL (the actual table will be loaded and registered with this name)
2. Always use exact column names from schema (case-sensitive)
3. For SELECT queries: Use LIMIT clause for safety (default: 100)
4. For UPDATE/DELETE: Always include WHERE clause for safety (no WHERE = error)
5. For aggregations: always include GROUP BY
6. For INSERT: Include all required columns
7. Keep queries simple and efficient
8. For write operations (UPDATE/INSERT/DELETE): operation must be "update", "insert", or "delete"

RESPONSE FORMAT (JSON):
{{
  "operation": "query|update|insert|delete|list_snapshots|table_info|test_connection|sync_table",
  "sql": "SELECT ... FROM query_table WHERE ..." OR "UPDATE query_table SET ... WHERE ..." OR "INSERT INTO query_table VALUES ..." OR "DELETE FROM query_table WHERE ...",
  "parameters": {{
    "columns": ["col1", "col2"],  // For simple queries
    "filter": "age > 25",  // WHERE clause
    "limit": 100,
    "is_destructive": true  // For UPDATE/DELETE operations
  }},
  "explanation": "I will execute a query to ...",
  "suggested_table": "table_name"  // If user didn't specify
}}

EXAMPLES:

User: "Show me all customers from Mumbai"
Response:
{{
  "operation": "query",
  "sql": "SELECT * FROM query_table WHERE City = 'Mumbai' LIMIT 100",
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
  "sql": "SELECT City, COUNT(*) as count FROM query_table GROUP BY City",
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
  "sql": "SELECT * FROM query_table LIMIT 5",
  "parameters": {{"limit": 5}},
  "explanation": "Selecting first 5 customer records"
}}

User: "Give me customers with email containing gmail"
Response:
{{
  "operation": "query",
  "sql": "SELECT * FROM query_table WHERE Email LIKE '%gmail%' LIMIT 100",
  "parameters": {{
    "filter": "Email LIKE '%gmail%'",
    "limit": 100
  }},
  "explanation": "Filtering customers whose email contains 'gmail'"
}}

User: "Update name to 'John Doe' where customer id is C001"
Response:
{{
  "operation": "update",
  "sql": "UPDATE query_table SET Name = 'John Doe' WHERE CustomerId = 'C001'",
  "parameters": {{
    "filter": "CustomerId = 'C001'",
    "is_destructive": true
  }},
  "explanation": "Updating customer name where CustomerId is C001"
}}

User: "Delete customer with id C999"
Response:
{{
  "operation": "delete",
  "sql": "DELETE FROM query_table WHERE CustomerId = 'C999'",
  "parameters": {{
    "filter": "CustomerId = 'C999'",
    "is_destructive": true
  }},
  "explanation": "Deleting customer record where CustomerId is C999"
}}

User: "Insert a new customer: id C100, name Sarah, email sarah@example.com"
Response:
{{
  "operation": "insert",
  "sql": "INSERT INTO query_table (CustomerId, Name, Email) VALUES ('C100', 'Sarah', 'sarah@example.com')",
  "parameters": {{
    "is_destructive": true
  }},
  "explanation": "Inserting new customer record with id C100"
}}

User: "Change email to newemail@test.com for all customers in Mumbai"
Response:
{{
  "operation": "update",
  "sql": "UPDATE query_table SET Email = 'newemail@test.com' WHERE City = 'Mumbai'",
  "parameters": {{
    "filter": "City = 'Mumbai'",
    "is_destructive": true
  }},
  "explanation": "Updating email for all customers in Mumbai city"
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
