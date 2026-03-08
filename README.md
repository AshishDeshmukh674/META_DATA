# 🏔️ Lakehouse Explorer - AI-Powered Data Platform

**A production-ready data lakehouse platform that automatically discovers, manages, and queries Delta Lake tables on AWS S3 using natural language - no SQL knowledge or metastore setup required.**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.109.0-009688.svg)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14.1.0-000000.svg)](https://nextjs.org)
[![Apache Spark](https://img.shields.io/badge/Apache%20Spark-3.5.1-E25A1C.svg)](https://spark.apache.org)
[![Delta Lake](https://img.shields.io/badge/Delta%20Lake-3.2.0-003366.svg)](https://delta.io)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB.svg)](https://python.org)

---

## 📑 Table of Contents

- [Project Overview](#-project-overview)
- [Key Features](#-key-features)
- [Architecture](#️-architecture)
- [Tech Stack](#-tech-stack)
- [Prerequisites](#-prerequisites)
- [Installation & Setup](#️-installation--setup)
- [Running the Project](#-running-the-project)
- [API Documentation](#-api-documentation)
- [Frontend Pages](#-frontend-pages)
- [Usage Examples](#-usage-examples)
- [Project Structure](#-project-structure)
- [Troubleshooting](#-troubleshooting)

---

## 📖 Project Overview

### What is Lakehouse Explorer?

Lakehouse Explorer is an enterprise-grade data platform that bridges the gap between technical and non-technical users. It enables anyone to discover, query, and manage data stored in modern lakehouse formats (Delta Lake, Iceberg, Hudi, Parquet) on AWS S3 without requiring:

- ❌ Complex metastore setup (Hive, Glue Catalog)
- ❌ SQL knowledge
- ❌ Manual table registration
- ❌ Expensive managed services

### The Problem We Solved

**Traditional Data Lakehouse Challenges:**

1. **Metadata Management** - Requires external metastores (Hive, AWS Glue) that are complex to set up and maintain
2. **Technical Barrier** - Non-technical users cannot access data without SQL knowledge
3. **Discovery** - Finding and understanding available datasets is difficult
4. **Version Control** - Tracking data changes and time travel capabilities are hidden in technical logs
5. **Query Performance** - Single query engine can't optimize for both fast queries and historical snapshots

### Our Solution

✅ **Metastore-less Architecture** - Reads metadata directly from Delta Lake's `_delta_log/` transaction logs  
✅ **AI-Powered Natural Language Queries** - Ask questions in plain English using Groq LLM  
✅ **Automatic Discovery** - Detects table format and reads schema automatically  
✅ **Dual Query Engines** - Spark for time travel + Trino for fast analytics  
✅ **Custom Snapshot System** - Business-friendly versioning with rich metadata  
✅ **Write Operations** - UPDATE/INSERT/DELETE via natural language  
✅ **Modern Web UI** - React-based frontend with real-time results  
✅ **REST API** - Easy integration with existing systems  

---

## 🎯 Key Features

### 1. **Automatic Metadata Discovery**
- Detects table format (Delta Lake, Iceberg, Hudi, Parquet)
- Reads schema, partitions, and statistics from `_delta_log/`
- No manual registration or configuration required
- Works with any S3-compatible storage (AWS S3, MinIO)

### 2. **Natural Language Queries (AI-Powered)**
- **Read Operations**: "Show me all customers from Mumbai"
- **Aggregations**: "Count customers by city"
- **Filters**: "Find customers with gmail email addresses"
- **Updates**: "Set name to 'John Doe' where customer ID is C001"
- **Inserts**: "Add a new customer with ID C100, name Sarah"
- **Deletes**: "Delete customer with ID C999"
- Powered by **Groq API** with Llama 3.3 70B model (800ms response time)
- Automatically generates optimized SQL
- Returns results in JSON format with explanation

### 3. **Custom Snapshot System**
- Create named snapshots of Delta tables with rich metadata
- Store in `.metadata-snapshots/` alongside data
- Track schema evolution, file counts, row counts, data size
- Enable time travel for business users
- Compare snapshots to understand data changes over time
- Supports versioning and rollback capabilities

### 4. **Dual Query Engine**
- **Apache Spark 3.5.1** - For snapshot queries and historical data access (supports time travel)
- **Trino 435** - For fast queries on current data (100ms response time)
- Automatic query routing based on operation type
- One-time sync endpoint to register tables in Trino catalog

### 5. **Write Operations (Delta Lake ACID)**
- UPDATE records based on conditions
- INSERT new records
- DELETE existing records
- All operations use Delta Lake's ACID transactions
- Automatic transaction log management
- Support for complex WHERE clauses

### 6. **Modern Web UI**
- **Explorer**: Browse S3 buckets and discover tables
- **Metadata Viewer**: See schema, statistics, and table information
- **Natural Language Query**: Ask questions in plain English with AI
- **SQL Query**: Execute custom SQL with Trino for fast results
- **Snapshot Manager**: Create, view, and compare snapshots
- **Settings**: Configure AWS credentials and storage backends

---

## 🏗️ Architecture

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                          Frontend (Next.js 14)                       │
│                           Port: 3001                                 │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌─────────┐ │
│  │ Explorer │ │ Metadata │ │ NL Query │ │ SQL Query│ │Snapshots│ │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └─────────┘ │
└─────────────────────────────┬───────────────────────────────────────┘
                              │ REST API
┌─────────────────────────────┴───────────────────────────────────────┐
│                       Backend (FastAPI)                              │
│                        Port: 8000                                   │
│  ┌───────────────────────────────────────────────────────────┐     │
│  │            API Layer (REST Endpoints)                      │     │
│  │  • Health   • Connection   • Detect   • Metadata          │     │
│  │  • Metadata Gen   • Query (Natural Language + SQL)        │     │
│  └──────────────┬────────────────────┬───────────────────────┘     │
│                 │                    │                             │
│  ┌──────────────▼──────┐  ┌──────────▼─────────────────────┐      │
│  │  Natural Language   │  │    Query Engines                │      │
│  │  Engine (Groq API)  │  │  ┌──────────┐  ┌──────────┐    │      │
│  │  llama-3.3-70b      │  │  │  Spark   │  │  Trino   │    │      │
│  │                     │  │  │  Query   │  │  Query   │    │      │
│  │  NL → SQL           │  │  │  Engine  │  │  Engine  │    │      │
│  │  (800ms)            │  │  └──────────┘  └──────────┘    │      │
│  └─────────────────────┘  └───────────────────────────┘      │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │          Metadata & Snapshot Management                      │   │
│  │  • spark_metadata_engine.py - Delta log reader             │   │
│  │  • Snapshot creation and versioning                        │   │
│  │  • Schema extraction and statistics                        │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
┌─────────────────────────────┴───────────────────────────────────────┐
│                      Apache Spark Cluster                            │
│                      (Dockerized)                                   │
│  ┌──────────────────┐          ┌──────────────────┐                │
│  │  Spark Master    │          │  Spark Worker    │                │
│  │  Port: 7077      │◄─────────│  2G RAM, 2 Cores │                │
│  │  UI: 8081        │          │                  │                │
│  └──────────────────┘          └──────────────────┘                │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
┌─────────────────────────────┴───────────────────────────────────────┐
│                         AWS S3 Storage                               │
│                    Bucket: metadataproject                          │
│                                                                     │
│  test-data/customer_data/customer_data_delta/                      │
│  ├── _delta_log/                  # Delta Lake transaction logs    │
│  │   ├── 00000000000000000000.json                                │
│  │   ├── 00000000000000000001.json                                │
│  │   └── ...                                                       │
│  ├── .metadata-snapshots/         # Our custom snapshots           │
│  │   ├── snapshot_20260301_120000_abc123.json                     │
│  │   └── snapshot_20260301_130000_def456.json                     │
│  └── part-00000-*.parquet         # Actual data files              │
└─────────────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **User Request** → Frontend sends natural language query
2. **API Gateway** → FastAPI receives request and routes to appropriate handler
3. **NL Processing** → Groq LLM converts natural language to SQL
4. **Query Routing** → System decides between Spark (time travel) or Trino (fast)
5. **Execution** → Query engine reads from S3 and executes SQL
6. **Response** → Results returned with metadata and explanation

---

## 🛠️ Tech Stack

### Backend
- **FastAPI 0.109.0** - Modern Python web framework for APIs
- **Python 3.12** - Core programming language
- **PySpark 3.5.1** - Distributed data processing
- **Delta Lake 3.2.0** - ACID transactions on data lakes
- **Groq API** - AI-powered natural language processing (llama-3.3-70b-versatile)
- **Trino** - Fast distributed SQL query engine
- **Boto3** - AWS SDK for S3 access

### Frontend
- **Next.js 14.1.0** - React framework with server-side rendering
- **React 18** - UI component library
- **TypeScript** - Type-safe JavaScript
- **Tailwind CSS** - Utility-first CSS framework
- **Shadcn/UI** - High-quality UI components

### Infrastructure
- **Docker & Docker Compose** - Containerization
- **Apache Spark 3.5.1** - Distributed computing cluster
- **Java 17** - Required for Spark
- **Hadoop AWS 3.3.4** - S3A filesystem support

### Storage
- **AWS S3** - Object storage for data lakes
- **Delta Lake** - Storage format with ACID properties

---

## 📋 Prerequisites

### Required Software

1. **Python 3.12+**
   ```powershell
   python --version
   # Should show: Python 3.12.x
   ```

2. **Java 17** (Required for Apache Spark)
   ```powershell
   java -version
   # Should show: openjdk version "17.x.x"
   ```
   
   **Download:** [Amazon Corretto 17](https://docs.aws.amazon.com/corretto/latest/corretto-17-ug/downloads-list.html)

3. **Node.js 18+** (For frontend)
   ```powershell
   node --version
   # Should show: v18.x.x or higher
   ```
   
   **Download:** [Node.js Official](https://nodejs.org/)

4. **Docker Desktop**
   - **Download:** [Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows-install/)
   - Ensure Docker is running before starting the project

### AWS Credentials

You'll need AWS credentials with S3 access:
- AWS Access Key ID
- AWS Secret Access Key
- S3 Bucket Name

### Groq API Key (For Natural Language Queries)

Get a free API key from [Groq Console](https://console.groq.com/keys)

---

## 🚀 Installation & Setup

### Step 1: Clone the Repository

```powershell
git clone <repository-url>
cd META
```

### Step 2: Java Setup (Required for Spark)

1. **Download Java 17:**
   - Go to [Amazon Corretto 17](https://docs.aws.amazon.com/corretto/latest/corretto-17-ug/downloads-list.html)
   - Download the Windows x64 MSI installer
   - Install with default settings

2. **Set JAVA_HOME Environment Variable:**
   ```powershell
   # Check Java installation
   java -version
   
   # Find Java installation path
   where java
   # Example: C:\Program Files\Amazon Corretto\jdk17.0.x\bin\java.exe
   
   # Set JAVA_HOME (adjust path as needed)
   setx JAVA_HOME "C:\Program Files\Amazon Corretto\jdk17.0.x"
   
   # Verify
   echo $env:JAVA_HOME
   ```

3. **Add to PATH:**
   ```powershell
   # Add Java bin to PATH
   setx PATH "$env:PATH;$env:JAVA_HOME\bin"
   ```

### Step 3: Spark Configuration

Spark is automatically configured via Docker. The setup includes:
- Spark Master on port 7077
- Spark Worker with 2G RAM and 2 cores
- Spark UI accessible at http://localhost:8081

**Docker Compose Configuration:**
```yaml
spark-master:
  image: apache/spark:3.5.1
  ports:
    - "7077:7077"   # Spark master
    - "8081:8080"   # Spark UI

spark-worker:
  image: apache/spark:3.5.1
  environment:
    - SPARK_WORKER_MEMORY=2G
    - SPARK_WORKER_CORES=2
```

### Step 4: Python Backend Setup

1. **Create Virtual Environment:**
   ```powershell
   python -m venv .venv
   ```

2. **Activate Virtual Environment:**
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

3. **Install Dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```

### Step 5: Environment Configuration

1. **Create `.env` file:**
   ```powershell
   Copy-Item .env.example .env
   ```

2. **Edit `.env` with your credentials:**
   ```env
   # AWS Configuration
   AWS_ACCESS_KEY_ID=your_access_key_here
   AWS_SECRET_ACCESS_KEY=your_secret_key_here
   AWS_REGION=us-east-1
   AWS_S3_BUCKET=your_bucket_name

   # Groq API (Natural Language Queries)
   GROQ_API_KEY=gsk_your_groq_api_key_here

   # Spark Configuration
   SPARK_MASTER=spark://localhost:7077

   # API Configuration
   API_HOST=0.0.0.0
   API_PORT=8000
   ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001
   ```

### Step 6: Frontend Setup

```powershell
cd frontend
npm install
cd ..
```

### Step 7: Docker Setup

Ensure Docker Desktop is running, then build the containers:

```powershell
docker-compose build
```

---

## 🏃 Running the Project

### Option 1: Start Everything with Docker Compose (Recommended)

```powershell
# Start all services (backend, Spark master, Spark worker)
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f fastapi
```

**Services Started:**
- FastAPI Backend: http://localhost:8000
- Spark Master: http://localhost:7077
- Spark UI: http://localhost:8081

### Option 2: Start Services Individually

**1. Start Spark Cluster:**
```powershell
docker-compose up -d spark-master spark-worker
```

**2. Start Backend:**
```powershell
# Option A: With Docker
docker-compose up -d fastapi

# Option B: Locally (for development)
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**3. Start Frontend:**
```powershell
cd frontend
npm run dev
```

### Accessing the Services

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:3001 | Web UI |
| Backend API | http://localhost:8000 | REST API |
| API Documentation | http://localhost:8000/docs | Swagger UI |
| Spark Master UI | http://localhost:8081 | Spark Cluster Status |

### Stopping Services

```powershell
# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

---

## 📡 API Documentation

### Base URL
```
http://localhost:8000
```

### Authentication
Currently, the API does not require authentication (suitable for development/internal use).

---

### 1. Health Check API

**Purpose:** Verify that the backend service is running and healthy.

#### `GET /health`

**Description:** Returns service health status with timestamp and version.

**Request:**
```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-03-08T10:30:00Z",
  "service": "LakehouseExplorer",
  "version": "0.1.0"
}
```

**Status Codes:**
- `200 OK` - Service is healthy

---

### 2. Connection Test API

**Purpose:** Test AWS S3 connectivity and validate credentials.

#### `POST /connection/test`

**Description:** Tests connection to AWS S3 by attempting to list buckets.

**Request Body:**
```json
{
  "storage_type": "aws",
  "endpoint": null,
  "access_key": "AKIA...",
  "secret_key": "wJal...",
  "bucket": "metadataproject",
  "region": "us-east-1"
}
```

**Request:**
```bash
curl -X POST http://localhost:8000/connection/test \
  -H "Content-Type: application/json" \
  -d '{
    "storage_type": "aws",
    "access_key": "AKIA...",
    "secret_key": "wJal...",
    "bucket": "metadataproject",
    "region": "us-east-1"
  }'
```

**Response (Success):**
```json
{
  "success": true,
  "message": "Successfully connected to AWS S3",
  "bucket_accessible": true,
  "region": "us-east-1"
}
```

**Response (Failure):**
```json
{
  "success": false,
  "message": "Failed to connect: Invalid credentials",
  "bucket_accessible": false
}
```

**Status Codes:**
- `200 OK` - Connection successful
- `400 Bad Request` - Invalid parameters
- `500 Internal Server Error` - Connection failed

---

### 3. Table Format Detection API

**Purpose:** Automatically detect the format of a table (Delta Lake, Iceberg, Hudi, or Parquet).

#### `POST /detect/format`

**Description:** Analyzes S3 path structure to determine table format.

**Request Body:**
```json
{
  "storage_type": "aws",
  "bucket": "metadataproject",
  "table_path": "test-data/customer_data/customer_data_delta"
}
```

**Request:**
```bash
curl -X POST http://localhost:8000/detect/format \
  -H "Content-Type: application/json" \
  -d '{
    "storage_type": "aws",
    "bucket": "metadataproject",
    "table_path": "test-data/customer_data/customer_data_delta"
  }'
```

**Response:**
```json
{
  "format": "delta",
  "confidence": "high",
  "indicators": {
    "has_delta_log": true,
    "has_metadata_folder": false,
    "has_parquet_files": true
  },
  "table_path": "test-data/customer_data/customer_data_delta",
  "recommended_actions": [
    "Use Delta Lake APIs for reading",
    "ACID transactions supported",
    "Time travel available via _delta_log"
  ]
}
```

**Supported Formats:**
- `delta` - Delta Lake
- `iceberg` - Apache Iceberg
- `hudi` - Apache Hudi
- `parquet` - Plain Parquet files

**Status Codes:**
- `200 OK` - Format detected
- `404 Not Found` - Table path not found
- `500 Internal Server Error` - Detection failed

---

### 4. Metadata Discovery API

**Purpose:** Read and extract metadata from Delta Lake transaction logs without a metastore.

#### `POST /metadata/read`

**Description:** Reads `_delta_log/` to extract schema, partitions, statistics, and table properties.

**Request Body:**
```json
{
  "storage_type": "aws",
  "bucket": "metadataproject",
  "table_path": "test-data/customer_data/customer_data_delta",
  "table_format": "delta"
}
```

**Request:**
```bash
curl -X POST http://localhost:8000/metadata/read \
  -H "Content-Type: application/json" \
  -d '{
    "storage_type": "aws",
    "bucket": "metadataproject",
    "table_path": "test-data/customer_data/customer_data_delta",
    "table_format": "delta"
  }'
```

**Response:**
```json
{
  "success": true,
  "table_format": "delta",
  "schema": [
    {
      "name": "CustomerId",
      "type": "string",
      "nullable": false,
      "metadata": {}
    },
    {
      "name": "Name",
      "type": "string",
      "nullable": true,
      "metadata": {}
    },
    {
      "name": "Email",
      "type": "string",
      "nullable": true,
      "metadata": {}
    }
  ],
  "partition_columns": [],
  "num_files": 1,
  "size_bytes": 1547,
  "row_count": 10,
  "delta_version": 0,
  "table_properties": {
    "delta.minReaderVersion": "1",
    "delta.minWriterVersion": "2"
  }
}
```

**Status Codes:**
- `200 OK` - Metadata retrieved
- `404 Not Found` - Table not found
- `500 Internal Server Error` - Failed to read metadata

---

### 5. Snapshot Management API

**Purpose:** Create, list, and manage custom snapshots of Delta Lake tables.

#### `POST /metadata/generate-snapshot`

**Description:** Creates a new snapshot with rich metadata and stores it in `.metadata-snapshots/`.

**Request Body:**
```json
{
  "storage_type": "aws",
  "bucket": "metadataproject",
  "source_path": "raw/customer_data.csv",
  "source_format": "csv",
  "target_path": "tables/customer_data_delta",
  "snapshot_name": "Initial Customer Data Load",
  "description": "First snapshot of customer data from CSV",
  "tags": ["production", "customer-data", "initial-load"]
}
```

**Request:**
```bash
curl -X POST http://localhost:8000/metadata/generate-snapshot \
  -H "Content-Type: application/json" \
  -d '{
    "storage_type": "aws",
    "bucket": "metadataproject",
    "source_path": "raw/customer_data.csv",
    "source_format": "csv",
    "target_path": "tables/customer_data_delta",
    "snapshot_name": "Initial Customer Data Load"
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "Snapshot created successfully",
  "snapshot_id": "snapshot_20260308_103000_abc123de",
  "snapshot_path": "s3://metadataproject/tables/customer_data_delta/.metadata-snapshots/snapshot_20260308_103000_abc123de.json",
  "delta_version": 0,
  "statistics": {
    "row_count": 10,
    "file_count": 1,
    "size_bytes": 1547,
    "columns": 5
  }
}
```

#### `GET /metadata/list-snapshots`

**Description:** List all available snapshots for a table.

**Query Parameters:**
- `storage_type` - Storage backend (aws/minio)
- `bucket` - S3 bucket name
- `table_path` - Path to Delta table

**Request:**
```bash
curl "http://localhost:8000/metadata/list-snapshots?storage_type=aws&bucket=metadataproject&table_path=tables/customer_data_delta"
```

**Response:**
```json
{
  "success": true,
  "snapshots": [
    {
      "snapshot_id": "snapshot_20260308_103000_abc123de",
      "name": "Initial Customer Data Load",
      "description": "First snapshot of customer data from CSV",
      "created_at": "2026-03-08T10:30:00Z",
      "delta_version": 0,
      "row_count": 10,
      "size_bytes": 1547,
      "tags": ["production", "customer-data", "initial-load"]
    }
  ],
  "total_snapshots": 1
}
```

**Status Codes:**
- `200 OK` - Snapshot created/listed
- `400 Bad Request` - Invalid parameters
- `500 Internal Server Error` - Operation failed

---

### 6. Natural Language Query API

**Purpose:** Execute queries using plain English powered by AI (Groq LLM).

#### `POST /query/natural-language`

**Description:** Converts natural language questions to SQL and executes them.

**Request Body:**
```json
{
  "storage_type": "aws",
  "bucket": "metadataproject",
  "table_path": "test-data/customer_data/customer_data_delta",
  "question": "Show me all customers from Mumbai"
}
```

**Request:**
```bash
curl -X POST http://localhost:8000/query/natural-language \
  -H "Content-Type: application/json" \
  -d '{
    "storage_type": "aws",
    "bucket": "metadataproject",
    "table_path": "test-data/customer_data/customer_data_delta",
    "question": "Show me all customers from Mumbai"
  }'
```

**Response:**
```json
{
  "success": true,
  "question": "Show me all customers from Mumbai",
  "generated_sql": "SELECT * FROM query_table WHERE City = 'Mumbai' LIMIT 100",
  "data": [
    {
      "CustomerId": "C001",
      "Name": "Raj Patel",
      "Email": "raj@example.com",
      "City": "Mumbai",
      "Age": 28
    }
  ],
  "columns": ["CustomerId", "Name", "Email", "City", "Age"],
  "row_count": 1,
  "execution_time_ms": 1847,
  "explanation": "Selecting all customers where city is Mumbai"
}
```

**Supported Query Types:**

**1. Read Queries (SELECT):**
- "Show me all customers"
- "Count customers by city"
- "Find customers with gmail email addresses"
- "Get top 10 customers by age"

**2. Update Queries:**
- "Set name to 'John Doe' where customer ID is C001"
- "Update email to test@example.com for all customers in Mumbai"

**3. Insert Queries:**
- "Add a new customer with ID C100, name Sarah, email sarah@test.com"
- "Insert customer with ID C200, name Mike, city Delhi"

**4. Delete Queries:**
- "Delete customer with ID C999"
- "Remove all customers from Delhi"

**Status Codes:**
- `200 OK` - Query executed
- `400 Bad Request` - Invalid question or failed to generate SQL
- `500 Internal Server Error` - Query execution failed

---

## 🖥️ Frontend Pages

### 1. **Explorer Page** (`/explorer`)

**Purpose:** Browse S3 buckets and discover tables.

**Features:**
- List all prefixes/folders in S3 bucket
- Navigate through directory structure
- Detect table format automatically
- View table preview

**How to Use:**
1. Go to http://localhost:3001/explorer
2. Enter bucket name and optional prefix
3. Click "List Objects"
4. Navigate through folders
5. Click on a table to see format detection

---

### 2. **Metadata Page** (`/metadata`)

**Purpose:** View detailed metadata about Delta Lake tables.

**Features:**
- Read schema from `_delta_log/`
- Display column names, types, and nullability
- Show partition columns
- Display table statistics (file count, size, rows)
- View Delta Lake version and properties

**How to Use:**
1. Go to http://localhost:3001/metadata
2. Select storage type (AWS/MinIO)
3. Enter bucket name and table path
4. Click "Read Metadata"
5. View schema and statistics

---

### 3. **Natural Language Query Page** (`/natural-language`)

**Purpose:** Ask questions in plain English and get SQL results.

**Features:**
- AI-powered query generation (Groq LLM)
- Sample questions for quick start
- Generated SQL display
- Results table with sorting
- Full JSON response viewer
- Execution time tracking

**How to Use:**
1. Go to http://localhost:3001/natural-language
2. Configure table settings (storage, bucket, path)
3. Enter your question in plain English
4. Click "Execute Query"
5. View generated SQL and results

**Example Questions:**
- "Show me all rows in the table"
- "Count customers by city"
- "Find customers with gmail email"
- "Update name to 'John' where ID is C001"

---

### 4. **SQL Query Page** (`/sql-query`)

**Purpose:** Execute custom SQL queries using Trino for fast analytics.

**Features:**
- Custom SQL editor
- Query history
- Result table with export
- Query performance metrics
- Syntax highlighting

**How to Use:**
1. Go to http://localhost:3001/sql-query
2. Enter Trino connection details
3. Write custom SQL query
4. Click "Execute"
5. View results and performance metrics

---

### 5. **Snapshots Page** (`/snapshots`)

**Purpose:** Create and manage custom snapshots of Delta tables.

**Features:**
- Create snapshots with metadata
- List all available snapshots
- View snapshot details
- Compare snapshots
- Time travel to historical versions

**How to Use:**
1. Go to http://localhost:3001/snapshots
2. Configure source and target paths
3. Enter snapshot name and description
4. Add optional tags
5. Click "Create Snapshot"
6. View snapshot list and details

---

### 6. **Settings Page** (`/settings`)

**Purpose:** Configure AWS credentials and storage backends.

**Features:**
- Test S3 connection
- Save credentials
- Configure storage type (AWS/MinIO)
- Validate bucket access

**How to Use:**
1. Go to http://localhost:3001/settings
2. Enter AWS credentials
3. Click "Test Connection"
4. Save configuration if successful

---

## 🎓 Usage Examples

### Example 1: Discover and Query a New Table

**Step 1: Test Connection**
```bash
curl -X POST http://localhost:8000/connection/test \
  -H "Content-Type: application/json" \
  -d '{
    "storage_type": "aws",
    "bucket": "metadataproject",
    "region": "us-east-1"
  }'
```

**Step 2: Detect Table Format**
```bash
curl -X POST http://localhost:8000/detect/format \
  -H "Content-Type: application/json" \
  -d '{
    "storage_type": "aws",
    "bucket": "metadataproject",
    "table_path": "test-data/customer_data/customer_data_delta"
  }'
```

**Step 3: Read Metadata**
```bash
curl -X POST http://localhost:8000/metadata/read \
  -H "Content-Type: application/json" \
  -d '{
    "storage_type": "aws",
    "bucket": "metadataproject",
    "table_path": "test-data/customer_data/customer_data_delta",
    "table_format": "delta"
  }'
```

**Step 4: Query with Natural Language**
```bash
curl -X POST http://localhost:8000/query/natural-language \
  -H "Content-Type: application/json" \
  -d '{
    "storage_type": "aws",
    "bucket": "metadataproject",
    "table_path": "test-data/customer_data/customer_data_delta",
    "question": "Show me the first 5 customers"
  }'
```

---

### Example 2: Create a Snapshot

```bash
curl -X POST http://localhost:8000/metadata/generate-snapshot \
  -H "Content-Type: application/json" \
  -d '{
    "storage_type": "aws",
    "bucket": "metadataproject",
    "source_path": "raw/customer_data.csv",
    "source_format": "csv",
    "target_path": "tables/customer_data_delta",
    "snapshot_name": "Q1 2026 Customer Data",
    "description": "Customer data snapshot for Q1 reporting",
    "tags": ["production", "quarterly"]
  }'
```

---

### Example 3: Update Data with Natural Language

```bash
curl -X POST http://localhost:8000/query/natural-language \
  -H "Content-Type: application/json" \
  -d '{
    "storage_type": "aws",
    "bucket": "metadataproject",
    "table_path": "test-data/customer_data/customer_data_delta",
    "question": "Update email to newemail@test.com where customer ID is C001"
  }'
```

---

## 📂 Project Structure

```
META/
├── app/                           # Backend application
│   ├── api/                       # API endpoints
│   │   ├── connection.py          # Connection testing
│   │   ├── detect.py              # Format detection
│   │   ├── health.py              # Health checks
│   │   ├── metadata.py            # Metadata reading
│   │   ├── metadata_gen.py        # Snapshot generation
│   │   └── query.py               # Natural language + SQL queries
│   ├── core/                      # Core configuration
│   │   ├── logger.py              # Structured logging
│   │   └── settings.py            # Environment settings
│   ├── engines/                   # Query & metadata engines
│   │   ├── nl_query_engine.py     # Groq LLM integration
│   │   ├── spark_metadata_engine.py  # Delta log reader
│   │   ├── spark_query_engine.py  # Spark SQL executor
│   │   └── trino_query_engine.py  # Trino query executor
│   └── main.py                    # FastAPI application
├── frontend/                      # Next.js frontend
│   ├── src/
│   │   ├── app/                   # Pages
│   │   │   ├── explorer/          # S3 browser
│   │   │   ├── metadata/          # Metadata viewer
│   │   │   ├── natural-language/  # NL query interface
│   │   │   ├── sql-query/         # SQL editor
│   │   │   ├── snapshots/         # Snapshot manager
│   │   │   └── settings/          # Configuration
│   │   ├── components/            # Reusable UI components
│   │   └── lib/                   # API clients and utilities
│   ├── package.json
│   └── next.config.js
├── docker-compose.yml             # Service orchestration
├── Dockerfile                     # Backend container
├── requirements.txt               # Python dependencies
├── .env                          # Environment variables
└── README.md                     # This file
```

---

## 🐛 Troubleshooting

### Common Issues

#### 1. **Java Not Found**

**Error:**
```
Error: JAVA_HOME is not set
```

**Solution:**
```powershell
# Install Java 17
# Download from: https://docs.aws.amazon.com/corretto/latest/corretto-17-ug/downloads-list.html

# Set JAVA_HOME
setx JAVA_HOME "C:\Program Files\Amazon Corretto\jdk17.0.x"

# Verify
java -version
```

#### 2. **Docker Not Running**

**Error:**
```
Cannot connect to the Docker daemon
```

**Solution:**
- Start Docker Desktop
- Wait for Docker to fully start
- Run `docker ps` to verify

#### 3. **Spark Connection Failed**

**Error:**
```
Failed to connect to Spark master
```

**Solution:**
```powershell
# Check Spark is running
docker-compose ps

# Restart Spark services
docker-compose restart spark-master spark-worker

# Check Spark UI
# Open: http://localhost:8081
```

#### 4. **Missing GROQ_API_KEY**

**Error:**
```
GROQ_API_KEY not set
```

**Solution:**
1. Get API key from https://console.groq.com/keys
2. Add to `.env` file:
   ```env
   GROQ_API_KEY=gsk_your_api_key_here
   ```
3. Restart backend:
   ```powershell
   docker-compose restart fastapi
   ```

#### 5. **AWS Credentials Invalid**

**Error:**
```
Failed to connect: Invalid credentials
```

**Solution:**
1. Verify credentials in `.env`
2. Test with AWS CLI:
   ```powershell
   aws s3 ls s3://your-bucket-name --profile your-profile
   ```
3. Update `.env` with correct credentials
4. Restart backend

#### 6. **Port Already in Use**

**Error:**
```
Port 8000 is already in use
```

**Solution:**
```powershell
# Find process using port
netstat -ano | findstr :8000

# Kill process (replace PID with actual process ID)
taskkill /PID <PID> /F

# Or change port in .env
API_PORT=8001
```

---

## 🔧 Development Commands

### Backend Development

```powershell
# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Run backend locally (hot reload)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
pytest

# Check code formatting
black app/
flake8 app/

# Type checking
mypy app/
```

### Frontend Development

```powershell
cd frontend

# Install dependencies
npm install

# Run development server (hot reload)
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Lint code
npm run lint
```

### Docker Commands

```powershell
# Build services
docker-compose build

# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f fastapi

# Restart specific service
docker-compose restart fastapi

# Remove everything (including volumes)
docker-compose down -v

# Rebuild and restart
docker-compose up -d --build
```

---

## 📝 Environment Variables Reference

```env
# Application
APP_NAME=LakehouseExplorer
APP_VERSION=0.1.0
ENVIRONMENT=development
LOG_LEVEL=INFO

# AWS Configuration
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
AWS_S3_BUCKET=your_bucket_name

# Groq API (Natural Language)
GROQ_API_KEY=gsk_your_groq_api_key

# Spark Configuration
SPARK_MASTER=spark://localhost:7077
SPARK_APP_NAME=LakehouseExplorer
SPARK_DRIVER_MEMORY=2g
SPARK_EXECUTOR_MEMORY=2g

# API Server
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=true
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001

# Security
SECRET_KEY=your_secret_key_here

# Feature Flags
ENABLE_MCP=true
ENABLE_LLM=true
ENABLE_METRICS=true
```

---

## 📄 License

This project is licensed under the MIT License.

---

## 🙏 Acknowledgments

- **Apache Spark** - Distributed computing framework
- **Delta Lake** - ACID transactions for data lakes
- **FastAPI** - Modern Python web framework
- **Next.js** - React framework
- **Groq** - Fast AI inference platform
- **Trino** - Distributed SQL query engine

---

## 📧 Support

For questions or issues, please create an issue in the GitHub repository.

---

**Built with ❤️ for modern data engineering**
