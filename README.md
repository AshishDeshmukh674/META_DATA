# 🏔️ Lakehouse Explorer & SQL Platform

A **metastore-less** lakehouse platform that discovers and queries Delta, Iceberg, Hudi, and Parquet tables directly from S3/MinIO storage.

## 🎯 What This Does

- ✅ **Discover** lakehouse tables without a metastore (no Hive/Glue/Unity Catalog)
- ✅ **Detect** table formats automatically (Delta/Iceberg/Hudi/Parquet)
- ✅ **Validate** AWS/MinIO credentials and connectivity
- ✅ **Query** using Trino (fast reads) or Spark (writes) - Coming in Phase 6-7
- ✅ **Explore** metadata, schemas, partitions, and snapshots - Coming in Phase 5
- ✅ **Route** queries intelligently via MCP Server - Coming in Phase 8
- ✅ **Test** everything via FastAPI

## 🧠 Architecture

```
User → FastAPI → MCP Server → Trino (READ) / Spark (WRITE) → S3/MinIO
                              ↓
                         Direct S3 API (metadata)
```

**Key Innovation:** Metadata is stored alongside data (Delta's `_delta_log/`, Iceberg's `metadata/`, etc.) — no separate metastore needed!

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+** installed
- **Docker Desktop** running
- **AWS Account** (optional, for S3 access)

### 1️⃣ Clone & Setup

```bash
git clone https://github.com/AshishDeshmukh674/META_DATA.git
cd META
```

### 2️⃣ Create Virtual Environment

**Windows:**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**Linux/Mac:**
```bash
python -m venv .venv
source .venv/bin/activate
```

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 4️⃣ Configure Environment

```bash
# Windows
Copy-Item .env.example .env

# Linux/Mac
cp .env.example .env
```

**Edit `.env` with your credentials:**

```env
# AWS Credentials (if using AWS S3)
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-east-1
AWS_S3_BUCKET=your-bucket-name

# MinIO (for local testing)
MINIO_ENDPOINT=http://localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=lakehouse
```

### 5️⃣ Start Infrastructure (Docker)

**Start Docker Desktop first**, then:

```bash
docker-compose up -d
```

This starts:
- **MinIO** (S3-compatible storage) on `localhost:9000`
- **Trino** (query engine) on `localhost:8080`

**Verify containers are running:**
```bash
docker ps
```

You should see:
- `lakehouse-minio` - healthy
- `lakehouse-trino` - healthy

### 6️⃣ Run API Server

```bash
uvicorn app.main:app --reload --port 8000
```

Or with Python module:
```bash
python -m uvicorn app.main:app --reload --port 8000
```

**API docs available at:** http://localhost:8000/docs

---

## 🎮 Access Points

| Service | URL | Credentials |
|---------|-----|-------------|
| **FastAPI Docs** | http://localhost:8000/docs | No auth |
| **FastAPI ReDoc** | http://localhost:8000/redoc | No auth |
| **MinIO Console** | http://localhost:9001 | minioadmin / minioadmin |
| **Trino Web UI** | http://localhost:8080 | No auth |

---

## 📂 Project Structure

```
META/
├── app/
│   ├── api/                # FastAPI routers & endpoints
│   │   ├── health.py       # Health check endpoints
│   │   ├── connection.py   # AWS/MinIO connection validation
│   │   ├── detect.py       # Table format detection
│   │   └── schemas.py      # Pydantic models
│   ├── core/               # Config, logging, utilities
│   │   ├── settings.py     # Environment configuration
│   │   ├── logger.py       # Structured JSON logging
│   │   └── aws_client.py   # AWS S3 client wrapper
│   ├── metadata/           # Format-specific readers
│   │   └── format_detector.py  # Auto-detect table formats
│   ├── engines/            # Trino & Spark clients (Phase 6-7)
│   └── mcp/                # Query routing logic (Phase 8)
├── config/                 # Configuration files
│   └── trino/              # Trino catalog configs
├── tests/                  # Unit & integration tests
├── docs/                   # Architecture & design docs
├── logs/                   # Application logs
├── .env                    # Environment variables (DO NOT COMMIT)
├── .env.example            # Environment template
├── requirements.txt        # Python dependencies
├── docker-compose.yml      # Docker services
└── README.md               # This file
```

