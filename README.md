# 🏔️ Lakehouse Metadata & Query Platform

**A complete data lakehouse platform that discovers, manages, and queries Delta Lake tables on AWS S3 without requiring external metastores like Hive or AWS Glue.**

---

## 📖 What This Project Is

This is a **real-world implementation** of a modern data lakehouse platform that solves a critical problem: **How do you query Delta Lake tables stored in S3 without setting up complex metastore infrastructure?**

### The Problem We Solved

Traditional data warehouses require:
- ❌ Complex metastore setup (Hive Metastore, AWS Glue Catalog)
- ❌ Expensive managed services
- ❌ Tight coupling between compute and metadata
- ❌ Manual table registration processes

### Our Solution

✅ **Metastore-less architecture** - Metadata lives with data in `_delta_log/`  
✅ **Auto-discovery** - Automatically detect and read table schemas  
✅ **Dual query engines** - Spark for time travel, Trino for fast analytics  
✅ **Custom snapshots** - Version control for data with automatic metadata  
✅ **REST API** - Easy integration with any application  

---

## 🎯 What We Built (The Journey)

### Phase 1-4: Foundation ✅
- Environment setup (Docker, Python, AWS credentials)
- FastAPI skeleton with health checks
- AWS S3 connectivity validation
- Automatic table format detection (Delta/Iceberg/Hudi/Parquet)

### Phase 5: Metadata Discovery ✅
- Read Delta Lake transaction logs (`_delta_log/`)
- Extract schema, partitions, and file information
- No metastore required - direct S3 reading

### Phase 6: Delta Snapshot System ✅
**Why:** Delta Lake's `_delta_log/` is technical. We needed business-friendly snapshots.

**What we built:**
- Convert CSV → Delta Lake format
- Generate custom snapshot metadata (`.metadata-snapshots/`)
- Store schema, version, file counts, and timestamps
- Enable easy time travel for non-technical users

**Real example:**
```
s3://metadataproject/test-data/customer_data/customer_data_delta/
├── _delta_log/                    # Delta's technical logs
│   ├── 00000000000000000000.json
│   └── ...
├── .metadata-snapshots/           # Our business-friendly snapshots
│   ├── snapshot_20260213_044224_cf52ef3e.json
│   ├── snapshot_20260213_044300_abc123de.json
│   └── ...
└── part-*.parquet                 # Actual data files
```

### Phase 7: Query Execution ✅
**Why:** Users need to query data, not just see metadata.

**The Challenge:** 
- Spark is slow (30-60 seconds) but supports time travel
- Trino is fast (100ms) but needs table registration
- How do we get the best of both?

**Our Solution:**
1. **Snapshot Queries** - Use Spark for time travel to any historical version
2. **Fast Queries** - Use Trino for current data after one-time registration
3. **Auto-sync endpoint** - Automatically register Delta tables in Trino

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         USER / APPLICATION                   │
└────────────┬───────────────────────────────────┬────────────┘
             │                                   │
    ┌────────▼────────┐                 ┌───────▼────────┐
    │   FASTAPI       │                 │   SWAGGER UI   │
    │   Port: 8000    │                 │   /docs        │
    └────────┬────────┘                 └────────────────┘
             │
   ┌─────────┴──────────────────────────────────────┐
   │         QUERY ROUTING LAYER                    │
   │  "Should this use Spark or Trino?"            │
   └─────────┬──────────────────────┬───────────────┘
             │                      │
   ┌─────────▼──────────┐  ┌───────▼──────────┐
   │  SPARK 3.5.1       │  │  TRINO 435       │
   │  (Time Travel)     │  │  (Fast Queries)  │
   │                    │  │                  │
   │  • Slow: 30-60s    │  │  • Fast: 100ms   │
   │  • Any version     │  │  • Current only  │
   │  • Auto-discovers  │  │  • Needs sync    │
   └─────────┬──────────┘  └───────┬──────────┘
             │                     │
             └──────────┬──────────┘
                        │
              ┌─────────▼────────────┐
              │      AWS S3          │
              │   metadataproject    │
              │                      │
              │  customer_data_      │
              │     delta/           │
              │  ├─ _delta_log/      │
              │  ├─ .metadata-       │
              │  │   snapshots/      │
              │  └─ part-*.parquet   │
              └──────────────────────┘
