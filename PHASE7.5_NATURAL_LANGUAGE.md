# Phase 7.5: Natural Language Query Interface

## 🎯 Overview

This enhancement adds **natural language querying** to the lakehouse platform. Users can now ask questions in plain English instead of writing SQL!

**Powered by**: Groq API (Llama 3.3 70B)

---

## ✨ What's New

### New Endpoint: `POST /query/natural`

Users can now ask questions like:
- "Show me all customers from Mumbai"
- "Count customers by city"
- "List all snapshots"
- "What columns does this table have?"

The system automatically:
1. Converts natural language → SQL (or appropriate operation)
2. Executes the query
3. Returns results with explanation

---

## 🚀 Setup Instructions

### 1. Install Groq SDK

```powershell
pip install groq==0.4.2
```

Or update all dependencies:
```powershell
pip install -r requirements.txt
```

### 2. Get Groq API Key

1. Go to: https://console.groq.com/keys
2. Sign up (free tier available)
3. Create an API key
4. Copy the key

### 3. Configure Environment

Add to your `.env` file:

```dotenv
# LLM Configuration (Phase 7.5)
GROQ_API_KEY=gsk_your_actual_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
GROQ_TEMPERATURE=0.1
GROQ_MAX_TOKENS=2000
```

### 4. Restart FastAPI

```powershell
docker-compose restart fastapi
```

---

## 📝 Usage Examples

### Example 1: Simple Data Retrieval

**Natural Language:**
```powershell
$body = @{
    query = "Show me all customers"
    storage_type = "aws"
    bucket = "metadataproject"
    table_path = "test-data/customer_data/customer_data_delta"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/query/natural" `
    -Method Post -ContentType "application/json" -Body $body