---

## 🔌 API Endpoints

### ✅ Phase 2: Health & Status

#### `GET /`
Basic API information.

**Example:**
```bash
curl http://localhost:8000/
```

#### `GET /health`
Simple health check.

**Response:**
```json
{
  "status": "healthy",
  "service": "LakehouseExplorer",
  "version": "0.1.0"
}
```

#### `GET /health/detailed`
Comprehensive system diagnostics.

#### `GET /health/ready`
Kubernetes readiness probe.

#### `GET /health/live`
Kubernetes liveness probe.

---

### ✅ Phase 3: Connection Validation

#### `POST /connect/aws`
Validate AWS S3 credentials and bucket access.

**Request:**
```json
{
  "access_key_id": "AKIA...",
  "secret_access_key": "...",
  "region": "us-east-1",
  "bucket": "your-bucket-name"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Successfully connected to AWS S3 bucket 'your-bucket-name'",
  "bucket": "your-bucket-name",
  "bucket_exists": true,
  "can_list": true,
  "can_read": true,
  "object_count": 42
}
```

#### `POST /connect/minio`
Validate MinIO connection (auto-creates bucket if needed).

**Request:**
```json
{
  "endpoint": "http://localhost:9000",
  "access_key": "minioadmin",
  "secret_key": "minioadmin",
  "bucket": "lakehouse"
}
```

#### `GET /connect/status`
Check current storage configuration.

---

### ✅ Phase 4: Table Format Detection

#### `POST /detect-format`
Automatically detect table format from storage layout.

**Request (AWS S3):**
```json
{
  "storage_type": "aws",
  "bucket": "metadataproject",
  "path": "test-data/sample-data/delta/sales_delta"
}
```

**Request (MinIO):**
```json
{
  "storage_type": "minio",
  "bucket": "lakehouse",
  "path": "warehouse/customers"
}
```

**Response (Delta Lake detected):**
```json
{
  "success": true,
  "format": "delta",
  "confidence": "high",
  "metadata_location": "s3://metadataproject/.../sales_delta/_delta_log/",
  "markers_found": ["_delta_log/", "5 transaction log files"],
  "file_count": 15,
  "data_files": 10,
  "message": "Detected Delta Lake table with transaction log"
}
```

**Supported Formats:**
- **Delta Lake**: Detects `_delta_log/` directory
- **Apache Iceberg**: Detects `metadata/` directory
- **Apache Hudi**: Detects `.hoodie/` directory
- **Parquet**: Plain `.parquet` files

---

### ✅ Phase 5: Metadata Exploration

Explore table metadata without a metastore! Get schema, partitions, snapshots, and file lists.

#### `POST /metadata/schema`
Get table schema (column names, types, partition columns).

**Request Body:**
```json
{
  "storage_type": "aws",
  "bucket": "metadataproject",
  "path": "test-data/sample-data/delta/sales_delta",
  "format": "delta"
}
```

**What each field means:**
- `storage_type`: Where your data is stored (`"aws"` for S3, `"minio"` for local)
- `bucket`: The S3/MinIO bucket name
- `path`: Path to the table inside the bucket
- `format`: Table format (`"delta"`, `"iceberg"`, `"hudi"`, or `"parquet"`) - optional, will auto-detect if not provided

**Expected Response:**
```json
{
  "success": true,
  "table_format": "delta",
  "data": {
    "success": true,
    "table_format": "delta",
    "schema": {
      "type": "struct",
      "fields": [
        {
          "name": "product_id",
          "type": "integer",
          "nullable": true,
          "metadata": {}
        },
        {
          "name": "product_name",
          "type": "string",
          "nullable": true,
          "metadata": {}
        },
        {
          "name": "price",
          "type": "double",
          "nullable": true,
          "metadata": {}
        }
      ]
    },
    "partition_columns": ["region", "date"],
    "version": 5
  },
  "timestamp": "2026-01-31T10:30:00Z"
}
```