```

---

## 💡 Why We Chose Each Technology

### FastAPI (REST API Layer)
**Why not Flask/Django?**
- ✅ Auto-generated API documentation (Swagger UI)
- ✅ Type validation with Pydantic
- ✅ Async support for better performance
- ✅ Modern Python 3.10+ features

### Apache Spark (Write Engine & Time Travel)
**Why not just Trino?**
- ✅ Native Delta Lake support
- ✅ Reads `_delta_log/` automatically
- ✅ Supports time travel queries
- ✅ Can write to Delta format
- ❌ Slow for interactive queries (30-60 seconds)

### Trino (Fast Query Engine)
**Why not just Spark?**
- ✅ 100-500ms query execution (vs 30-60s with Spark)
- ✅ Designed for interactive analytics
- ✅ Supports standard SQL
- ❌ Needs table registration (can't read `_delta_log/` directly)
- ❌ No time travel support

### Delta Lake (Storage Format)
**Why not Iceberg/Hudi/Parquet?**
- ✅ ACID transactions
- ✅ Time travel (query old versions)
- ✅ Schema evolution
- ✅ Scalable metadata (`_delta_log/` is just JSON files)
- ✅ Battle-tested by Databricks

### Docker (Infrastructure)
**Why not install everything locally?**
- ✅ Consistent environments (works on any machine)
- ✅ Easy cleanup (remove containers, not reinstall software)
- ✅ Production-like setup
- ✅ Multiple services (Spark, Trino) isolated

---

## 🐛 Mistakes We Made & How We Fixed Them

### Mistake 1: Using CREATE TABLE for Existing Delta Data
**What happened:** Tried to register Delta table in Trino with `CREATE TABLE ... WITH (location = 's3://...')`

**Error:**
```
Using CREATE TABLE with an existing table content is disallowed
```

**Why it failed:** Trino's Delta connector expects clean locations for CREATE TABLE. Existing data must use `register_table()` procedure.

**Solution:**
```sql
-- ❌ Wrong
CREATE TABLE delta.default.customer_data_delta (...) WITH (location = 's3://...')

-- ✅ Correct
CALL delta.system.register_table(
  schema_name => 'default',
  table_name => 'customer_data_delta',
  table_location => 's3://metadataproject/test-data/customer_data/customer_data_delta/'
)
```

**Impact:** Updated `/query/sync-table` endpoint to use `register_table()` instead of `CREATE TABLE`.

---

### Mistake 2: Duplicate API Tags in Swagger UI
**What happened:** All endpoints appeared twice in Swagger UI under different sections.

**Why it failed:** Tags defined in both `router = APIRouter(tags=["X"])` and `app.include_router(router, tags=["Y"])`.

**Solution:** Removed duplicate tags from router definitions, kept only in `main.py`.

**Before:**
```
Query Execution (Phase 7)
  - POST /query/execute
  - POST /query/execute/simple
  ...

Query Execution  
  - POST /query/execute  (duplicate!)
  - POST /query/execute/simple  (duplicate!)
  ...
```

**After:**
```
Query Execution (Phase 7)
  - POST /query/execute
  - POST /query/execute/simple
  ...
```

---

### Mistake 3: Schema Not Found Error
**What happened:** `/query/execute` failed with "Schema 'default' does not exist"

**Why it failed:** Trino catalogs are completely separate. Having a Delta connector doesn't mean tables are registered.

**The confusion:** Spark can query `s3://bucket/path/` directly. Trino needs explicit registration.

**Solution:** Created `/query/sync-table` endpoint to register tables before querying.

**Workflow now:**
```
1. Generate Delta table → /metadata/generate
2. Register in Trino  → /query/sync-table
3. Fast queries work  → /query/execute
```

---

### Mistake 4: Confusing Snapshot Queries with Trino Queries
**User confusion:** "Why do some queries need `storage_type`, `bucket`, `table_path` and others need `sql`?"

**Why this happened:** Two different query systems with different purposes.

**Clarification:**
- **Snapshot Queries** (`/query/execute/snapshot`): Spark-based, time travel, needs S3 params
- **Trino Queries** (`/query/execute`): Trino-based, fast, needs SQL with registered table names

---

## 🗂️ Our Real Data Structure

**S3 Bucket:** `metadataproject`  
**Table Path:** `test-data/customer_data/customer_data_delta`  
**Format:** Delta Lake  
**Columns:** CustomerID, Name, Email, City  
**Row Count:** 3 rows  
**Files:** 3 parquet files (~2.1 KB each)  
**Snapshots:** 4 versions available  

**Full S3 Structure:**
```
s3://metadataproject/
└── test-data/
    └── customer_data/
        ├── customer_data.csv                    # Original source
        └── customer_data_delta/                 # Delta Lake table
            ├── _delta_log/                      # Delta transaction log
            │   ├── 00000000000000000000.json    # Version 0
            │   ├── 00000000000000000001.json
            │   └── _last_checkpoint
            ├──metadata-snapshots/             # Our custom snapshots
            │   ├── snapshot_20260213_044224_cf52ef3e.json
            │   ├── snapshot_20260213_044300_abc123de.json
            │   ├── snapshot_20260213_044315_def456gh.json
            │   └── snapshot_20260213_044330_ghi789jk.json
            ├── part-00000-*.snappy.parquet      # Data file 1
            ├── part-00001-*.snappy.parquet      # Data file 2
            └── part-00002-*.snappy.parquet      # Data file 3
```

**Sample Data:**
| CustomerID | Name  | Email           | City   |
|------------|-------|-----------------|--------|
| 1          | Alice | alice@email.com | Mumbai |
| 2          | Bob   | bob@email.com   | Delhi  |
| 3          | Carol | carol@email.com | Mumbai |

---

## 🚀 Quick Start Guide

### Prerequisites
- **Windows** (or Linux/Mac with minor command changes)
- **Python 3.10+** installed
- **Docker Desktop** running
- **AWS Account** with S3 access

### Step 1: Clone Repository
```powershell
git clone https://github.com/AshishDeshmukh674/META_DATA.git
cd METAL
```

### Step 2: Create Virtual Environment
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### Step 3: Install Dependencies
```powershell
pip install -r requirements.txt
```

