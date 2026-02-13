# Phase 7: SQL Read Engine (Trino) ✅

**Status:** Complete  
**Date:** February 13, 2026

## 🎯 What Was Built

Phase 7 adds a **fast SQL query engine** using Trino for reading data from Delta Lake, Iceberg, Hudi, and Parquet tables stored in AWS S3.

### Key Features

- ✅ **Trino Query Engine** - 10-100x faster than Spark for read queries
- ✅ **SQL Query Endpoint** - Execute arbitrary SQL SELECT queries
- ✅ **Multiple Catalogs** - Support for Delta Lake (`delta`) and Parquet/Iceberg/Hudi (`hive`)
- ✅ **Simplified Queries** - Helper endpoint for basic table queries
- ✅ **Table Metadata** - Get schema information for any table
- ✅ **Connection Testing** - Verify Trino connectivity

---

## 🏗️ Architecture

```
User → FastAPI → Trino → S3 (AWS)
                    ↓
            [Delta, Iceberg, Hudi, Parquet]
```

**Why Trino for Reads?**
- **Speed**: MPP (Massively Parallel Processing) architecture
- **Zero ETL**: Queries data directly from S3, no data movement
- **ANSI SQL**: Standard SQL syntax, easy to use
- **Multiple Formats**: Native support for all lakehouse formats

---

## 🐳 Docker Services

### Added in Phase 7

```yaml
services:
  trino:
    image: trinodb/trino:435
    ports:
      - "8082:8080"  # Trino UI
    environment:
      - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
      - AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
      - AWS_REGION=${AWS_REGION}
    volumes:
      - ./config/trino/catalog:/etc/trino/catalog
```

### Full Stack (Phase 6 + 7)

| Service | Port | Purpose |
|---------|------|---------|
| **FastAPI** | 8000 | Main API server |
| **Spark Master** | 7077, 8081 | Metadata extraction & writes |
| **Spark Worker** | - | Executes Spark jobs |
| **Trino** | 8082 | Fast SQL read queries |

---

## 📂 New Files

### 1. Trino Query Engine
**File:** `app/engines/trino_query_engine.py` (343 lines)

**What it does:**
- Connects to Trino cluster
- Executes SQL queries
- Returns results as JSON
- Handles errors and retries

**Key Methods:**
```python
engine = TrinoQueryEngine()

# Execute SQL query
result = engine.execute_query(
    sql="SELECT * FROM delta.default.sales WHERE region = 'us-east' LIMIT 100"
)

# Get table metadata
info = engine.get_table_info(
    catalog='delta',
    schema='default',
    table='sales_delta'
)

# Test connection
status = engine.test_connection()
```

---

### 2. Query API Endpoints
**File:** `app/api/query.py` (456 lines)

**Endpoints:**

#### `POST /query/execute`
Execute arbitrary SQL SELECT queries.

**Request:**
```json
{
  "sql": "SELECT * FROM delta.default.sales_delta WHERE region = 'us-east'",
  "limit": 100
}
```

**Response:**
```json
{
  "success": true,
  "row_count": 100,
  "columns": ["id", "name", "price", "region"],
  "data": [
    {"id": 1, "name": "Product A", "price": 19.99, "region": "us-east"},
    {"id": 2, "name": "Product B", "price": 29.99, "region": "us-east"}
  ],
  "execution_time_ms": 234,
  "timestamp": "2026-02-13T10:30:00Z"
}
```

---

#### `POST /query/execute/simple`
Simplified query interface - no SQL required!

**Request:**
```json
{
  "catalog": "delta",
  "schema": "default",
  "table": "sales_delta",
  "filter": "region = 'us-east' AND amount > 100",
  "columns": ["id", "customer_name", "amount"],
  "limit": 50
}
```

Automatically builds SQL:
```sql
SELECT id, customer_name, amount 
FROM delta.default.sales_delta 
WHERE region = 'us-east' AND amount > 100 
LIMIT 50
```

---

#### `GET /query/table-info`
Get table schema and column information.

**Request:**
```
GET /query/table-info?catalog=delta&schema=default&table=sales_delta
```

**Response:**
```json
{
  "success": true,
  "catalog": "delta",
  "schema": "default",
  "table": "sales_delta",
  "columns": [
    {"name": "id", "type": "integer", "nullable": true},
    {"name": "name", "type": "varchar", "nullable": true},
    {"name": "price", "type": "double", "nullable": true}
  ]
}
```

---

#### `POST /query/test-connection`
Verify Trino is running and accessible.

**Response:**
```json
{
  "success": true,
  "message": "Connected to Trino successfully",
  "version": "435",
  "catalogs": ["delta", "hive", "system"],
  "host": "trino",
  "port": 8080
}
```

---

### 3. Trino Catalog Configuration
**Files:** 
- `config/trino/catalog/delta.properties` - Delta Lake catalog
- `config/trino/catalog/hive.properties` - Parquet/Iceberg/Hudi catalog