**What you get:**
- Full table schema with all columns and their data types
- Partition columns (columns used to organize data)
- Current table version (Delta Lake tracks versions)

---

#### `POST /metadata/snapshots`
Get table version history (who changed what and when).

**Request Body:**
```json
{
  "storage_type": "aws",
  "bucket": "metadataproject",
  "path": "test-data/sample-data/delta/sales_delta",
  "format": "delta"
}
```

**Expected Response:**
```json
{
  "success": true,
  "table_format": "delta",
  "data": {
    "success": true,
    "table_format": "delta",
    "snapshot_count": 6,
    "latest_version": 5,
    "snapshots": [
      {
        "version": 0,
        "timestamp": 1640995200000,
        "operation": "CREATE TABLE",
        "files_added": 10,
        "files_removed": 0
      },
      {
        "version": 1,
        "timestamp": 1641081600000,
        "operation": "WRITE",
        "files_added": 5,
        "files_removed": 0
      },
      {
        "version": 2,
        "timestamp": 1641168000000,
        "operation": "UPDATE",
        "files_added": 3,
        "files_removed": 2
      }
    ]
  },
  "timestamp": "2026-01-31T10:30:00Z"
}
```

**What you get:**
- Complete version history of the table
- Each snapshot shows: version number, timestamp, operation type (CREATE/WRITE/UPDATE/DELETE), files added/removed
- Latest version number

**Use cases:**
- Time travel: See table state at any point in time
- Audit trail: Track all changes to the table
- Debugging: Find when data was corrupted or deleted

---

#### `POST /metadata/partitions`
Get partition information (how data is organized).

**Request Body:**
```json
{
  "storage_type": "aws",
  "bucket": "metadataproject",
  "path": "test-data/sample-data/delta/sales_delta",
  "format": "delta"
}
```

**Expected Response:**
```json
{
  "success": true,
  "table_format": "delta",
  "data": {
    "success": true,
    "table_format": "delta",
    "is_partitioned": true,
    "partition_columns": ["region", "date"],
    "partition_count": 45,
    "partitions": [
      {"region": "us-east", "date": "2024-01-01"},
      {"region": "us-east", "date": "2024-01-02"},
      {"region": "us-west", "date": "2024-01-01"},
      {"region": "eu-central", "date": "2024-01-01"}
    ]
  },
  "timestamp": "2026-01-31T10:30:00Z"
}
```

**What you get:**
- Partition columns (columns used to split data into folders)
- All unique partition values (e.g., all regions and dates)
- Total partition count

**Why partitions matter:**
- Faster queries: Only read relevant partitions (e.g., only data for "us-east")
- Cost savings: Skip scanning unnecessary data
- Better organization: Data grouped by business logic (region, date, etc.)

---

#### `POST /metadata/files`
Get list of all data files in the table.

**Request Body:**
```json
{
  "storage_type": "aws",
  "bucket": "metadataproject",
  "path": "test-data/sample-data/delta/sales_delta",
  "format": "delta"
}
```

**Expected Response:**
```json
{
  "success": true,
  "table_format": "delta",
  "data": {
    "success": true,
    "table_format": "delta",
    "file_count": 127,
    "total_size_bytes": 4589234567,
    "files": [
      {
        "path": "region=us-east/date=2024-01-01/part-00000.parquet",
        "size": 45892345,
        "modification_time": 1640995200000,
        "partition_values": {
          "region": "us-east",
          "date": "2024-01-01"
        }
      },
      {
        "path": "region=us-west/date=2024-01-02/part-00001.parquet",
        "size": 38234567,
        "modification_time": 1641081600000,
        "partition_values": {
          "region": "us-west",
          "date": "2024-01-02"
        }
      }
    ]
  },
  "timestamp": "2026-01-31T10:30:00Z"
}
```

**What you get:**
- Total number of data files
- Total size in bytes (convert: 1 GB = 1,073,741,824 bytes)
- Each file with: path, size, modification time, partition values