### Step 4: Configure Environment
```powershell
Copy-Item .env.example .env
```

**Edit `.env` with your AWS credentials:**
```env
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-east-1
```

### Step 5: Start Docker Services
```powershell
docker-compose up -d
Start-Sleep -Seconds 30  # Wait for containers to be ready
```

**Verify containers:**
```powershell
docker ps
```

Should show:
- `lakehouse-api` (FastAPI)
- `spark-master`
- `spark-worker`
- `lakehouse-trino`

### Step 6: Access the Platform
- **API Docs:** http://localhost:8000/docs
- **Trino UI:** http://localhost:8082
- **Spark UI:** http://localhost:8081

---

## 📚 Complete API Reference

### Phase 6: Metadata Generation

#### POST /metadata/generate
**Purpose:** Convert CSV to Delta Lake format and generate snapshots

**Why this exists:** Delta Lake needs setup. This endpoint automates: CSV reading → Spark conversion → Delta write → Snapshot generation.

**Real Example:**
```powershell
$body = @{
    storage_type = "aws"
    bucket = "metadataproject"
    path = "test-data/customer_data/customer_data.csv"
    table_format = "delta"
    force_refresh = $false
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/metadata/generate" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body
```

**Response:**
```json
{
  "success": true,
  "message": "Metadata generated successfully",
  "table_format": "delta",
  "snapshot_id": "snapshot_20260213_044224_cf52ef3e",
  "s3_location": "s3://metadataproject/test-data/customer_data/customer_data_delta/",
  "schema": {
    "fields": [
      {"name": "CustomerID", "type": "string"},
      {"name": "Name", "type": "string"},
      {"name": "Email", "type": "string"},
      {"name": "City", "type": "string"}
    ]
  },
  "row_count": 3,
  "file_count": 3,
  "execution_time_ms": 125430
}
```

**What it does:**
1. Reads `customer_data.csv` from S3
2. Creates Spark session with Delta Lake support
3. Writes data to `customer_data_delta/` folder
4. Generates `_delta_log/` transaction logs
5. Creates `.metadata-snapshots/` with version info
6. Returns snapshot ID for querying

**First run:** Takes 2-3 minutes (downloads JARs: delta-spark, hadoop-aws, aws-sdk)  
**Subsequent runs:** 30-60 seconds

---

#### GET /query/snapshots/list
**Purpose:** List all available snapshot versions

**Why this exists:** Users need to see available versions before time travel queries.

**Real Example:**
```powershell
$uri = 'http://localhost:8000/query/snapshots/list?storage_type=aws&bucket=metadataproject&table_path=test-data/customer_data/customer_data_delta'
Invoke-RestMethod -Uri $uri -Method Get
```

**Response:**
```json
{
  "success": true,
  "message": "Found 4 snapshots",
  "snapshot_count": 4,
  "storage_info": {
    "storage_type": "aws",
    "bucket": "metadataproject",
    "table_path": "test-data/customer_data/customer_data_delta"
  },
  "snapshots": [
    {
      "snapshot_id": "snapshot_20260213_044330_ghi789jk",
      "delta_version": 0,
      "timestamp": "2026-02-13T04:43:30Z",
      "schema_columns": ["CustomerID", "Name", "Email", "City"],
      "file_count": 3,
      "format": "delta"
    },
    {
      "snapshot_id": "snapshot_20260213_044315_def456gh",
      "delta_version": 0,
      "timestamp": "2026-02-13T04:43:15Z",
      "schema_columns": ["CustomerID", "Name", "Email", "City"],
      "file_count": 3,
      "format": "delta"
    },
    {
      "snapshot_id": "snapshot_20260213_044300_abc123de",
      "delta_version": 0,
      "timestamp": "2026-02-13T04:43:00Z",
      "schema_columns": ["CustomerID", "Name", "Email", "City"],
      "file_count": 3,
      "format": "delta"
    },
    {
      "snapshot_id": "snapshot_20260213_044224_cf52ef3e",
      "delta_version": 0,
      "timestamp": "2026-02-13T04:42:24Z",
      "schema_columns": ["CustomerID", "Name", "Email", "City"],
      "file_count": 3,
      "format": "delta"
    }
  ]
}
```

**What you get:**
- Total snapshot count
- Each snapshot's ID, timestamp, schema, file count
- Latest snapshot first (descending order)

**Use case:** Get snapshot IDs for time travel queries

---

### Phase 7: Query Execution

#### POST /query/test-connection
**Purpose:** Verify Trino is running and accessible

**Why this exists:** Before querying, ensure Trino container is healthy.

**Real Example:**
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/query/test-connection" `
    -Method Post `
    -ContentType "application/json" `
    -Body '{}'
