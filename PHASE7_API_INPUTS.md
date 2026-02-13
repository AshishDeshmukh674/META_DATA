# Phase 7 API Input Guide

## Your Setup Information
- **Storage Type**: aws
- **Bucket**: metadataproject
- **Table Path**: test-data/customer_data/customer_data_delta
- **Table Columns**: CustomerID, Name, Email, City
- **Available Snapshots**: 4 snapshots

---

## API Endpoint Inputs

### 1. POST /query/test-connection
**Purpose**: Test Trino connection and list available catalogs

**Input (JSON)**:
```json
{}
```

**PowerShell**:
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/query/test-connection" -Method Post -ContentType "application/json" -Body '{}'
```

**Expected Output**:
- `success`: true
- `trino_version`: "435"
- `catalogs`: ["delta", "hive", "system"]

---

### 2. GET /query/snapshots/list
**Purpose**: List all available snapshots for your Delta table

**Input (Query Parameters)**:
- `storage_type`: aws
- `bucket`: metadataproject
- `table_path`: test-data/customer_data/customer_data_delta

**PowerShell**:
```powershell
$uri = 'http://localhost:8000/query/snapshots/list?storage_type=aws&bucket=metadataproject&table_path=test-data/customer_data/customer_data_delta'
Invoke-RestMethod -Uri $uri -Method Get
```

**Expected Output**:
- `snapshot_count`: 4
- `snapshots`: Array with snapshot_id, delta_version, schema_columns, file_count

---

### 3. POST /query/execute
**Purpose**: Execute SQL queries using Trino (fast queries)

**Input Examples**:

**Example 1: Basic SELECT**
```json
{
  "sql": "SELECT 1 AS test"
}
```

**Example 2: Show Schemas**
```json
{
  "sql": "SHOW SCHEMAS IN delta"
}
```

**Example 3: Describe Table**
```json
{
  "sql": "DESCRIBE delta.default.customer_data_delta"
}
```

**Example 4: Show Tables**
```json
{
  "sql": "SHOW TABLES IN delta.default"
}
```

**PowerShell**:
```powershell
$body = '{"sql":"SELECT 1 AS test"}'
Invoke-RestMethod -Uri "http://localhost:8000/query/execute" -Method Post -ContentType "application/json" -Body $body
```

---

### 4. POST /query/execute/simple
**Purpose**: Simplified query execution with automatic LIMIT

**Input (JSON)**:
```json
{
  "sql": "SELECT * FROM delta.default.customer_data_delta"
}
```

**PowerShell**:
```powershell
$body = '{"sql":"SELECT * FROM delta.default.customer_data_delta"}'
Invoke-RestMethod -Uri "http://localhost:8000/query/execute/simple" -Method Post -ContentType "application/json" -Body $body
```

**Note**: Automatically adds LIMIT 100 if not specified

---

### 5. POST /query/execute/snapshot
**Purpose**: Query specific snapshot version (Time Travel)

**Input (JSON)**:

**Example 1: Basic Snapshot Query (returns all columns)**
```json
{
  "storage_type": "aws",
  "bucket": "metadataproject",
  "table_path": "test-data/customer_data/customer_data_delta",
  "snapshot_id": "snapshot_20260213_044224_cf52ef3e",
  "limit": 10
}
```

**Example 2: Custom SQL Query**
```json
{
  "storage_type": "aws",
  "bucket": "metadataproject",
  "table_path": "test-data/customer_data/customer_data_delta",
  "snapshot_id": "snapshot_20260213_044224_cf52ef3e",
  "sql_query": "SELECT * FROM {table}",
  "limit": 10
}
```

**Example 3: Filter by Name**
```json
{
  "storage_type": "aws",
  "bucket": "metadataproject",
  "table_path": "test-data/customer_data/customer_data_delta",
  "snapshot_id": "snapshot_20260213_044224_cf52ef3e",
  "sql_query": "SELECT * FROM {table} WHERE Name LIKE 'A%'",
  "limit": 5
}
```

**Example 4: Filter by City**
```json
{
  "storage_type": "aws",
  "bucket": "metadataproject",
  "table_path": "test-data/customer_data/customer_data_delta",
  "snapshot_id": "snapshot_20260213_044224_cf52ef3e",
  "sql_query": "SELECT * FROM {table} WHERE City = 'Mumbai'",
  "limit": 10
}
```

**Example 5: Aggregate COUNT**
```json
{
  "storage_type": "aws",
  "bucket": "metadataproject",
  "table_path": "test-data/customer_data/customer_data_delta",
  "snapshot_id": "snapshot_20260213_044224_cf52ef3e",
  "sql_query": "SELECT COUNT(*) as total_count FROM {table}",
  "limit": 1
}
```

**Example 6: Group By City**
```json
{
  "storage_type": "aws",
  "bucket": "metadataproject",
  "table_path": "test-data/customer_data/customer_data_delta",
  "snapshot_id": "snapshot_20260213_044224_cf52ef3e",
  "sql_query": "SELECT City, COUNT(*) as customer_count FROM {table} GROUP BY City",
  "limit": 100
}
```

**Example 7: Select Specific Columns**
```json
{
  "storage_type": "aws",
  "bucket": "metadataproject",
  "table_path": "test-data/customer_data/customer_data_delta",
  "snapshot_id": "snapshot_20260213_044224_cf52ef3e",
  "sql_query": "SELECT CustomerID, Name, City FROM {table}",
  "limit": 10
}
```

**PowerShell**:
```powershell
$body = @{
    storage_type = "aws"
    bucket = "metadataproject"
    table_path = "test-data/customer_data/customer_data_delta"
    snapshot_id = "snapshot_20260213_044224_cf52ef3e"
    sql_query = "SELECT * FROM {table} WHERE Name LIKE 'A%'"
    limit = 5
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/query/execute/snapshot" -Method Post -ContentType "application/json" -Body $body -TimeoutSec 180
```

**Important Notes**:
- Use `{table}` as placeholder in sql_query - it will be replaced with actual table reference
- First query on each table takes 2-3 minutes (downloads JARs)
- Subsequent queries are faster (30-60 seconds)
- Available columns: CustomerID, Name, Email, City

---

### 6. GET /query/table-info
**Purpose**: Get metadata about a table from Trino catalog

**Input (Query Parameters)**:
- `catalog`: delta
- `schema`: default
- `table`: customer_data_delta

**PowerShell**:
```powershell
$uri = 'http://localhost:8000/query/table-info?catalog=delta&schema=default&table=customer_data_delta'
Invoke-RestMethod -Uri $uri -Method Get
```

**Expected Output**:
- `success`: true
- `table_name`: "customer_data_delta"
- `columns`: Array of column information (name, type, nullable)

---

### 7. POST /query/write
**Purpose**: Write operations (INSERT, UPDATE, DELETE) - Coming in Phase 8

**Input**: Not yet implemented

**Note**: This endpoint is a placeholder for Phase 8 implementation

---

## Common Query Examples for Your Data

### Available Snapshots
To get the latest snapshot ID, first call:
```powershell
$uri = 'http://localhost:8000/query/snapshots/list?storage_type=aws&bucket=metadataproject&table_path=test-data/customer_data/customer_data_delta'
$snapshots = Invoke-RestMethod -Uri $uri -Method Get
$latest_snapshot = $snapshots.snapshots[0].snapshot_id
Write-Host "Latest Snapshot: $latest_snapshot"
```

### Query All Customers
```json
{
  "storage_type": "aws",
  "bucket": "metadataproject",
  "table_path": "test-data/customer_data/customer_data_delta",
  "snapshot_id": "snapshot_20260213_044224_cf52ef3e",
  "limit": 100
}
```

### Search by Customer Name
```json
{
  "storage_type": "aws",
  "bucket": "metadataproject",
  "table_path": "test-data/customer_data/customer_data_delta",
  "snapshot_id": "snapshot_20260213_044224_cf52ef3e",
  "sql_query": "SELECT * FROM {table} WHERE Name LIKE '%Sharma%'",
  "limit": 10
}
```

### Get Customers by City
```json
{
  "storage_type": "aws",
  "bucket": "metadataproject",
  "table_path": "test-data/customer_data/customer_data_delta",
  "snapshot_id": "snapshot_20260213_044224_cf52ef3e",
  "sql_query": "SELECT * FROM {table} WHERE City IN ('Mumbai', 'Delhi')",
  "limit": 50
}
```

### Count Customers per City
```json
{
  "storage_type": "aws",
  "bucket": "metadataproject",
  "table_path": "test-data/customer_data/customer_data_delta",
  "snapshot_id": "snapshot_20260213_044224_cf52ef3e",
  "sql_query": "SELECT City, COUNT(*) as total FROM {table} GROUP BY City ORDER BY total DESC",
  "limit": 100
}
```

### Search by Email Domain
```json
{
  "storage_type": "aws",
  "bucket": "metadataproject",
  "table_path": "test-data/customer_data/customer_data_delta",
  "snapshot_id": "snapshot_20260213_044224_cf52ef3e",
  "sql_query": "SELECT * FROM {table} WHERE Email LIKE '%@gmail.com'",
  "limit": 20
}
```

---

## Complete PowerShell Test Script

```powershell
# Set your configuration
$baseUrl = "http://localhost:8000"
$storageType = "aws"
$bucket = "metadataproject"
$tablePath = "test-data/customer_data/customer_data_delta"

# 1. Test Connection
Write-Host "Testing Trino connection..." -ForegroundColor Cyan
$result = Invoke-RestMethod -Uri "$baseUrl/query/test-connection" -Method Post -ContentType "application/json" -Body '{}'
Write-Host "Connected: $($result.success), Catalogs: $($result.catalogs -join ', ')" -ForegroundColor Green

# 2. List Snapshots
Write-Host "`nListing snapshots..." -ForegroundColor Cyan
$uri = "$baseUrl/query/snapshots/list?storage_type=$storageType&bucket=$bucket&table_path=$tablePath"
$snapshots = Invoke-RestMethod -Uri $uri -Method Get
Write-Host "Found $($snapshots.snapshot_count) snapshots" -ForegroundColor Green
$latest_snapshot = $snapshots.snapshots[0].snapshot_id
Write-Host "Latest snapshot: $latest_snapshot" -ForegroundColor Gray

# 3. Basic Query
Write-Host "`nExecuting basic query..." -ForegroundColor Cyan
$body = '{"sql":"SELECT 1 AS test"}'
$result = Invoke-RestMethod -Uri "$baseUrl/query/execute" -Method Post -ContentType "application/json" -Body $body
Write-Host "Query result: $($result.data[0].test)" -ForegroundColor Green

# 4. Snapshot Query - Get All Data
Write-Host "`nQuerying snapshot (all data)..." -ForegroundColor Cyan
$body = @{
    storage_type = $storageType
    bucket = $bucket
    table_path = $tablePath
    snapshot_id = $latest_snapshot
    limit = 5
} | ConvertTo-Json
$result = Invoke-RestMethod -Uri "$baseUrl/query/execute/snapshot" -Method Post -ContentType "application/json" -Body $body -TimeoutSec 180
Write-Host "Returned $($result.row_count) rows in $($result.execution_time_ms)ms" -ForegroundColor Green
$result.data | Format-Table

# 5. Snapshot Query - Filter by Name
Write-Host "`nQuerying with filter (Name LIKE 'A%')..." -ForegroundColor Cyan
$body = @{
    storage_type = $storageType
    bucket = $bucket
    table_path = $tablePath
    snapshot_id = $latest_snapshot
    sql_query = "SELECT * FROM {table} WHERE Name LIKE 'A%'"
    limit = 10
} | ConvertTo-Json
$result = Invoke-RestMethod -Uri "$baseUrl/query/execute/snapshot" -Method Post -ContentType "application/json" -Body $body -TimeoutSec 180
Write-Host "Found $($result.row_count) customers with names starting with 'A'" -ForegroundColor Green

# 6. Snapshot Query - Count Total
Write-Host "`nCounting total customers..." -ForegroundColor Cyan
$body = @{
    storage_type = $storageType
    bucket = $bucket
    table_path = $tablePath
    snapshot_id = $latest_snapshot
    sql_query = "SELECT COUNT(*) as total_count FROM {table}"
    limit = 1
} | ConvertTo-Json
$result = Invoke-RestMethod -Uri "$baseUrl/query/execute/snapshot" -Method Post -ContentType "application/json" -Body $body -TimeoutSec 180
Write-Host "Total customers: $($result.data[0].total_count)" -ForegroundColor Green

Write-Host "`nAll queries completed successfully!" -ForegroundColor Cyan
```

---

## Performance Tips

1. **First Query Performance**: First snapshot query takes 2-3 minutes due to JAR downloads (delta-spark, hadoop-aws, aws-sdk)
2. **Subsequent Queries**: Faster, typically 30-60 seconds
3. **Use Trino for Fast Queries**: For simple SELECTs without time travel, use `/query/execute` (much faster)
4. **Limit Results**: Always use `limit` parameter to avoid long-running queries
5. **Connection Pooling**: Reuse connections by keeping containers running

---

## Error Handling

- **500 Internal Server Error**: Check column names match exactly (CustomerID, Name, Email, City)
- **404 Not Found**: Restart FastAPI container if endpoints not found
- **Timeout**: Increase `-TimeoutSec` parameter for large queries
- **Unknown Version**: System defaults to version 0 automatically