**Use cases:**
- Storage analysis: See which partitions use most space
- Performance tuning: Identify small files that should be compacted
- Data lineage: Track which files were added in each version

---

### 🔜 Coming Soon

#### Phase 6-7: Query Execution
- `POST /query/execute` - Execute SQL (MCP routes to Trino or Spark)

#### Phase 9: Snapshot Operations
- `GET /snapshots/diff` - Compare two snapshots

---

## 🧪 Testing Examples

### Test MinIO Connection

```bash
curl -X POST http://localhost:8000/connect/minio \
  -H "Content-Type: application/json" \
  -d '{
    "endpoint": "http://localhost:9000",
    "access_key": "minioadmin",
    "secret_key": "minioadmin",
    "bucket": "lakehouse"
  }'
```

**PowerShell:**
```powershell
$body = @{
  endpoint="http://localhost:9000"
  access_key="minioadmin"
  secret_key="minioadmin"
  bucket="lakehouse"
} | ConvertTo-Json

Invoke-RestMethod -Uri http://localhost:8000/connect/minio `
  -Method Post -Body $body -ContentType "application/json"
```

### Test Format Detection

```bash
curl -X POST http://localhost:8000/detect-format \
  -H "Content-Type: application/json" \
  -d '{
    "storage_type": "aws",
    "bucket": "metadataproject",
    "path": "test-data/sample-data/delta/sales_delta"
  }'
```

**PowerShell:**
```powershell
$body = @{
  storage_type="aws"
  bucket="metadataproject"
  path="test-data/sample-data/delta/sales_delta"
} | ConvertTo-Json

Invoke-RestMethod -Uri http://localhost:8000/detect-format `
  -Method Post -Body $body -ContentType "application/json"
```

---

### Test Metadata Extraction (Phase 5)

#### Get Table Schema

**PowerShell:**
```powershell
# Get schema for Delta Lake table on AWS S3
$body = @{
  storage_type="aws"
  bucket="metadataproject"
  path="test-data/sample-data/delta/sales_delta"
  format="delta"
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri http://localhost:8000/metadata/schema `
  -Method Post -Body $body -ContentType "application/json"

# View the schema
$response.data.schema | ConvertTo-Json -Depth 5
```

**Bash/curl:**
```bash
curl -X POST http://localhost:8000/metadata/schema \
  -H "Content-Type: application/json" \
  -d '{
    "storage_type": "aws",
    "bucket": "metadataproject",
    "path": "test-data/sample-data/delta/sales_delta",
    "format": "delta"
  }' | jq '.data.schema'
```

---

#### Get Table Snapshots (Version History)

**PowerShell:**
```powershell
# Get snapshot history
$body = @{
  storage_type="aws"
  bucket="metadataproject"
  path="test-data/sample-data/delta/sales_delta"
  format="delta"
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri http://localhost:8000/metadata/snapshots `
  -Method Post -Body $body -ContentType "application/json"

# View snapshots
Write-Host "Total Versions: $($response.data.snapshot_count)"
Write-Host "Latest Version: $($response.data.latest_version)"
$response.data.snapshots | Format-Table version, operation, files_added, files_removed
```

**Bash/curl:**
```bash
curl -X POST http://localhost:8000/metadata/snapshots \
  -H "Content-Type: application/json" \
  -d '{
    "storage_type": "aws",
    "bucket": "metadataproject",
    "path": "test-data/sample-data/delta/sales_delta",
    "format": "delta"
  }' | jq '.data.snapshots'
```

---

#### Get Partition Information

**PowerShell:**
```powershell
# Get partition details
$body = @{
  storage_type="aws"
  bucket="metadataproject"
  path="test-data/sample-data/delta/sales_delta"
  format="delta"
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri http://localhost:8000/metadata/partitions `
  -Method Post -Body $body -ContentType "application/json"

# View partitions
Write-Host "Is Partitioned: $($response.data.is_partitioned)"
Write-Host "Partition Columns: $($response.data.partition_columns -join ', ')"
Write-Host "Total Partitions: $($response.data.partition_count)"
$response.data.partitions | Select-Object -First 10 | Format-Table
```

**Bash/curl:**
```bash
curl -X POST http://localhost:8000/metadata/partitions \
  -H "Content-Type: application/json" \
  -d '{
    "storage_type": "aws",
    "bucket": "metadataproject",
    "path": "test-data/sample-data/delta/sales_delta",
    "format": "delta"
  }' | jq '.data | {is_partitioned, partition_columns, partition_count}'