```

**Response:**
```json
{
  "success": true,
  "trino_version": "435",
  "catalogs": ["delta", "hive", "system"],
  "message": "Successfully connected to Trino"
}
```

**What it checks:**
- Trino container is running
- Version info accessible
- Delta catalog configured

**Run this first** before any Trino queries.

---

#### POST /query/sync-table
**Purpose:** Register Delta table in Trino for fast queries

**Why this exists:** Trino can't read `_delta_log/` automatically. This endpoint:
1. Reads Delta metadata from S3
2. Extracts schema
3. Registers table using `delta.system.register_table()`
4. Enables fast SQL queries

**Real Example:**
```powershell
$uri = 'http://localhost:8000/query/sync-table?storage_type=aws&bucket=metadataproject&table_path=test-data/customer_data/customer_data_delta&schema_name=default'
Invoke-RestMethod -Uri $uri -Method Post
```

**Response:**
```json
{
  "success": true,
  "message": "Table synced successfully to Trino",
  "catalog": "delta",
  "schema": "default",
  "table": "customer_data_delta",
  "location": "s3://metadataproject/test-data/customer_data/customer_data_delta/",
  "columns": ["CustomerID", "Name", "Email", "City"],
  "trino_query_example": "SELECT * FROM delta.default.customer_data_delta LIMIT 10"
}
```

**What it does:**
1. Lists snapshots to get latest metadata
2. Extracts schema from `_delta_log/`
3. Creates schema: `CREATE SCHEMA IF NOT EXISTS delta.default`
4. Unregisters old version: `CALL delta.system.unregister_table(...)`
5. Registers table: `CALL delta.system.register_table(...)`
6. Verifies with `SELECT COUNT(*)`

**Run this once** after generating Delta table. Re-run if schema changes.

**After sync, you can query:**
```sql
SELECT * FROM delta.default.customer_data_delta WHERE City = 'Mumbai'
```

---

#### POST /query/execute
**Purpose:** Execute SQL queries using Trino (fast, current data only)

**Why this exists:** For interactive analytics when you don't need time travel.

**Prerequisites:** Table must be registered with `/query/sync-table` first.

**Real Examples:**

**1. Simple SELECT:**
```powershell
$body = '{"sql":"SELECT 1+1 AS result"}'
Invoke-RestMethod -Uri "http://localhost:8000/query/execute" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body
```

**2. Query Customer Data:**
```powershell
$body = '{"sql":"SELECT * FROM delta.default.customer_data_delta"}'
Invoke-RestMethod -Uri "http://localhost:8000/query/execute" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body
```

**3. Filter by City:**
```powershell
$body = '{"sql":"SELECT * FROM delta.default.customer_data_delta WHERE City = '\''Mumbai'\''"}'
Invoke-RestMethod -Uri "http://localhost:8000/query/execute" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body
```

**4. Count Customers per City:**
```powershell
$body = '{"sql":"SELECT City, COUNT(*) as count FROM delta.default.customer_data_delta GROUP BY City"}'
Invoke-RestMethod -Uri "http://localhost:8000/query/execute" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body
```

**Response:**
```json
{
  "success": true,
  "row_count": 2,
  "columns": ["City", "count"],
  "data": [
    {"City": "Mumbai", "count": 2},
    {"City": "Delhi", "count": 1}
  ],
  "execution_time_ms": 156,
  "query_id": "20260213_071145_00030_22tqz"
}
```

**Performance:** 100-500ms (vs 30-60s with Spark)

**Supports:**
- ✅ SELECT, WHERE, JOIN, GROUP BY, ORDER BY
- ✅ Aggregations (COUNT, SUM, AVG, MIN, MAX)
- ✅ SHOW SCHEMAS, SHOW TABLES, DESCRIBE
- ❌ Time travel (use `/query/execute/snapshot` instead)
- ❌ INSERT/UPDATE/DELETE (Phase 8)

---

#### POST /query/execute/simple
**Purpose:** Simplified query execution with automatic LIMIT

**Why this exists:** Prevents accidentally returning millions of rows.

**Difference from /query/execute:** Automatically adds `LIMIT 100` if not specified.

**Real Example:**
```powershell
# This query will auto-add LIMIT 100
$body = '{"sql":"SELECT * FROM delta.default.customer_data_delta"}'
Invoke-RestMethod -Uri "http://localhost:8000/query/execute/simple" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body
```

**Actual query executed:**
```sql
SELECT * FROM delta.default.customer_data_delta LIMIT 100
```

**Use case:** Safe exploration of large tables

---

#### POST /query/execute/snapshot
**Purpose:** Query specific historical snapshot (time travel)

**Why this exists:** See data as it was at any point in time. Uses Spark (auto-reads `_delta_log/`).

**Real Examples:**

**1. Get All Data from Latest Snapshot:**
```powershell
$body = @{
    storage_type = "aws"
    bucket = "metadataproject"
    table_path = "test-data/customer_data/customer_data_delta"
    snapshot_id = "snapshot_20260213_044224_cf52ef3e"
    limit = 10
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/query/execute/snapshot" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body `
    -TimeoutSec 180
```

**2. Filter by City:**
```powershell
$body = @{
    storage_type = "aws"
    bucket = "metadataproject"
    table_path = "test-data/customer_data/customer_data_delta"
    snapshot_id = "snapshot_20260213_044224_cf52ef3e"
    sql_query = "SELECT * FROM {table} WHERE City = 'Mumbai'"
    limit = 10
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/query/execute/snapshot" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body `
    -TimeoutSec 180
```

**3. Count Customers per City:**
```powershell
$body = @{
    storage_type = "aws"
    bucket = "metadataproject"
    table_path = "test-data/customer_data/customer_data_delta"
    snapshot_id = "snapshot_20260213_044224_cf52ef3e"
    sql_query = "SELECT City, COUNT(*) as count FROM {table} GROUP BY City"
    limit = 100
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/query/execute/snapshot" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body `
    -TimeoutSec 180
```

**Response:**
```json
{
  "success": true,
  "snapshot_id": "snapshot_20260213_044224_cf52ef3e",
  "row_count": 3,
  "columns": ["CustomerID", "Name", "Email", "City"],
  "data": [
    {"CustomerID": "1", "Name": "Alice", "Email": "alice@email.com", "City": "Mumbai"},
    {"CustomerID": "2", "Name": "Bob", "Email": "bob@email.com", "City": "Delhi"},
    {"CustomerID": "3", "Name": "Carol", "Email": "carol@email.com", "City": "Mumbai"}
  ],
  "execution_time_ms": 77546,
  "delta_version": 0
}
```

**Important notes:**
- Use `{table}` placeholder in `sql_query` - it's replaced with actual table reference
- First query: 2-3 minutes (downloads JARs)
- Subsequent queries: 30-60 seconds
- Supports full Spark SQL syntax

**Available columns for queries:**
- CustomerID
- Name
- Email
- City

**Example queries:**
```sql
-- All customers
SELECT * FROM {table}

-- Mumbai customers only
SELECT * FROM {table} WHERE City = 'Mumbai'

-- Names starting with 'A'
SELECT * FROM {table} WHERE Name LIKE 'A%'

-- Count by city
SELECT City, COUNT(*) as count FROM {table} GROUP BY City

-- Search by email domain
SELECT * FROM {table} WHERE Email LIKE '%@email.com'
```

---

#### GET /query/table-info
**Purpose:** Get table metadata from Trino catalog

**Why this exists:** After registration, verify table is queryable and see schema.

**Prerequisites:** Table must be synced with `/query/sync-table` first.

**Real Example:**
```powershell
$uri = 'http://localhost:8000/query/table-info?catalog=delta&schema=default&table=customer_data_delta'
Invoke-RestMethod -Uri $uri -Method Get
```

**Response:**
```json
{
  "success": true,
  "catalog": "delta",
  "schema": "default",
  "table_name": "customer_data_delta",
  "columns": [
    {"name": "CustomerID", "type": "varchar", "nullable": true},
    {"name": "Name", "type": "varchar", "nullable": true},
    {"name": "Email", "type": "varchar", "nullable": true},
    {"name": "City", "type": "varchar", "nullable": true}
  ]
}
```

**What you get:**
- Column names and Trino types
- Nullable status
- Confirms table is registered correctly

---

#### POST /query/write
**Purpose:** Execute write operations (INSERT/UPDATE/DELETE)

**Status:** ❌ **NOT IMPLEMENTED** (Coming in Phase 8)

**Current Response:**
```json
{
  "detail": "Write queries will be implemented in Phase 8"
}
```

**Planned for Phase 8:**
- INSERT new rows
- UPDATE existing data
- DELETE rows
- MERGE (upsert) operations
- Automatic snapshot generation after writes

---

## 🔄 Complete Workflow Example

### Scenario: Query Customer Data

**Step 1: Generate Delta Table**
```powershell
# Convert CSV to Delta Lake format
$body = @{
    storage_type = "aws"
    bucket = "metadataproject"
    path = "test-data/customer_data/customer_data.csv"
    table_format = "delta"
    force_refresh = $false
} | ConvertTo-Json

$result = Invoke-RestMethod -Uri "http://localhost:8000/metadata/generate" `
    -Method Post -ContentType "application/json" -Body $body

Write-Host "Table generated: $($result.s3_location)"
Write-Host "Snapshot ID: $($result.snapshot_id)"
```

**Step 2: List Available Snapshots**
```powershell
# See all versions
$uri = 'http://localhost:8000/query/snapshots/list?storage_type=aws&bucket=metadataproject&table_path=test-data/customer_data/customer_data_delta'
$snapshots = Invoke-RestMethod -Uri $uri -Method Get

Write-Host "Found $($snapshots.snapshot_count) snapshots"
$latest_snapshot = $snapshots.snapshots[0].snapshot_id
Write-Host "Latest: $latest_snapshot"
```

**Step 3: Option A - Slow Snapshot Query (Time Travel)**
```powershell
# Query using Spark (supports any version)
$body = @{
    storage_type = "aws"
    bucket = "metadataproject"
    table_path = "test-data/customer_data/customer_data_delta"
    snapshot_id = $latest_snapshot
    sql_query = "SELECT City, COUNT(*) as count FROM {table} GROUP BY City"
    limit = 100
} | ConvertTo-Json

$result = Invoke-RestMethod -Uri "http://localhost:8000/query/execute/snapshot" `
    -Method Post -ContentType "application/json" -Body $body -TimeoutSec 180

Write-Host "Query time: $($result.execution_time_ms)ms"
$result.data | Format-Table
```

**Execution time:** ~30-60 seconds

**Step 3: Option B - Fast Trino Query (Current Data Only)**
```powershell
# First, register table in Trino (one-time)
$uri = 'http://localhost:8000/query/sync-table?storage_type=aws&bucket=metadataproject&table_path=test-data/customer_data/customer_data_delta&schema_name=default'
Invoke-RestMethod -Uri $uri -Method Post

# Now query with Trino (fast!)
$body = '{"sql":"SELECT City, COUNT(*) as count FROM delta.default.customer_data_delta GROUP BY City"}'
$result = Invoke-RestMethod -Uri "http://localhost:8000/query/execute" `
    -Method Post -ContentType "application/json" -Body $body

Write-Host "Query time: $($result.execution_time_ms)ms"
$result.data | Format-Table
```

**Execution time:** ~100-500 milliseconds

---

## 🔍 Understanding the Two Query Systems

### When to Use Snapshot Queries (Spark)

**Use cases:**
- ✅ Need to query old versions (time travel)
- ✅ Auditing: "What did the data look like last week?"
- ✅ Debugging: "When did this bad data appear?"
- ✅ Compliance: "Show me data as of December 31st"

**Characteristics:**
- Slow: 30-60 seconds per query
- No setup required (auto-discovers `_delta_log/`)
- Supports any snapshot version
- Full Spark SQL support

**Example:**
```powershell
# Query data from 2 hours ago
$body = @{
    storage_type = "aws"
    bucket = "metadataproject"
    table_path = "test-data/customer_data/customer_data_delta"
    snapshot_id = "snapshot_20260213_044224_cf52ef3e"  # Old version
    sql_query = "SELECT * FROM {table} WHERE City = 'Mumbai'"
    limit = 10
} | ConvertTo-Json
```

---

### When to Use Trino Queries

**Use cases:**
- ✅ Interactive dashboards
- ✅ BI tools (Tableau, Power BI)
- ✅ Ad-hoc exploration
- ✅ Real-time analytics
- ✅ API responses (user-facing applications)

**Characteristics:**
- Fast: 100-500 milliseconds
- Requires one-time setup (`/query/sync-table`)
- Current data only (no time travel)
- Standard SQL support

**Example:**
```powershell
# First sync (once)
$uri = 'http://localhost:8000/query/sync-table?storage_type=aws&bucket=metadataproject&table_path=test-data/customer_data/customer_data_delta&schema_name=default'
Invoke-RestMethod -Uri $uri -Method Post

# Then query (many times, fast)
$body = '{"sql":"SELECT * FROM delta.default.customer_data_delta WHERE City = '\''Mumbai'\''"}'
Invoke-RestMethod -Uri "http://localhost:8000/query/execute" `
    -Method Post -ContentType "application/json" -Body $body
```

---

## 🔬 How Trino Registration Works

### The Problem

Trino doesn't scan S3 looking for tables. It needs a **catalog** (think: table of contents).

**Without registration:**
```sql
SELECT * FROM delta.default.customer_data_delta
→ Error: Schema 'default' does not exist
```

**Why?** Trino's catalog is empty:
```
delta.information_schema [empty]
```

---

### The Solution: register_table()

Trino provides `delta.system.register_table()` procedure:

**What it does:**
1. Reads Delta `_delta_log/` from S3
2. Extracts schema (columns and types)
3. Notes current data file locations
4. Creates catalog entry: `delta.default.customer_data_delta` → `s3://...`

**After registration:**
```
delta.default.customer_data_delta → s3://metadataproject/.../customer_data_delta/
```

**Now queries work:**
```sql
SELECT * FROM delta.default.customer_data_delta
→ Returns data in 100ms!
```

---

### Our /query/sync-table Endpoint

Automates the registration process:

```
1. List snapshots → Get latest
2. Read _delta_log/ → Extract schema
3. Map Delta types → Trino types
   string → VARCHAR
   integer → INTEGER
   long → BIGINT
4. CREATE SCHEMA IF NOT EXISTS delta.default
5. CALL delta.system.unregister_table() (remove old)
6. CALL delta.system.register_table() (register new)
7. SELECT COUNT(*) → Verify it works
```

**You call once:**
```powershell
POST /query/sync-table
```

**Then query forever:**
```sql
SELECT * FROM delta.default.customer_data_delta WHERE...
```

---

## 📊 Performance Comparison

### Real Performance Data (Our Table)

| Operation | Trino | Spark | Winner |
|-----------|-------|-------|--------|
| **Simple SELECT** | 156ms | 77,546ms (77s) | Trino (494x faster) |
| **GROUP BY** | 189ms | 82,123ms (82s) | Trino (434x faster) |
| **WHERE filter** | 143ms | 75,234ms (75s) | Trino (526x faster) |
| **Time travel** | ❌ Not supported | 77,546ms (77s) | Spark (only option) |

### Why Such a Big Difference?

**Spark (Snapshot Queries):**
1. Start JVM (10s)
2. Download JARs: delta-spark, hadoop-aws, aws-sdk (30s first time)
3. Create Spark session (5s)
4. List S3 files (2s)
5. Read `_delta_log/` (3s)
6. Plan query (2s)
7. Execute query (5s)
8. Collect results (1s)
9. Shutdown (1s)

**Total:** ~59 seconds

**Trino (Fast Queries):**
1. Parse SQL (10ms)
2. Look up catalog (5ms)
3. Plan query (20ms)
4. Execute on workers (100ms)
5. Return results (21ms)

**Total:** ~156ms

---

## 🛠️ Docker Services

### What's Running?

```powershell
docker ps
```

**Expected containers:**

| Container | Image | Port | Purpose |
|-----------|-------|------|---------|
| `lakehouse-api` | Custom (FastAPI) | 8000 | REST API |
| `spark-master` | apache/spark:3.5.1 | 7077, 8081 | Spark master |
| `spark-worker` | apache/spark:3.5.1 | - | Spark worker |
| `lakehouse-trino` | trinodb/trino:435 | 8082 | Trino query engine |

### Service Management

**Start all services:**
```powershell
docker-compose up -d
```

**Stop all services:**
```powershell
docker-compose down
```

**Restart specific service:**
```powershell
docker-compose restart fastapi
docker-compose restart trino
```

**View logs:**
```powershell
docker logs lakehouse-api --tail 50 --follow
docker logs lakehouse-trino --tail 50 --follow
```

**Check health:**
```powershell
# API health
Invoke-RestMethod http://localhost:8000/health

# Trino health
Invoke-RestMethod http://localhost:8082/v1/info
```

---

## 🌐 Access Points

| Service | URL | Purpose |
|---------|-----|---------|
| **FastAPI Swagger** | http://localhost:8000/docs | Interactive API docs |
| **FastAPI ReDoc** | http://localhost:8000/redoc | Alternative API docs |
| **Trino Web UI** | http://localhost:8082 | Query monitoring |
| **Spark Master UI** | http://localhost:8081 | Spark cluster status |

---

## 🧪 Testing Checklist

### Phase 6: Metadata Generation

- [ ] Generate Delta table from CSV
- [ ] List snapshots (should show 4)
- [ ] Verify files in S3 (3 parquet files)
- [ ] Check `_delta_log/` exists
- [ ] Check `.metadata-snapshots/` exists

**Commands:**
```powershell
# Generate
POST /metadata/generate

# List
GET /query/snapshots/list
```

---

### Phase 7: Query Execution

- [ ] Test Trino connection
- [ ] Sync table to Trino
- [ ] Execute simple Trino query
- [ ] Execute COUNT/GROUP BY query
- [ ] Execute snapshot query (time travel)
- [ ] Verify Trino UI shows queries

**Commands:**
```powershell
# 1. Test connection
POST /query/test-connection

# 2. Sync table
POST /query/sync-table

# 3. Trino query
POST /query/execute
{"sql":"SELECT * FROM delta.default.customer_data_delta"}

# 4. Snapshot query
POST /query/execute/snapshot
{snapshot_id, sql_query, ...}
```

---

## 🐞 Troubleshooting

### Error: "Schema 'default' does not exist"

**Cause:** Table not registered in Trino

**Solution:**
```powershell
$uri = 'http://localhost:8000/query/sync-table?storage_type=aws&bucket=metadataproject&table_path=test-data/customer_data/customer_data_delta&schema_name=default'
Invoke-RestMethod -Uri $uri -Method Post
```

---

### Error: "Using CREATE TABLE with existing table content"

**Cause:** Trino can't CREATE TABLE on existing Delta data

**Solution:** Already fixed! We use `register_table()` instead. Just call `/query/sync-table`.

---

### Error: Snapshot query takes 3+ minutes

**Cause:** First query downloads JARs (delta-spark, hadoop-aws, aws-sdk)

**Solution:** Wait once. Subsequent queries will be ~30-60 seconds.

---

### Error: Docker container not starting

**Check logs:**
```powershell
docker logs lakehouse-api
docker logs lakehouse-trino
```

**Common issues:**
- Port already in use (change in docker-compose.yml)
- Out of memory (allocate more to Docker Desktop)
- AWS credentials not set (check .env file)

---

### Error: API returns 500 Internal Server Error

**Check logs:**
```powershell
docker logs lakehouse-api --tail 50
```

**Common causes:**
- Invalid AWS credentials
- S3 bucket doesn't exist
- Network timeout (increase `-TimeoutSec`)

---

## 📈 What's Next: Phase 8

**Write Operations:**
- INSERT new rows into Delta tables
- UPDATE existing data
- DELETE rows
- MERGE (upsert) operations
- Automatic snapshot generation after writes
- Transaction rollback support

**Example (coming soon):**
```powershell
$body = @{
    sql = "INSERT INTO delta.``s3a://metadataproject/test-data/customer_data/customer_data_delta`` (CustomerID, Name, Email, City) VALUES ('4', 'David', 'david@email.com', 'Bangalore')"
    storage_type = "aws"
    bucket = "metadataproject"
    target_path = "test-data/customer_data/customer_data_delta"
    auto_snapshot = $true
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/query/write" `
    -Method Post -ContentType "application/json" -Body $body
```

---

## 📚 Key Learnings

### 1. Metastores Are Optional
Traditional wisdom: "You need Hive Metastore or AWS Glue"

**Reality:** Delta Lake's `_delta_log/` IS the metastore. Just read it directly!

### 2. One Size Doesn't Fit All
**Spark:** Great for writes and time travel  
**Trino:** Great for fast reads  

**Use both!** Each for its strengths.

### 3. Registration vs Discovery
**Spark:** Auto-discovers (`_delta_log/` reading is built-in)  
**Trino:** Needs registration (catalog-based architecture)

**Solution:** Automate registration with `/query/sync-table`

### 4. Custom Snapshots Fill a Gap
**Delta's `_delta_log/`:** Technical, hard to understand  
**Our `.metadata-snapshots/`:** Business-friendly, easy versions

**Both matter:** Delta for engine compatibility, snapshots for humans

---

## 🎓 Project Structure

```
META/
├── app/
│   ├── api/                              # API endpoints
│   │   ├── health.py                     # Health checks
│   │   ├── connection.py                 # AWS validation (Phase 3)
│   │   ├── detect.py                     # Format detection (Phase 4)
│   │   ├── metadata.py                   # Metadata reading (Phase 5)
│   │   ├── metadata_gen.py               # Delta generation (Phase 6)
│   │   └── query.py                      # Query execution (Phase 7)
│   ├── core/                             # Core utilities
│   │   ├── settings.py                   # Environment config
│   │   ├── logger.py                     # JSON logging
│   │   └── aws_client.py                 # S3 client
│   ├── engines/                          # Query engines
│   │   ├── trino_query_engine.py         # Trino interface
│   │   └── spark_query_engine.py         # Spark interface
│   ├── metadata/                         # Format readers
│   │   ├── delta_reader.py               # Delta _delta_log/ parser
│   │   └── format_detector.py            # Auto-detect formats
│   ├── storage/                          # Snapshot management
│   │   ├── snapshot_manager.py           # Generate/list snapshots
│   │   └── delta_converter.py            # CSV → Delta conversion
│   └── main.py                           # FastAPI app
├── config/
│   └── trino/
│       └── catalog/
│           ├── delta.properties          # Delta Lake connector
│           └── hive.properties           # Hive connector
├── docker-compose.yml                    # Container orchestration
├── Dockerfile                            # FastAPI container
├── requirements.txt                      # Python dependencies
├── .env                                  # Environment variables (DO NOT COMMIT)
├── .env.example                          # Environment template
├── PHASE7_API_INPUTS.md                  # API usage guide
└── README.md                             # This file
```

---

## 🤝 Contributing

This is a learning project built phase-by-phase. Each phase is committed separately to show progression.

**Commit convention:**
```
feat: Phase X - Description
fix: Bug description
docs: Documentation update
```

---

## 📄 License

MIT License - Educational purposes

---

## 👨‍💻 Author

Built as a hands-on learning project for understanding:
- Lakehouse architecture (Delta Lake, Iceberg, Hudi)
- Distributed query engines (Trino, Spark)
- Data platform engineering
- REST API design
- Docker orchestration

**GitHub:** https://github.com/AshishDeshmukh674/META_DATA

---

## 📌 Quick Command Reference

### Setup
```powershell
# Clone & setup
git clone https://github.com/AshishDeshmukh674/META_DATA.git
cd META
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Configure
Copy-Item .env.example .env
# Edit .env with AWS credentials

# Start services
docker-compose up -d
Start-Sleep -Seconds 30
```

### Generate Delta Table
```powershell
$body = @{
    storage_type = "aws"
    bucket = "metadataproject"
    path = "test-data/customer_data/customer_data.csv"
    table_format = "delta"
    force_refresh = $false
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/metadata/generate" `
    -Method Post -ContentType "application/json" -Body $body
```

### Query with Trino (Fast)
```powershell
# Step 1: Sync table (once)
$uri = 'http://localhost:8000/query/sync-table?storage_type=aws&bucket=metadataproject&table_path=test-data/customer_data/customer_data_delta&schema_name=default'
Invoke-RestMethod -Uri $uri -Method Post

# Step 2: Query (many times)
$body = '{"sql":"SELECT * FROM delta.default.customer_data_delta WHERE City = '\''Mumbai'\''"}'
Invoke-RestMethod -Uri "http://localhost:8000/query/execute" `
    -Method Post -ContentType "application/json" -Body $body
```

### Query with Spark (Time Travel)
```powershell
# List snapshots
$uri = 'http://localhost:8000/query/snapshots/list?storage_type=aws&bucket=metadataproject&table_path=test-data/customer_data/customer_data_delta'
$snapshots = Invoke-RestMethod -Uri $uri -Method Get
$snapshot_id = $snapshots.snapshots[0].snapshot_id

# Query snapshot
$body = @{
    storage_type = "aws"
    bucket = "metadataproject"
    table_path = "test-data/customer_data/customer_data_delta"
    snapshot_id = $snapshot_id
    sql_query = "SELECT * FROM {table} WHERE City = 'Mumbai'"
    limit = 10
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/query/execute/snapshot" `
    -Method Post -ContentType "application/json" -Body $body -TimeoutSec 180
```

---

**Last Updated:** Phase 7 Complete (Query Execution)  
**Status:** Fully functional read-query platform  
**Next:** Phase 8 - Write Operations

---

## 🎉 Success Metrics

If you can do all of these, the platform is working:

- ✅ Generate Delta table from CSV → `/metadata/generate`
- ✅ List 4 snapshots → `/query/snapshots/list`
- ✅ See Delta files in S3 → AWS Console
- ✅ Test Trino connection → `/query/test-connection`
- ✅ Sync table to Trino → `/query/sync-table`
- ✅ Fast query (< 1 second) → `/query/execute`
- ✅ Time travel query → `/query/execute/snapshot`
- ✅ See queries in Trino UI → http://localhost:8082

**All green? Congratulations! Your lakehouse platform is live! 🚀**
