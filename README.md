# 🏔️ Lakehouse Explorer & SQL Platform

A **metastore-less** lakehouse platform that discovers and queries Delta, Iceberg, Hudi, and Parquet tables directly from S3/MinIO storage.

## 🎯 What This Does

- ✅ **Discover** lakehouse tables without a metastore (no Hive/Glue/Unity Catalog)
- ✅ **Query** using Trino (fast reads) or Spark (writes)
- ✅ **Explore** metadata, schemas, partitions, and snapshots
- ✅ **Route** queries intelligently via MCP Server
- ✅ **Test** everything via FastAPI endpoints

## 🧠 Architecture

```
User → FastAPI → MCP Server → Trino (READ) / Spark (WRITE) → S3/MinIO
                              ↓
                         Direct S3 API (metadata)
```

**Key Innovation:** Metadata is stored alongside data (Delta's `_delta_log/`, Iceberg's `metadata/`, etc.) — no separate metastore needed!

## 🚀 Quick Start

### 1️⃣ Clone & Setup

```bash
git clone <your-repo>
cd META
```

### 2️⃣ Create Virtual Environment

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1  # Windows
source .venv/bin/activate   # Linux/Mac
```

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 4️⃣ Configure Environment

```bash
cp .env.example .env
# Edit .env with your AWS credentials or MinIO settings
```

### 5️⃣ Start Infrastructure (Docker)

```bash
docker-compose up -d
```

This starts:
- **MinIO** (S3-compatible storage) on `localhost:9000`
- **Trino** (query engine) on `localhost:8080`

### 6️⃣ Run API Server

```bash
uvicorn app.main:app --reload --port 8000
```

API docs available at: http://localhost:8000/docs

## 📂 Project Structure

```
META/
├── app/
│   ├── api/           # FastAPI routers & endpoints
│   ├── core/          # Config, logging, utilities
│   ├── engines/       # Trino & Spark clients
│   ├── metadata/      # Delta/Iceberg/Hudi/Parquet readers
│   └── mcp/           # Query routing logic
├── config/            # YAML configs
├── tests/             # Unit & integration tests
├── docs/              # Architecture & design docs
└── logs/              # Application logs
```

## 🔌 API Endpoints (Phase by Phase)

### Phase 3: Connection Management
- `POST /connect/aws` - Validate AWS credentials
- `POST /connect/minio` - Validate MinIO connection

### Phase 4: Table Discovery
- `POST /detect-format` - Detect table format (Delta/Iceberg/Hudi/Parquet)

### Phase 5: Metadata Exploration
- `GET /metadata/schema` - Get table schema
- `GET /metadata/partitions` - List partitions
- `GET /metadata/snapshots` - List snapshots
- `GET /metadata/files` - List data files

### Phase 6-7: Query Execution
- `POST /query/execute` - Execute SQL (MCP routes to Trino or Spark)

### Phase 9: Snapshot Operations
- `GET /snapshots/diff` - Compare two snapshots

### Health & Debug
- `GET /health` - System health check
- `GET /logs` - Recent logs

## 🧪 Development Phases

This project is built incrementally:

- [x] **Phase 0:** Architecture & Theory
- [x] **Phase 1:** Environment Setup
- [ ] **Phase 2:** FastAPI Skeleton
- [ ] **Phase 3:** AWS Credential Validation
- [ ] **Phase 4:** Table Format Detection
- [ ] **Phase 5:** Metadata Readers
- [ ] **Phase 6:** Trino Integration
- [ ] **Phase 7:** Spark Integration
- [ ] **Phase 8:** MCP Server
- [ ] **Phase 9:** Snapshot Comparison
- [ ] **Phase 10:** LLM Integration (Optional)
- [ ] **Phase 11:** Frontend

## 🧰 Tech Stack

| Component | Technology |
|-----------|------------|
| API Framework | FastAPI |
| Read Engine | Trino |
| Write Engine | Apache Spark |
| Storage | S3 / MinIO |
| Formats | Delta, Iceberg, Hudi, Parquet |
| Routing | MCP Server |
| Language | Python 3.12 |

## 📚 Learning Resources

- [Delta Lake Transaction Log Protocol](https://github.com/delta-io/delta/blob/master/PROTOCOL.md)
- [Iceberg Table Spec](https://iceberg.apache.org/spec/)
- [Trino Documentation](https://trino.io/docs/current/)
- [PySpark Documentation](https://spark.apache.org/docs/latest/api/python/)

## 🤝 Contributing

This is a learning project. Each phase is committed separately to show progression.

## 📄 License

MIT License - Educational purposes

---

**Built with ❤️ as a hands-on learning project for lakehouse architecture**