```

---

#### Get Data Files List

**PowerShell:**
```powershell
# Get all data files
$body = @{
  storage_type="aws"
  bucket="metadataproject"
  path="test-data/sample-data/delta/sales_delta"
  format="delta"
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri http://localhost:8000/metadata/files `
  -Method Post -Body $body -ContentType "application/json"

# View file statistics
Write-Host "Total Files: $($response.data.file_count)"
$sizeGB = [math]::Round($response.data.total_size_bytes / 1GB, 2)
Write-Host "Total Size: $sizeGB GB"
$response.data.files | Select-Object -First 5 | Format-Table path, size, partition_values
```

**Bash/curl:**
```bash
curl -X POST http://localhost:8000/metadata/files \
  -H "Content-Type: application/json" \
  -d '{
    "storage_type": "aws",
    "bucket": "metadataproject",
    "path": "test-data/sample-data/delta/sales_delta",
    "format": "delta"
  }' | jq '.data | {file_count, total_size_bytes, files: .files[:5]}'
```

---

## 🐳 Docker Management

### Start Services
```bash
docker-compose up -d
```

### Stop Services
```bash
docker-compose down
```

### Restart Specific Service
```bash
docker-compose restart trino
docker-compose restart minio
```

### View Logs
```bash
docker logs lakehouse-trino
docker logs lakehouse-minio --follow
```

### Check Status
```bash
docker ps
docker-compose ps
```

### Stop and Remove Everything (including data!)
```bash
docker-compose down -v
```

---

## 🧰 Tech Stack

| Component | Technology | Version |
|-----------|------------|---------|
| **API Framework** | FastAPI | 0.109.0 |
| **Server** | Uvicorn | 0.27.0 |
| **Read Engine** | Trino | Latest |
| **Write Engine** | Apache Spark | 3.5.0 |
| **Storage** | S3 / MinIO | Latest |
| **Formats** | Delta, Iceberg, Hudi, Parquet | - |
| **Routing** | MCP Server | Custom |
| **Language** | Python | 3.12+ |
| **Containerization** | Docker | Latest |

---

## 🧾 Development Phases

This project is built incrementally with each phase committed separately:

- [x] **Phase 0:** Architecture & Theory
- [x] **Phase 1:** Environment Setup (Docker, structure, configs)
- [x] **Phase 2:** FastAPI Skeleton (logging, settings, health endpoints)
- [x] **Phase 3:** AWS Credential Validation (S3 connectivity testing)
- [x] **Phase 4:** Table Format Detection (Delta/Iceberg/Hudi/Parquet)
- [x] **Phase 5:** Metadata Readers (schema, partitions, snapshots, files)
- [ ] **Phase 6:** Trino Integration (READ queries)
- [ ] **Phase 7:** Spark Integration (WRITE queries)
- [ ] **Phase 8:** MCP Server (intelligent query routing)
- [ ] **Phase 9:** Snapshot Comparison
- [ ] **Phase 10:** LLM Integration (Optional)
- [ ] **Phase 11:** Frontend (React/Next.js)

---

## 🔧 Troubleshooting

### Docker not running
**Error:** `error during connect: Get "http://%2F%2F.%2Fpipe%2FdockerDesktopLinuxEngine"`

**Solution:** Start Docker Desktop and wait ~30 seconds for it to fully initialize.

### Trino configuration errors
**Error:** `Configuration property 'hive.s3.aws-access-key' was not used`

**Solution:** We've removed catalog configs temporarily. They'll be added back in Phase 6 with correct configuration.

### Port already in use
**Error:** `Bind for 0.0.0.0:8000 failed: port is already allocated`

**Solution:** 
```bash
# Windows
Get-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess | Stop-Process