**Delta Catalog Config:**
```properties
connector.name=delta_lake
hive.metastore=file
hive.metastore.catalog.dir=s3://metadataproject/

# S3 credentials from environment
hive.s3.aws-access-key=${ENV:AWS_ACCESS_KEY_ID}
hive.s3.aws-secret-key=${ENV:AWS_SECRET_ACCESS_KEY}
hive.s3.endpoint=s3.${ENV:AWS_REGION}.amazonaws.com
```

---

## 🚀 Getting Started

### 1. Install Dependencies

```bash
# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Install new dependencies
pip install trino==0.328.0
```

Or reinstall all:
```bash
pip install -r requirements.txt
```

---

### 2. Start Docker Services

```bash
# Stop existing containers (if running)
docker-compose down

# Start all services (Spark + Trino)
docker-compose up -d

# Verify all containers are running
docker ps
```

**Expected Output:**
```
CONTAINER ID   IMAGE                   STATUS       PORTS
xxxxx          apache/spark:3.5.1      Up 30s       7077, 8081
xxxxx          apache/spark:3.5.1      Up 30s       
xxxxx          trinodb/trino:435       Up 30s       8082:8080
xxxxx          lakehouse-api           Up 30s       8000:8000
```

---

### 3. Wait for Services to Initialize

**Trino takes 30-60 seconds to start**

Check Trino logs:
```bash
docker logs lakehouse-trino --follow
```

Wait for:
```
INFO  main  io.trino.server.Server  ======== SERVER STARTED ========
```

Or check health:
```bash
curl http://localhost:8082/v1/info
```

---

### 4. Test Connection

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/query/test-connection" `
  -Method Post