```

**Generated SQL:**
```sql
SELECT * FROM delta.default.customer_data_delta LIMIT 100
```

**Response:**
```json
{
  "success": true,
  "operation": "query",
  "sql": "SELECT * FROM delta.default.customer_data_delta LIMIT 100",
  "explanation": "Selecting all customer records with a default limit of 100",
  "row_count": 3,
  "columns": ["CustomerID", "Name", "Email", "City"],
  "data": [
    {"CustomerID": "1", "Name": "Alice", "Email": "alice@email.com", "City": "Mumbai"},
    {"CustomerID": "2", "Name": "Bob", "Email": "bob@email.com", "City": "Delhi"},
    {"CustomerID": "3", "Name": "Carol", "Email": "carol@email.com", "City": "Mumbai"}
  ],
  "execution_time_ms": 156,
  "engine": "trino"
}
```

---

### Example 2: Filtering

**Natural Language:**
```powershell
$body = @{
    query = "Show me customers from Mumbai"
    storage_type = "aws"
    bucket = "metadataproject"
    table_path = "test-data/customer_data/customer_data_delta"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/query/natural" `
    -Method Post -ContentType "application/json" -Body $body
```

**Generated SQL:**
```sql
SELECT * FROM delta.default.customer_data_delta WHERE City = 'Mumbai' LIMIT 100
```

**Response:** 2 rows (Alice and Carol)

---

### Example 3: Aggregation

**Natural Language:**
```powershell
$body = @{
    query = "Count customers by city"
    storage_type = "aws"
    bucket = "metadataproject"
    table_path = "test-data/customer_data/customer_data_delta"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/query/natural" `
    -Method Post -ContentType "application/json" -Body $body
```

**Generated SQL:**
```sql
SELECT City, COUNT(*) as count 
FROM delta.default.customer_data_delta 
GROUP BY City
```

**Response:**
```json
{
  "success": true,
  "operation": "query",
  "sql": "SELECT City, COUNT(*) as count FROM delta.default.customer_data_delta GROUP BY City",
  "explanation": "Counting customers grouped by city",
  "row_count": 2,
  "columns": ["City", "count"],
  "data": [
    {"City": "Mumbai", "count": 2},
    {"City": "Delhi", "count": 1}
  ],
  "execution_time_ms": 189,
  "engine": "trino"
}
```

---

### Example 4: Operations (No SQL)

**Natural Language:**
```powershell
$body = @{
    query = "List all snapshots"
    storage_type = "aws"
    bucket = "metadataproject"
    table_path = "test-data/customer_data/customer_data_delta"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/query/natural" `
    -Method Post -ContentType "application/json" -Body $body
```

**Response:**
```json
{
  "success": true,
  "operation": "list_snapshots",
  "explanation": "Listing all available snapshots/versions of the table",
  "snapshot_count": 4,
  "snapshots": [...]
}
```

---

### Example 5: Table Schema

**Natural Language:**
```powershell
$body = @{
    query = "What columns does this table have?"
    storage_type = "aws"
    bucket = "metadataproject"
    table_path = "test-data/customer_data/customer_data_delta"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/query/natural" `
    -Method Post -ContentType "application/json" -Body $body
```

**Response:**
```json
{
  "success": true,
  "operation": "table_info",
  "explanation": "Retrieving table schema and column information",
  "columns": [
    {"name": "CustomerID", "type": "varchar"},
    {"name": "Name", "type": "varchar"},
    {"name": "Email", "type": "varchar"},
    {"name": "City", "type": "varchar"}
  ]
}
```

---

### Example 6: Complex Queries

**Natural Language:**
```powershell
$body = @{
    query = "Show me customers from Mumbai with Gmail emails"
    storage_type = "aws"
    bucket = "metadataproject"
    table_path = "test-data/customer_data/customer_data_delta"
} | ConvertTo-Json
```

**Generated SQL:**
```sql
SELECT * FROM delta.default.customer_data_delta 
WHERE City = 'Mumbai' AND Email LIKE '%gmail%' 
LIMIT 100
```

---

## 🎯 Supported Query Types

### 1. Data Queries (SQL Generated)
- "Show me all customers"
- "Get top 10 records"
- "Find customers where age > 30"
- "List products with price > 100"
- "Show me customers from Mumbai with gmail"

### 2. Aggregations (SQL Generated)
- "Count customers by city"
- "How many customers are there?"
- "Sum of sales by region"
- "Average price per category"

### 3. Operations (No SQL)
- "List all snapshots"
- "Give me snapshots at this location"
- "What columns are in this table?"
- "Show me table schema"
- "Test connection to Trino"

---

## ⚙️ Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | string | **required** | Natural language question |
| `storage_type` | string | `"aws"` | Storage backend (aws, minio) |
| `bucket` | string | **required** | S3 bucket name |
| `table_path` | string | **required** | Path to table in bucket |
| `catalog` | string | `"delta"` | Trino catalog name |
| `schema_name` | string | `"default"` | Trino schema name |
| `use_trino` | boolean | `true` | Use Trino (fast) vs Spark (slow, time travel) |
| `auto_sync` | boolean | `true` | Auto-register table in Trino if needed |

---

## 🔄 How It Works

```
User Question
    ↓
"Show me customers from Mumbai"
    ↓
Groq API (Llama 3.3 70B)
    ↓
Intent Detection + SQL Generation
    ↓
{
  "operation": "query",
  "sql": "SELECT * FROM ... WHERE City = 'Mumbai'",
  "explanation": "Filtering customers by city"
}
    ↓
Auto-sync Table (if needed)
    ↓
Execute Query (Trino/Spark)
    ↓
Return Results + Explanation
```

**Processing Time:**
- LLM inference: ~100-200ms (Groq is fast!)
- Query execution: 100-500ms (Trino) or 30-60s (Spark)
- **Total**: ~200-700ms for most queries

---

## 🧠 LLM Configuration

### Model: `llama-3.3-70b-versatile`
- **Why this model?** Excellent at SQL generation, fast inference
- **Size:** 70B parameters
- **Speed:** ~100ms inference via Groq
- **Cost:** Free tier available (generous limits)

### Temperature: `0.1` (Low)
- **Why?** Consistent SQL generation
- Low temperature = deterministic output
- Same question → same SQL every time

### Max Tokens: `2000`
- **Why?** Enough for complex SQL + explanation
- Typical usage: 200-500 tokens

---

## 🔒 Security Notes

### 1. SQL Injection Protection
- LLM generates SQL but doesn't see user credentials
- All queries run through existing Trino/Spark engines
- Same security as manual SQL queries

### 2. API Key Security
- Store `GROQ_API_KEY` in `.env` (never commit!)
- Key is loaded at startup
- Not exposed in API responses

### 3. Query Limits
- Default LIMIT: 100 rows
- Max limit: 100,000 rows
- Prevents accidental massive queries

---

## 📊 Performance Comparison

| Query Method | Complexity | Speed | SQL Knowledge Required |
|--------------|------------|-------|------------------------|
| **Natural Language** | Easy | ~200-700ms | ❌ No |
| **Trino SQL** | Medium | ~100-500ms | ✅ Yes |
| **Snapshot (No SQL)** | Easy | ~30-60s | ❌ No |
| **Snapshot (SQL)** | Hard | ~30-60s | ✅ Yes |

---

## 🐛 Troubleshooting

### Error: "GROQ_API_KEY not set"

**Solution:**
1. Get API key from https://console.groq.com/keys
2. Add to `.env`: `GROQ_API_KEY=gsk_...`
3. Restart FastAPI: `docker-compose restart fastapi`

### Error: "Schema 'default' does not exist"

**Solution:** Table not registered in Trino
- Set `auto_sync=true` in request (default)
- Or manually sync: `POST /query/sync-table`

### LLM generates wrong SQL

**Solution:** Provide better context
- Query is more specific: "Show customers where city equals Mumbai"
- Include table schema in request (auto-detected if table is synced)

### Query is slow

**Solution:** Use Trino instead of Spark
- Set `use_trino=true` (default)
- Ensure table is synced to Trino
- Trino: 100-500ms, Spark: 30-60s

---

## 🎓 Tips for Better Results

### 1. Be Specific
❌ "Show data"  
✅ "Show me all customers"

### 2. Use Domain Terms
❌ "Filter by location Mumbai"  
✅ "Show customers from Mumbai"

### 3. Specify Aggregations Clearly
❌ "Count by city"  
✅ "Count customers by city"

### 4. Use Approximate Column Names
- System knows schema, so "customer id" → `CustomerID`
- "email address" → `Email`
- "customer name" → `Name`

---

## 🚀 Future Enhancements

### Coming in Future Phases:
- **Multi-table joins**: "Show orders with customer names"
- **Date filtering**: "Customers added in last 30 days"
- **Trend analysis**: "Show sales trend by month"
- **Saved queries**: "Run my weekly report"
- **Query suggestions**: "You might also want to..."

---

## 📚 Related Endpoints

| Endpoint | Purpose | Use When |
|----------|---------|----------|
| `POST /query/natural` | Natural language | Easy questions |
| `POST /query/execute` | SQL queries | Complex SQL |
| `POST /query/execute/snapshot` | Time travel | Historical data |
| `GET /query/snapshots/list` | List versions | See history |
| `POST /query/sync-table` | Register table | Setup Trino |

---

## ✅ Summary

**Before (Phase 7):**
```powershell
# Had to write SQL manually
$body = '{"sql":"SELECT * FROM delta.default.customer_data_delta WHERE City = '\''Mumbai'\''"}'
```

**After (Phase 7.5):**
```powershell
# Just ask in natural language!
$body = '{"query":"Show me customers from Mumbai","bucket":"metadataproject","table_path":"test-data/customer_data/customer_data_delta"}'
```

**Result:** Same data, 10x easier! 🎉

---

**Status:** ✅ Implemented (Phase 7.5)  
**Dependencies:** Groq API key required  
**Speed:** ~200-700ms per query (LLM + execution)  
**Cost:** Free tier available (check Groq pricing)