# Linux/Mac
lsof -ti:8000 | xargs kill -9
```

### AWS credentials invalid
**Error:** `InvalidAccessKeyId` or `SignatureDoesNotMatch`

**Solution:** 
1. Verify credentials in `.env` file
2. Check AWS IAM permissions (need `s3:ListBucket`, `s3:GetObject`)
3. Test with `/connect/aws` endpoint first

### MinIO bucket not found
**Solution:** The `/connect/minio` endpoint auto-creates buckets. Or create manually:
1. Open http://localhost:9001
2. Login: minioadmin / minioadmin
3. Click "Buckets" → "Create Bucket"
4. Enter name: `lakehouse`

---

## 📚 Learning Resources

- [Delta Lake Transaction Log Protocol](https://github.com/delta-io/delta/blob/master/PROTOCOL.md)
- [Apache Iceberg Table Spec](https://iceberg.apache.org/spec/)
- [Apache Hudi Documentation](https://hudi.apache.org/docs/overview)
- [Trino Documentation](https://trino.io/docs/current/)
- [PySpark Documentation](https://spark.apache.org/docs/latest/api/python/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

---

## 🤝 Contributing

This is a learning project built step-by-step. Each phase is committed separately to show progression.

### Commit Convention
```
feat: Phase X - Description
fix: Bug description
docs: Documentation update
```

---

## 📄 License

MIT License - Educational purposes

---

## 🎓 Author

Built as a hands-on learning project for understanding lakehouse architecture, distributed systems, and data platform engineering.

**GitHub Repository:** https://github.com/AshishDeshmukh674/META_DATA

---

**Last Updated:** Phase 5 Complete (Metadata Exploration)  
**Next Phase:** Phase 6 - Trino Integration (SQL READ Queries)

---

## 📋 Quick Reference: Phase 5 Summary

### What Phase 5 Does
Extracts metadata directly from lakehouse table files without a metastore.

### Supported Formats
- ✅ **Delta Lake** - Reads `_delta_log/*.json` transaction logs
- ✅ **Apache Iceberg** - Reads `metadata/*.json` metadata files
- ✅ **Apache Hudi** - Reads `.hoodie/` timeline and properties
- ✅ **Parquet** - Uses PyArrow to read file metadata

### Available Endpoints
| Endpoint | Purpose | Response Time* |
|----------|---------|----------------|
| `POST /metadata/schema` | Get column names and types | ~3-4s |
| `POST /metadata/snapshots` | Get version history | ~2-3s |
| `POST /metadata/partitions` | Get partition info | ~2-3s |
| `POST /metadata/files` | List all data files | ~2-3s |

*Response times measured with AWS S3 Delta Lake table (127 files, ~4.5GB)

### Common Use Cases

**1. Schema Discovery**
```powershell
# Find out what columns a table has
POST /metadata/schema
→ Returns: column names, data types, nullable, partition columns
```

**2. Time Travel / Auditing**
```powershell
# See all changes to a table over time
POST /metadata/snapshots
→ Returns: version history, operations, who/when changed
```

**3. Data Organization Analysis**
```powershell
# Understand how data is partitioned
POST /metadata/partitions
→ Returns: partition columns, all partition values
```

**4. Storage Analysis**
```powershell
# See file count and sizes
POST /metadata/files
→ Returns: all file paths, sizes, partition assignments
```

### Real Output Examples

**Schema Response:**
```json
{
  "table_format": "delta",
  "data": {
    "schema": {
      "fields": [
        {"name": "id", "type": "integer"},
        {"name": "name", "type": "string"},
        {"name": "price", "type": "double"}
      ]
    },
    "partition_columns": ["region", "date"]
  }
}
```

**Files Response:**
```json
{
  "table_format": "delta",
  "data": {
    "file_count": 127,
    "total_size_bytes": 4589234567,
    "files": [
      {
        "path": "region=us-east/part-00000.parquet",
        "size": 45892345,
        "partition_values": {"region": "us-east"}
      }
    ]
  }
}
```