```

**Expected Response:**
```json
{
  "success": true,
  "message": "Connected to Trino successfully",
  "version": "435",
  "catalogs": ["delta", "hive", "system"]
}
```

---

## 🧪 Testing Examples

### Example 1: Query Delta Lake Table

**Query your existing Delta table from Phase 6:**

```powershell
$body = @{
  sql = "SELECT * FROM delta.default.""s3://metadataproject/test-data/customer_data/customer_data_delta"" LIMIT 10"
  limit = 10
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/query/execute" `
  -Method Post -Body $body -ContentType "application/json"
```

**Note:** For direct S3 paths, wrap in double quotes and escape inner quotes.

---

### Example 2: Simplified Query

```powershell
$body = @{
  catalog = "delta"
  schema = "default"
  table = '"s3://metadataproject/test-data/customer_data/customer_data_delta"'
  limit = 10
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/query/execute/simple" `
  -Method Post -Body $body -ContentType "application/json"
```

---

### Example 3: Aggregate Query

```powershell
$body = @{
  sql = @"
SELECT 
  COUNT(*) as total_customers,
  AVG(age) as avg_age
FROM delta.default."s3://metadataproject/test-data/customer_data/customer_data_delta"
"@
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/query/execute" `
  -Method Post -Body $body -ContentType "application/json"
```

---

### Example 4: Query Parquet Files Directly

```powershell
$body = @{
  sql = "SELECT * FROM hive.default.""s3://metadataproject/test-data/customer_data/customer_data.parquet"" LIMIT 5"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/query/execute" `
  -Method Post -Body $body -ContentType "application/json"
```

---

## 🎯 SQL Query Examples

### Basic SELECT
```sql
SELECT * FROM delta.default."s3://bucket/table_delta" LIMIT 100
```

### Filtering
```sql
SELECT id, name, price 
FROM delta.default."s3://bucket/products_delta"
WHERE price > 50 AND category = 'Electronics'
```

### Aggregation
```sql
SELECT 
  region,
  COUNT(*) as order_count,
  SUM(amount) as total_revenue,
  AVG(amount) as avg_order_value
FROM delta.default."s3://bucket/orders_delta"
GROUP BY region
ORDER BY total_revenue DESC
```

### Joins
```sql
SELECT 
  o.order_id,
  o.amount,
  c.customer_name,
  c.email
FROM delta.default."s3://bucket/orders_delta" o
JOIN delta.default."s3://bucket/customers_delta" c
  ON o.customer_id = c.id
WHERE o.date >= DATE '2024-01-01'
```

### Window Functions
```sql
SELECT 
  customer_id,
  order_date,
  amount,
  SUM(amount) OVER (
    PARTITION BY customer_id 
    ORDER BY order_date
  ) as running_total
FROM delta.default."s3://bucket/orders_delta"
```

---

## ⚡ Performance Tips

### 1. Add LIMIT Clause
Always use `LIMIT` for exploratory queries:
```sql
SELECT * FROM table LIMIT 1000
```

### 2. Use Partition Pruning
If table is partitioned by date/region:
```sql
-- Good: Reads only one partition
SELECT * FROM sales WHERE date = '2024-01-15'

-- Bad: Reads all partitions
SELECT * FROM sales WHERE customer_id = 123
```

### 3. Select Only Needed Columns
```sql
-- Good: Reads only 3 columns
SELECT id, name, price FROM products

-- Bad: Reads all columns (slower)
SELECT * FROM products
```

### 4. Use Column Predicates
```sql
-- Good: Predicate pushdown (fast)
SELECT * FROM orders WHERE amount > 100

-- Bad: Filter in application (slow)
SELECT * FROM orders -- then filter in code
```

---

## 📊 Expected Performance

| Query Size | Row Count | Execution Time |
|------------|-----------|----------------|
| Small | < 1,000 | 50-200ms |
| Medium | 1K - 100K | 200-2000ms |
| Large | 100K - 1M | 2-10s |
| Very Large | > 1M | 10-60s |

**Factors:**
- S3 latency: ~10-50ms per object
- Data size: Parquet compression ratio
- Query complexity: Joins, aggregations slower
- Partition pruning: Only read necessary data

---

## 🔍 Troubleshooting

### Trino Not Starting

**Check logs:**
```bash
docker logs lakehouse-trino
```

**Common Issues:**
- **Port conflict:** Another service using 8082
- **Memory:** Trino needs ~2GB RAM
- **AWS credentials:** Check environment variables

**Solution:**
```bash
docker-compose restart trino
```

---

### Query Fails: "Catalog 'delta' does not exist"

**Cause:** Catalog configuration not mounted

**Solution:**
```bash
# Check catalog files exist
ls config/trino/catalog/

# Restart Trino to reload configs
docker-compose restart trino
```

---

### Query Fails: "Access Denied" on S3

**Cause:** AWS credentials not passed to Trino

**Check:**
```bash
# View Trino environment
docker exec lakehouse-trino env | grep AWS
```

**Solution:**
```bash
# Ensure .env file has AWS credentials
cat .env | grep AWS

# Restart with new credentials
docker-compose down
docker-compose up -d
```

---

### Query Times Out

**Cause:** Query too large or complex

**Solutions:**
1. Add `LIMIT` clause
2. Add partition filters
3. Select fewer columns
4. Increase timeout (in `trino_query_engine.py`)

---

## 🔜 Phase 8 Preview: SQL Write Engine

**Coming Next:** SQL write operations with **automatic metadata updates**

### What Will Be Built

1. **Spark SQL Write Engine**
   - Execute INSERT/UPDATE/DELETE/MERGE queries
   - ACID transactions via Delta Lake
   - Support for all lakehouse formats

2. **Automatic Metadata Updates**
   - Generate new metadata snapshot after every write
   - Track schema changes, row counts
   - Store in S3 for version history

3. **Write Endpoint**
   - `POST /query/write` - Execute write queries

### Example (Phase 8)

```powershell
# Insert new data
$body = @{
  sql = @"
INSERT INTO delta.`s3a://bucket/sales_delta`
VALUES (1, 'Product X', 99.99, 'us-west', '2024-01-15')
"@
  storage_type = "aws"
  bucket = "metadataproject"
  target_path = "tables/sales_delta"
  auto_snapshot = true  # Automatically update metadata
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/query/write" `
  -Method Post -Body $body -ContentType "application/json"
```

**Response:**
```json
{
  "success": true,
  "operation": "INSERT",
  "rows_affected": 1,
  "execution_time_ms": 3456,
  "metadata_updated": true,
  "snapshot_id": "snapshot_20260213_105430_abc123",
  "timestamp": "2026-02-13T10:54:30Z"
}
```

---

## 📈 Progress Summary

### Completed

- ✅ Phase 0: Architecture & Design
- ✅ Phase 1: Environment Setup
- ✅ Phase 2: FastAPI Skeleton
- ✅ Phase 3: AWS Connection Validation
- ✅ Phase 4: Table Format Detection
- ✅ Phase 5: Metadata Readers
- ✅ Phase 6: Spark Metadata Extraction + CSV to Delta
- ✅ **Phase 7: Trino SQL Read Engine** ← **YOU ARE HERE**

### Next Steps

- ⏳ Phase 8: Spark SQL Write Engine + Auto Metadata Updates
- ⏳ Phase 9: MCP Server (Query Routing)
- ⏳ Phase 10: Snapshot Comparison
- ⏳ Phase 11: Frontend (React/Next.js)

---

## 🎓 What You Learned

### Phase 7 Concepts

1. **Trino Architecture**
   - MPP query execution
   - Catalog-based data access
   - Connector architecture (Delta, Hive)

2. **SQL Query Optimization**
   - Partition pruning
   - Projection pushdown
   - Predicate pushdown

3. **Docker Orchestration**
   - Multi-service docker-compose
   - Service dependencies
   - Volume mounting for configs

4. **API Design**
   - SQL query endpoints
   - Simplified query builders
   - Error handling for external services

---

## 📚 References

- [Trino Documentation](https://trino.io/docs/current/)
- [Trino Delta Lake Connector](https://trino.io/docs/current/connector/delta-lake.html)
- [Trino Hive Connector](https://trino.io/docs/current/connector/hive.html)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Python Trino Client](https://github.com/trinodb/trino-python-client)

---

**Next:** Ready to implement Phase 8? Let me know!
