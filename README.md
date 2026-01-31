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

### 🔜 Coming Soon

#### Phase 5: Metadata Exploration
- `GET /metadata/schema` - Get table schema
- `GET /metadata/partitions` - List partitions
- `GET /metadata/snapshots` - List snapshots
- `GET /metadata/files` - List data files

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
- [ ] **Phase 5:** Metadata Readers (schema, partitions, snapshots)
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

**Last Updated:** Phase 4 Complete (Table Format Detection)  
**Next Phase:** Phase 5 - Metadata Readers (Schema, Partitions, Snapshots)
