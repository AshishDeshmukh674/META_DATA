# Phase 6: Spark-Based Metadata Generation Engine

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Implementation Journey: Mistakes & Lessons](#implementation-journey-mistakes--lessons)
4. [Why Docker? The Critical Decision](#why-docker-the-critical-decision)
5. [Docker Setup Guide](#docker-setup-guide)
6. [API Endpoints](#api-endpoints)
7. [Testing Guide](#testing-guide)
8. [Troubleshooting](#troubleshooting)
9. [Technical Specifications](#technical-specifications)

---

## Overview

Phase 6 implements a **Spark-based metadata generation and versioning system** for lakehouse tables stored in S3. The system extracts comprehensive metadata (schema, partitions, files, versions) and saves versioned snapshots that enable:
- Schema evolution tracking
- Data lineage analysis
- Metadata versioning and comparison
- Historical metadata queries

**Key Features:**
- ✅ Multi-format support: Delta Lake, Iceberg, Hudi, Parquet
- ✅ Automated metadata extraction using Apache Spark
- ✅ Versioned snapshots with sortable IDs
- ✅ Co-located storage (`.metadata-snapshots/` folder at table location)
- ✅ RESTful API with 4 endpoints
- ✅ Production-ready Docker deployment

---

## Architecture

### High-Level Design

```
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI Container                       │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  API Layer (app/api/metadata_gen.py)                   │ │
│  │  - POST /metadata/generate                             │ │
│  │  - GET  /metadata/snapshots/latest                     │ │
│  │  - GET  /metadata/snapshots/list                       │ │
│  │  - POST /metadata/snapshots/diff                       │ │
│  └────────────────┬───────────────────────────────────────┘ │
│                   │                                          │
│  ┌────────────────▼───────────────────────────────────────┐ │
│  │  Spark Metadata Engine                                 │ │
│  │  (app/engines/spark_metadata_engine.py)                │ │
│  │  - Creates SparkSession per request                    │ │
│  │  - Connects to Spark cluster via spark://             │ │
│  │  - Extracts schema, partitions, files, versions        │ │
│  └────────────────┬───────────────────────────────────────┘ │
│                   │                                          │
│  ┌────────────────▼───────────────────────────────────────┐ │
│  │  Snapshot Storage Manager                              │ │
│  │  (app/storage/snapshot_manager.py)                     │ │
│  │  - Saves snapshots to S3                               │ │
│  │  - Lists and retrieves snapshots                       │ │
│  │  - Compares snapshot versions                          │ │
│  └────────────────┬───────────────────────────────────────┘ │
└───────────────────┼───────────────────────────────────────┘
                    │
                    │ S3 API calls (boto3)
                    ▼
┌─────────────────────────────────────────────────────────────┐
│                    S3 Storage Layer                          │
│  s3://bucket/table-path/                                     │
│  ├── _delta_log/                   (Delta table metadata)   │
│  ├── part-0001.parquet              (Data files)            │
│  └── .metadata-snapshots/           (Our snapshots)         │
│      ├── snapshot_20260208_140802_d1e6bb63.json             │
│      ├── snapshot_20260208_151030_a3f2c891.json             │
│      └── snapshot_20260208_162145_f7b9d234.json             │
└─────────────────────────────────────────────────────────────┘
                    ▲
                    │ Spark reads table metadata
                    │
┌─────────────────────────────────────────────────────────────┐
│              Spark Cluster (Docker Network)                  │
│  ┌──────────────────┐       ┌──────────────────┐           │
│  │  Spark Master    │◄──────┤  Spark Worker    │           │
│  │  Port: 7077      │       │  2 cores, 2G RAM │           │
│  │  UI: 8081        │       │                  │           │
│  └──────────────────┘       └──────────────────┘           │
└─────────────────────────────────────────────────────────────┘
```

### Component Details

#### 1. **Spark Metadata Engine** (`app/engines/spark_metadata_engine.py`)
- **Per-Request Sessions**: Creates fresh SparkSession for each API request
- **Auto-Cleanup**: Stops Spark session in `finally` block
- **Cluster Connection**: Connects to `spark://spark-master:7077` in Docker network
- **Package Management**: Auto-downloads Delta Lake and Hadoop AWS JARs
- **Metadata Extraction**:
  - Schema: Column names, types, nullability
  - Partitions: Partition columns and count
  - Files: File count, total size, sample paths
  - Version: Table format version (Delta/Iceberg/Hudi)

#### 2. **Snapshot Storage Manager** (`app/storage/snapshot_manager.py`)
- **Snapshot Format**: JSON with comprehensive metadata
- **Storage Pattern**: Co-located at `<table-path>/.metadata-snapshots/`
- **Snapshot ID Format**: `snapshot_YYYYMMDD_HHMMSS_<uuid8>` (sortable + unique)
- **Operations**:
  - `save_snapshot()`: Upload to S3
  - `get_latest_snapshot()`: Retrieve most recent
  - `list_snapshots()`: List all with metadata
  - `compare_snapshots()`: Diff two snapshots

#### 3. **API Router** (`app/api/metadata_gen.py`)
Four endpoints with comprehensive error handling and logging.

#### 4. **Pydantic Schemas** (`app/api/schemas.py`)
Type-safe request/response models for all operations.

---

## Implementation Journey: Mistakes & Lessons

### Timeline of Issues and Solutions

#### **Attempt 1: Windows + PySpark 4.0 + Java 25** ❌
**Goal**: Run Spark locally in Windows with latest versions

**Mistakes Made**:
1. Used Java 25 (too new, incompatible with Hadoop 3.3.x)
2. Assumed PySpark 4.0 would work out-of-the-box on Windows
3. Didn't check Java compatibility matrix

**Errors Encountered**:
```
java.lang.UnsupportedClassVersionError: Compiled by Java 25
```

**Lesson**: Always check compatibility matrices. Spark ecosystem moves slowly; stick with LTS Java versions.

---

#### **Attempt 2: Downgrade to Java 17** ❌
**Changes**: Installed Java 17 LTS, set `JAVA_HOME`

**New Issues**:
1. Missing Hadoop native libraries for Windows
2. `winutils.exe` not found
3. Hadoop requires Windows-specific binaries

**Errors Encountered**:
```
WARN NativeCodeLoader: Unable to load native-hadoop library for your platform
Could not locate winutils.exe
```

**Solution Tried**:
- Downloaded `winutils.exe` to `C:\hadoop\bin`
- Set `HADOOP_HOME=C:\hadoop`

**Lesson**: Hadoop on Windows requires extra setup that's platform-specific and fragile.

---

#### **Attempt 3: Configure Windows Environment** ❌
**Changes**: Added environment variables, configured paths

**New Critical Issue**:
**Hadoop "60s" Timeout Parsing Bug**: Hadoop 3.3.x configuration files contain timeout values as strings like `"60s"`, but Spark 4.0's Java timeout parser expects numeric milliseconds.

**Error**:
```
java.lang.NumberFormatException: For input string: "60s"
```

**Solution Tried**:
1. Created custom `C:\hadoop\etc\hadoop\core-site.xml` with numeric values
2. Set `HADOOP_CONF_DIR` environment variable
3. Attempted post-session config override

**Result**: Failed. Spark loads JARs with bundled configs before our custom config.

**Lesson**: When Spark bundles Hadoop JARs, your external configs are often ignored.

---

#### **Attempt 4: Change Hadoop Version** ❌
**Changes**: Tried `hadoop-aws:3.2.0`, `hadoop-aws:3.3.1`, `hadoop-aws:3.3.5`

**Issues**:
- 3.2.0: Different credential provider error
- 3.3.1: Same "60s" parsing bug
- 3.3.5: "60s" parsing bug + other issues

**Lesson**: The bug exists across multiple Hadoop 3.3.x versions. Version juggling wasn't the solution.

---

#### **Attempt 5: PySpark 4.0 NullPointerException** ❌ 🚨 **CRITICAL BLOCKER**
**Issue**: Even after fixing Hadoop configs, Spark 4.0 on Windows hit a critical internal bug.

**Error**:
```
java.lang.NullPointerException: Cannot invoke 
"org.apache.spark.storage.BlockManagerId.executorId()" 
because "idWithoutTopologyInfo" is null
```

**Location**: `BlockManagerMasterEndpoint.scala` - Spark's internal block manager

**Analysis**:
- This is a Spark 4.x bug on Windows
- Related to heartbeat mechanism between workers and master
- NOT a configuration issue - internal Spark code bug
- Not fixable without patching Spark source code

**Lesson**: Bleeding-edge versions (Spark 4.x) often have platform-specific bugs. Stick with LTS versions for production.

---

#### **Attempt 6: Downgrade to PySpark 3.5.3** ❌
**Goal**: Use Spark 3.5 LTS (stable version)

**Issue**: No binary wheels available, only source tarball

**Problem**:
```bash
pip install pyspark==3.5.3
# Started building from source... 
# Estimated time: 30+ minutes
# User canceled
```

**Lesson**: Not all PySpark versions have pre-built wheels. Always check PyPI before committing to a version.

---

#### **Attempt 7: Multiple Configuration Workarounds** ❌
Tried over **60+ different approaches**:
- ✗ Custom Hadoop XML configs
- ✗ Environment variable overrides
- ✗ Post-session Spark config updates
- ✗ Clearing `SPARK_HOME` to prevent interference
- ✗ Different Java versions (17, 21, 25)
- ✗ Different PySpark versions (4.0, 3.5.3)
- ✗ Different Hadoop versions (3.2.0, 3.3.1, 3.3.4, 3.3.5)

**Result**: All failed due to fundamental Windows + Spark incompatibilities.

**Total Time Spent**: ~3-4 hours of troubleshooting

**Lesson**: When you hit multiple fundamental compatibility issues, it's time to change the approach entirely rather than continuing to fight the platform.

---

## Why Docker? The Critical Decision

### The Problem Summary

After 60+ failed attempts, we identified **three fundamental blockers**:

1. **Java/Hadoop Version Matrix Hell**
   - Java 25 incompatible with Hadoop
   - Java 17 works but triggers other bugs
   - Spark 4.x requires Java 17+ but has Windows bugs
   - Spark 3.5 stable with Java 17 but missing wheels

2. **Windows Platform Issues**
   - Hadoop designed for UNIX/Linux
   - `winutils.exe` fragility
   - Path separators (`\` vs `/`)
   - Native library incompatibilities
   - File system case sensitivity differences

3. **Spark 4.x Windows Bug** (Critical)
   - `BlockManagerMasterEndpoint` NullPointerException
   - Not fixable via configuration
   - Requires Spark source code patch
   - Blocks all Spark operations

### Why Docker Solves Everything

#### ✅ **1. Eliminates Platform Issues**
- Linux containers provide native Spark/Hadoop environment
- No `winutils.exe` nonsense
- Proper UNIX file permissions
- Native Hadoop libraries included

#### ✅ **2. Version Control**
- Official Apache Spark Docker images (`apache/spark:3.5.1`)
- Pre-configured with compatible Java version
- Bundled Hadoop libraries (proper versions)
- Tested and validated by Apache community

#### ✅ **3. Reproducible Environment**
- Same container works on Windows, Mac, Linux
- No "works on my machine" issues
- Easy to share with team
- Identical to production deployment

#### ✅ **4. Clean Architecture**
- Spark cluster in separate containers
- FastAPI in separate container
- Clear networking boundaries
- Scalable design (can add more workers)

#### ✅ **5. Simplified Development**
- Single command to start everything: `docker-compose up -d`
- No complex environment variable setup
- No Java installation required on host
- No Hadoop configuration files

#### ✅ **6. Production-Ready**
- Same setup works in production
- Easy to scale horizontally (add workers)
- Health checks built-in
- Container orchestration ready (Kubernetes)

### Performance Comparison

| Aspect | Windows Setup | Docker Setup |
|--------|--------------|--------------|
| **Setup Time** | 4+ hours (failed) | 15 minutes |
| **Success Rate** | 0% after 60+ attempts | 100% first try |
| **Startup Time** | N/A (broken) | ~10 seconds |
| **Maintenance** | Constant troubleshooting | Zero config needed |
| **Team Setup** | Hours per person | `docker-compose up` |
| **Production Parity** | Low | Identical |

---

## Docker Setup Guide

### Prerequisites

1. **Docker Desktop for Windows**
   - Download: https://www.docker.com/products/docker-desktop/
   - Install and start Docker Desktop
   - Enable WSL 2 backend (recommended)

2. **Required Files** (All included in project)
   - `Dockerfile` - FastAPI container definition
   - `docker-compose.yml` - Multi-container orchestration
   - `.dockerignore` - Files to exclude from image
   - `requirements.txt` - Python dependencies
   - `.env` - Environment variables (AWS credentials)

### File Structure

```
META/
├── Dockerfile                      # FastAPI container definition
├── docker-compose.yml              # Orchestration config
├── .dockerignore                   # Build exclusions
├── requirements.txt                # Python packages
├── .env                           # Environment variables
├── app/
│   ├── main.py                    # FastAPI application
│   ├── engines/
│   │   └── spark_metadata_engine.py
│   ├── storage/
│   │   └── snapshot_manager.py
│   └── api/
│       ├── metadata_gen.py        # Phase 6 endpoints
│       └── schemas.py             # Pydantic models
└── PHASE6_README.md               # This file
```

### Dockerfile Explanation

```dockerfile
# Base image: Python 3.12 slim (Debian-based)
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
# - curl: Health checks
# - openjdk-21-jre-headless: Java runtime for PySpark (headless = no GUI)
RUN apt-get update && apt-get install -y \
    curl \
    openjdk-21-jre-headless \
    && rm -rf /var/lib/apt/lists/*

# Set Java environment variables
ENV JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64
ENV PATH="${JAVA_HOME}/bin:${PATH}"

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY .env .env

# Expose FastAPI port
EXPOSE 8000

# Health check - ensures container is responding
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run FastAPI with uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Key Decisions**:
- **Java 21**: Debian Trixie doesn't have Java 17 package, Java 21 LTS works perfectly
- **Slim Image**: Smaller size, faster downloads (vs full Python image)
- **No Cache Pip**: Reduces image size by not storing pip cache
- **Health Check**: Docker monitors service health automatically

### docker-compose.yml Explanation

```yaml
version: '3.8'

services:
  # Spark Master Node
  spark-master:
    image: apache/spark:3.5.1
    container_name: spark-master
    hostname: spark-master
    entrypoint: ['/opt/spark/bin/spark-class', 'org.apache.spark.deploy.master.Master']
    environment:
      - SPARK_NO_DAEMONIZE=true  # Run in foreground (for Docker)
    ports:
      - "7077:7077"   # Spark cluster communication port
      - "8081:8080"   # Spark Web UI (mapped to 8081 to avoid conflicts)
    networks:
      - lakehouse-network
    volumes:
      - spark-master-data:/opt/spark/work-dir

  # Spark Worker Node
  spark-worker:
    image: apache/spark:3.5.1
    container_name: spark-worker
    hostname: spark-worker
    entrypoint: ['/opt/spark/bin/spark-class', 'org.apache.spark.deploy.worker.Worker', 'spark://spark-master:7077']
    environment:
      - SPARK_NO_DAEMONIZE=true
      - SPARK_WORKER_MEMORY=2G    # Worker memory allocation
      - SPARK_WORKER_CORES=2      # CPU cores for worker
    depends_on:
      - spark-master
    networks:
      - lakehouse-network
    volumes:
      - spark-worker-data:/opt/spark/work-dir

  # FastAPI Application
  fastapi:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: lakehouse-api
    hostname: lakehouse-api
    environment:
      # AWS Credentials (read from .env file)
      - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
      - AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
      - AWS_REGION=${AWS_REGION:-us-east-1}
      # Spark Configuration
      - SPARK_MASTER_URL=spark://spark-master:7077  # Docker network URL
    ports:
      - "8000:8000"   # FastAPI port
    depends_on:
      - spark-master
      - spark-worker
    networks:
      - lakehouse-network
    volumes:
      - ./app:/app/app:ro  # Mount code for development (read-only)
    restart: unless-stopped

networks:
  lakehouse-network:
    driver: bridge  # Docker bridge network for inter-container communication

volumes:
  spark-master-data:
  spark-worker-data:
```

**Key Decisions**:
- **Apache Spark Image**: Official image, pre-configured and tested
- **Bridge Network**: Containers can communicate via hostnames
- **Depends On**: Ensures Spark starts before FastAPI
- **Read-Only Mount**: Prevents container from modifying host code
- **Persistent Volumes**: Spark work directories survive container restarts
- **Environment Variables**: AWS creds passed from `.env` file

### Complete Setup Commands

#### 1. Initial Setup (One-Time)

```powershell
# Verify Docker is running
docker --version
# Output: Docker version 24.x.x, build...

docker-compose --version
# Output: Docker Compose version v2.x.x

# Verify .env file exists with AWS credentials
Get-Content .env
# Should show:
# AWS_ACCESS_KEY_ID=AKIA...
# AWS_SECRET_ACCESS_KEY=...
# AWS_REGION=us-east-1
```

#### 2. Build and Start All Services

```powershell
# Build images and start containers in detached mode
docker-compose up -d --build

# Expected output:
# [+] Building 180.0s (13/13) FINISHED
# [+] Running 3/3
#  ✔ Container spark-master   Started
#  ✔ Container spark-worker   Started  
#  ✔ Container lakehouse-api  Started
```

**What happens**:
1. Pulls Apache Spark image (if not cached)
2. Builds FastAPI image from Dockerfile
3. Creates network: `meta_lakehouse-network`
4. Creates volumes: `meta_spark-master-data`, `meta_spark-worker-data`
5. Starts spark-master container
6. Starts spark-worker container (connects to master)
7. Starts lakehouse-api container (connects to Spark cluster)

**Time**: ~3-5 minutes on first run, ~10 seconds on subsequent runs

#### 3. Verify Services are Running

```powershell
# Check container status
docker ps

# Expected output:
# CONTAINER ID   IMAGE                COMMAND                  CREATED          STATUS                    PORTS
# b38787245f36   meta-fastapi         "uvicorn app.main:ap…"   2 minutes ago    Up 2 minutes (healthy)    0.0.0.0:8000->8000/tcp
# 39fad7c42ebf   apache/spark:3.5.1   "/opt/spark/bin/spar…"   2 minutes ago    Up 2 minutes              
# cb733f6c04e3   apache/spark:3.5.1   "/opt/spark/bin/spar…"   2 minutes ago    Up 2 minutes              0.0.0.0:7077->7077/tcp, 0.0.0.0:8081->8080/tcp
```

**Key Indicators**:
- ✅ All 3 containers running
- ✅ `lakehouse-api` shows `(healthy)` status
- ✅ Ports mapped correctly

#### 4. Check Logs

```powershell
# FastAPI logs
docker logs lakehouse-api

# Expected output:
# INFO:     Started server process [1]
# INFO:     Waiting for application startup.
# {"timestamp": "...", "message": "Starting Lakehouse Explorer API", "version": "0.1.0"}
# INFO:     Application startup complete.
# INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)

# Spark Master logs
docker logs spark-master

# Expected output:
# INFO Master: Starting Spark master at spark://172.18.0.2:7077
# INFO Master: Running Spark version 3.5.1
# INFO Master: I have been elected leader! New state: ALIVE
# INFO Master: Registering worker 172.18.0.3:41933 with 2 cores, 2.0 GiB RAM

# Spark Worker logs
docker logs spark-worker

# Expected output:
# INFO Worker: Successfully registered with master spark://spark-master:7077
```

#### 5. Access Services

```powershell
# Test FastAPI health endpoint
Invoke-RestMethod -Uri http://localhost:8000/health

# Expected output:
# status      : healthy
# timestamp   : 2026-02-08T14:30:15.123456Z
# environment : development
# version     : 0.1.0

# Open Spark Web UI in browser
Start-Process http://localhost:8081

# Open FastAPI Swagger Docs
Start-Process http://localhost:8000/docs
```

#### 6. Stop Services

```powershell
# Stop all containers (preserves data)
docker-compose down

# Expected output:
# [+] Running 3/3
#  ✔ Container lakehouse-api  Removed
#  ✔ Container spark-worker   Removed
#  ✔ Container spark-master   Removed
#  ✔ Network meta_lakehouse-network  Removed

# Stop and remove volumes (deletes data)
docker-compose down -v
```

#### 7. Restart Individual Service

```powershell
# Restart only FastAPI (e.g., after code changes)
docker restart lakehouse-api

# Rebuild and restart FastAPI
docker-compose up -d --build fastapi

# Restart all services
docker-compose restart
```

#### 8. View Real-Time Logs

```powershell
# Follow logs for all services
docker-compose logs -f

# Follow logs for specific service
docker-compose logs -f fastapi

# Last 50 lines from all services
docker-compose logs --tail=50
```

#### 9. Execute Commands Inside Containers

```powershell
# Open bash shell in FastAPI container
docker exec -it lakehouse-api bash

# Check Python version inside container
docker exec lakehouse-api python --version

# Check Java version inside container
docker exec lakehouse-api java -version

# Run pytest inside container
docker exec lakehouse-api pytest tests/
```

#### 10. Cleanup (Complete Reset)

```powershell
# Stop and remove everything
docker-compose down -v

# Remove all images
docker rmi meta-fastapi apache/spark:3.5.1

# Clean Docker system (frees up space)
docker system prune -a

# Verify everything removed
docker ps -a
docker images
docker volume ls
```

### Troubleshooting Commands

```powershell
# Container won't start - check detailed logs
docker logs lakehouse-api --tail 100

# Check container resource usage
docker stats

# Inspect container details
docker inspect lakehouse-api

# Check network connectivity between containers
docker exec lakehouse-api ping spark-master

# Test Spark connection from FastAPI container
docker exec lakehouse-api python -c "from pyspark.sql import SparkSession; spark = SparkSession.builder.master('spark://spark-master:7077').getOrCreate(); print('Connected!'); spark.stop()"

# Check environment variables
docker exec lakehouse-api env | grep SPARK
docker exec lakehouse-api env | grep AWS

# Port conflict - find process using port 8000
netstat -ano | findstr :8000

# Kill process by PID
taskkill /PID <pid> /F
```

---

## API Endpoints

### 1. Generate Metadata Snapshot

**Endpoint**: `POST /metadata/generate`

**Description**: Extracts metadata from a lakehouse table using Spark and saves a versioned snapshot to S3.

**Request**:
```json
{
  "storage_type": "aws",
  "bucket": "metadataproject",
  "path": "test-data/sample-data/delta/sales_delta",
  "table_format": "delta"
}
```

**PowerShell**:
```powershell
$body = @{
    storage_type = "aws"
    bucket = "metadataproject"
    path = "test-data/sample-data/delta/sales_delta"
    table_format = "delta"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/metadata/generate" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body
```

**Response**:
```json
{
  "success": true,
  "snapshot_id": "snapshot_20260208_140802_d1e6bb63",
  "table_path": "s3a://metadataproject/test-data/sample-data/delta/sales_delta",
  "table_format": "delta",
  "generated_at": "2026-02-08T14:09:54.686147Z",
  "snapshot_location": "s3://metadataproject/test-data/sample-data/delta/sales_delta/.metadata-snapshots/snapshot_20260208_140802_d1e6bb63.json",
  "metadata_summary": {
    "column_count": 5,
    "file_count": 12,
    "total_size_bytes": 2458624
  },
  "error": null
}
```

**What happens internally**:
1. API validates request
2. Spark metadata engine creates SparkSession
3. Connects to Spark cluster at `spark://spark-master:7077`
4. Downloads Delta Lake JARs (first time only)
5. Reads table from S3 using Delta Lake connector
6. Extracts schema, partitions, file stats, version info
7. Generates snapshot ID with timestamp + UUID
8. Snapshot manager saves JSON to `.metadata-snapshots/` folder
9. Spark session stopped and cleaned up

**Time**: ~30-60 seconds first run (JAR downloads), ~10-15 seconds subsequent runs

---

### 2. Get Latest Snapshot

**Endpoint**: `GET /metadata/snapshots/latest`

**Description**: Retrieves the most recent metadata snapshot for a table.

**Parameters**:
- `storage_type` (query): `"aws"` or `"minio"`
- `bucket` (query): S3 bucket name
- `path` (query): Table path within bucket

**PowerShell**:
```powershell
$params = @{
    storage_type = "aws"
    bucket = "metadataproject"
    path = "test-data/sample-data/delta/sales_delta"
}

$query = ($params.GetEnumerator() | ForEach-Object { "$($_.Key)=$($_.Value)" }) -join "&"
Invoke-RestMethod -Uri "http://localhost:8000/metadata/snapshots/latest?$query"
```

**Response**:
```json
{
  "success": true,
  "snapshot_id": "snapshot_20260208_140802_d1e6bb63",
  "table_path": "s3a://metadataproject/test-data/sample-data/delta/sales_delta",
  "table_format": "delta",
  "generated_at": "2026-02-08T14:09:54.686147Z",
  "schema": {
    "type": "struct",
    "fields": [
      {
        "name": "order_id",
        "type": "string",
        "nullable": true,
        "metadata": {}
      },
      {
        "name": "customer_id",
        "type": "string",
        "nullable": true,
        "metadata": {}
      },
      {
        "name": "product_id",
        "type": "string",
        "nullable": true,
        "metadata": {}
      },
      {
        "name": "quantity",
        "type": "long",
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
  "partitions": {
    "is_partitioned": false,
    "partition_columns": [],
    "partition_count": 0
  },
  "files": {
    "file_count": 12,
    "total_size_bytes": 2458624,
    "sample_files": [
      "part-00000-abc123.snappy.parquet",
      "part-00001-def456.snappy.parquet",
      "part-00002-ghi789.snappy.parquet"
    ]
  },
  "version_info": {
    "format": "delta",
    "version": "2"
  }
}
```

---

### 3. List All Snapshots

**Endpoint**: `GET /metadata/snapshots/list`

**Description**: Lists all metadata snapshots for a table with their metadata.

**PowerShell**:
```powershell
$params = @{
    storage_type = "aws"
    bucket = "metadataproject"
    path = "test-data/sample-data/delta/sales_delta"
}

$query = ($params.GetEnumerator() | ForEach-Object { "$($_.Key)=$($_.Value)" }) -join "&"
Invoke-RestMethod -Uri "http://localhost:8000/metadata/snapshots/list?$query"
```

**Response**:
```json
{
  "success": true,
  "table_path": "s3://metadataproject/test-data/sample-data/delta/sales_delta",
  "snapshot_count": 3,
  "snapshots": [
    {
      "snapshot_id": "snapshot_20260208_140802_d1e6bb63",
      "timestamp": "2026-02-08T14:08:02Z",
      "size_bytes": 1140,
      "s3_key": "test-data/sample-data/delta/sales_delta/.metadata-snapshots/snapshot_20260208_140802_d1e6bb63.json"
    },
    {
      "snapshot_id": "snapshot_20260208_151030_a3f2c891",
      "timestamp": "2026-02-08T15:10:30Z",
      "size_bytes": 1156,
      "s3_key": "test-data/sample-data/delta/sales_delta/.metadata-snapshots/snapshot_20260208_151030_a3f2c891.json"
    },
    {
      "snapshot_id": "snapshot_20260208_162145_f7b9d234",
      "timestamp": "2026-02-08T16:21:45Z",
      "size_bytes": 1248,
      "s3_key": "test-data/sample-data/delta/sales_delta/.metadata-snapshots/snapshot_20260208_162145_f7b9d234.json"
    }
  ],
  "error": null
}
```

---

### 4. Compare Snapshots

**Endpoint**: `POST /metadata/snapshots/diff`

**Description**: Compares two metadata snapshots and identifies differences.

**Request**:
```json
{
  "storage_type": "aws",
  "bucket": "metadataproject",
  "path": "test-data/sample-data/delta/sales_delta",
  "snapshot_id_1": "snapshot_20260208_140802_d1e6bb63",
  "snapshot_id_2": "snapshot_20260208_162145_f7b9d234"
}
```

**PowerShell**:
```powershell
$body = @{
    storage_type = "aws"
    bucket = "metadataproject"
    path = "test-data/sample-data/delta/sales_delta"
    snapshot_id_1 = "snapshot_20260208_140802_d1e6bb63"
    snapshot_id_2 = "snapshot_20260208_162145_f7b9d234"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/metadata/snapshots/diff" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body
```

**Response**:
```json
{
  "success": true,
  "snapshot_1": {
    "snapshot_id": "snapshot_20260208_140802_d1e6bb63",
    "generated_at": "2026-02-08T14:09:54.686147Z"
  },
  "snapshot_2": {
    "snapshot_id": "snapshot_20260208_162145_f7b9d234",
    "generated_at": "2026-02-08T16:21:45.123456Z"
  },
  "differences": {
    "schema_changes": [
      {
        "type": "column_added",
        "column": "discount",
        "data_type": "double",
        "nullable": true
      }
    ],
    "partition_changes": [],
    "file_count_change": {
      "before": 12,
      "after": 15,
      "delta": 3
    },
    "size_change": {
      "before": 2458624,
      "after": 3145728,
      "delta": 687104,
      "delta_percentage": 27.9
    },
    "version_change": {
      "before": "2",
      "after": "3"
    }
  },
  "error": null
}
```

---

## Testing Guide

### Manual Testing Workflow

#### 1. Generate Initial Snapshot

```powershell
# Test metadata extraction
$response = Invoke-RestMethod -Uri "http://localhost:8000/metadata/generate" `
    -Method Post `
    -ContentType "application/json" `
    -Body '{"storage_type":"aws","bucket":"metadataproject","path":"test-data/sample-data/delta/sales_delta","table_format":"delta"}'

# Check response
$response | ConvertTo-Json -Depth 10

# Verify snapshot saved to S3
aws s3 ls s3://metadataproject/test-data/sample-data/delta/sales_delta/.metadata-snapshots/
```

#### 2. Retrieve Latest Snapshot

```powershell
$latest = Invoke-RestMethod -Uri "http://localhost:8000/metadata/snapshots/latest?storage_type=aws&bucket=metadataproject&path=test-data/sample-data/delta/sales_delta"

# Examine schema
$latest.schema.fields | Format-Table name, type, nullable

# Check partitions
$latest.partitions

# Check file statistics
$latest.files
```

#### 3. Generate Multiple Snapshots

```powershell
# Generate 3 snapshots with 5-second intervals
1..3 | ForEach-Object {
    Write-Host "Generating snapshot $_..."
    Invoke-RestMethod -Uri "http://localhost:8000/metadata/generate" `
        -Method Post `
        -ContentType "application/json" `
        -Body '{"storage_type":"aws","bucket":"metadataproject","path":"test-data/sample-data/delta/sales_delta","table_format":"delta"}' | Out-Null
    Start-Sleep -Seconds 5
}
```

#### 4. List All Snapshots

```powershell
$list = Invoke-RestMethod -Uri "http://localhost:8000/metadata/snapshots/list?storage_type=aws&bucket=metadataproject&path=test-data/sample-data/delta/sales_delta"

Write-Host "Total snapshots: $($list.snapshot_count)"
$list.snapshots | Format-Table snapshot_id, timestamp, size_bytes
```

#### 5. Compare Snapshots

```powershell
# Get first and last snapshot IDs
$snapshots = $list.snapshots
$snapshot1 = $snapshots[0].snapshot_id
$snapshot2 = $snapshots[-1].snapshot_id

# Compare them
$diff = Invoke-RestMethod -Uri "http://localhost:8000/metadata/snapshots/diff" `
    -Method Post `
    -ContentType "application/json" `
    -Body (@{
        storage_type = "aws"
        bucket = "metadataproject"
        path = "test-data/sample-data/delta/sales_delta"
        snapshot_id_1 = $snapshot1
        snapshot_id_2 = $snapshot2
    } | ConvertTo-Json)

# View differences
$diff.differences | ConvertTo-Json -Depth 5
```

### Automated Testing Script

```powershell
# complete-phase6-test.ps1

Write-Host "=== Phase 6 Metadata Generation API Test Suite ===" -ForegroundColor Cyan

# Test 1: Health Check
Write-Host "`n[Test 1] Health Check" -ForegroundColor Yellow
$health = Invoke-RestMethod -Uri "http://localhost:8000/health"
if ($health.status -eq "healthy") {
    Write-Host "✓ API is healthy" -ForegroundColor Green
} else {
    Write-Host "✗ API health check failed" -ForegroundColor Red
    exit 1
}

# Test 2: Generate Metadata
Write-Host "`n[Test 2] Generate Metadata Snapshot" -ForegroundColor Yellow
$generate = Invoke-RestMethod -Uri "http://localhost:8000/metadata/generate" `
    -Method Post -ContentType "application/json" `
    -Body '{"storage_type":"aws","bucket":"metadataproject","path":"test-data/sample-data/delta/sales_delta","table_format":"delta"}'

if ($generate.success) {
    Write-Host "✓ Metadata generated successfully" -ForegroundColor Green
    Write-Host "  Snapshot ID: $($generate.snapshot_id)"
    Write-Host "  Columns: $($generate.metadata_summary.column_count)"
    Write-Host "  Files: $($generate.metadata_summary.file_count)"
} else {
    Write-Host "✗ Metadata generation failed: $($generate.error)" -ForegroundColor Red
    exit 1
}

# Test 3: Get Latest Snapshot
Write-Host "`n[Test 3] Get Latest Snapshot" -ForegroundColor Yellow
$latest = Invoke-RestMethod -Uri "http://localhost:8000/metadata/snapshots/latest?storage_type=aws&bucket=metadataproject&path=test-data/sample-data/delta/sales_delta"

if ($latest.success) {
    Write-Host "✓ Latest snapshot retrieved" -ForegroundColor Green
    Write-Host "  Snapshot ID: $($latest.snapshot_id)"
    Write-Host "  Schema fields: $($latest.schema.fields.Count)"
} else {
    Write-Host "✗ Get latest snapshot failed: $($latest.error)" -ForegroundColor Red
    exit 1
}

# Test 4: List Snapshots
Write-Host "`n[Test 4] List All Snapshots" -ForegroundColor Yellow
$list = Invoke-RestMethod -Uri "http://localhost:8000/metadata/snapshots/list?storage_type=aws&bucket=metadataproject&path=test-data/sample-data/delta/sales_delta"

if ($list.success -and $list.snapshot_count -gt 0) {
    Write-Host "✓ Snapshots listed successfully" -ForegroundColor Green
    Write-Host "  Total snapshots: $($list.snapshot_count)"
    $list.snapshots | ForEach-Object {
        Write-Host "    - $($_.snapshot_id) ($($_.size_bytes) bytes)"
    }
} else {
    Write-Host "✗ List snapshots failed: $($list.error)" -ForegroundColor Red
    exit 1
}

# Test 5: Generate Second Snapshot
Write-Host "`n[Test 5] Generate Second Snapshot for Comparison" -ForegroundColor Yellow
Start-Sleep -Seconds 2
$generate2 = Invoke-RestMethod -Uri "http://localhost:8000/metadata/generate" `
    -Method Post -ContentType "application/json" `
    -Body '{"storage_type":"aws","bucket":"metadataproject","path":"test-data/sample-data/delta/sales_delta","table_format":"delta"}'

if ($generate2.success) {
    Write-Host "✓ Second snapshot generated" -ForegroundColor Green
    Write-Host "  Snapshot ID: $($generate2.snapshot_id)"
} else {
    Write-Host "✗ Second snapshot failed: $($generate2.error)" -ForegroundColor Red
    exit 1
}

# Test 6: Compare Snapshots
Write-Host "`n[Test 6] Compare Two Snapshots" -ForegroundColor Yellow
$diff = Invoke-RestMethod -Uri "http://localhost:8000/metadata/snapshots/diff" `
    -Method Post -ContentType "application/json" `
    -Body (@{
        storage_type = "aws"
        bucket = "metadataproject"
        path = "test-data/sample-data/delta/sales_delta"
        snapshot_id_1 = $generate.snapshot_id
        snapshot_id_2 = $generate2.snapshot_id
    } | ConvertTo-Json)

if ($diff.success) {
    Write-Host "✓ Snapshots compared successfully" -ForegroundColor Green
    Write-Host "  Schema changes: $($diff.differences.schema_changes.Count)"
    Write-Host "  File count change: $($diff.differences.file_count_change.delta)"
} else {
    Write-Host "✗ Snapshot comparison failed: $($diff.error)" -ForegroundColor Red
    exit 1
}

Write-Host "`n=== All Tests Passed ✓ ===" -ForegroundColor Green
```

**Run**:
```powershell
.\complete-phase6-test.ps1
```

---

## Troubleshooting

### Issue 1: Container Fails to Start

**Symptoms**:
- `docker ps` doesn't show `lakehouse-api`
- Container status shows "Exited (1)"

**Diagnosis**:
```powershell
docker logs lakehouse-api
```

**Common Causes**:
1. **Missing .env file**
   ```
   Error: AWS_ACCESS_KEY_ID environment variable not set
   ```
   **Fix**: Create `.env` file with AWS credentials

2. **Port conflict**
   ```
   Error: bind: Only one usage of each socket address is normally permitted
   ```
   **Fix**: Stop process using port 8000 or change port in docker-compose.yml

3. **Import error**
   ```
   ModuleNotFoundError: No module named 'pyspark'
   ```
   **Fix**: Rebuild image: `docker-compose up -d --build`

### Issue 2: Spark Connection Timeout

**Symptoms**:
```
Failed to generate metadata: Spark master not available
```

**Diagnosis**:
```powershell
# Check Spark master is running
docker logs spark-master

# Check worker connected
docker logs spark-worker | Select-String "Successfully registered"

# Test connectivity from FastAPI container
docker exec lakehouse-api ping spark-master
```

**Fix**:
```powershell
# Restart Spark cluster
docker restart spark-master spark-worker

# Wait 10 seconds for worker to reconnect
Start-Sleep -Seconds 10

# Retry API request
```

### Issue 3: S3 Access Denied

**Symptoms**:
```json
{
  "detail": "Failed to generate metadata: Access Denied (Service: Amazon S3)"
}
```

**Diagnosis**:
```powershell
# Check AWS credentials in container
docker exec lakehouse-api env | Select-String "AWS"
```

**Fix**:
1. Verify `.env` file has correct AWS credentials
2. Test credentials with AWS CLI:
   ```powershell
   aws s3 ls s3://metadataproject/
   ```
3. Restart FastAPI container:
   ```powershell
   docker restart lakehouse-api
   ```

### Issue 4: Slow First Request

**Symptoms**:
- First API call takes 60+ seconds
- Subsequent calls are fast (~10 seconds)

**Explanation**: This is **normal**. First request downloads Delta Lake and Hadoop JARs from Maven Central (~150MB).

**View progress**:
```powershell
docker logs lakehouse-api -f
# Shows: [SUCCESSFUL] io.delta#delta-spark_2.12;3.2.0!delta-spark_2.12.jar (2400ms)
```

**Workaround**: Use readiness probe or warm-up request on container start.

### Issue 5: Java Version Mismatch

**Symptoms**:
```
java.lang.UnsupportedClassVersionError: Compiled by Java X
```

**Diagnosis**:
```powershell
# Check Java version in container
docker exec lakehouse-api java -version

# Check Spark Java version
docker exec spark-master java -version
```

**Fix**: Versions must match. Rebuild FastAPI image with correct Java version in Dockerfile.

### Issue 6: Snapshot Not Found

**Symptoms**:
```json
{
  "success": false,
  "error": "No snapshots found for table"
}
```

**Diagnosis**:
```powershell
# Check S3 .metadata-snapshots folder exists
aws s3 ls s3://metadataproject/test-data/sample-data/delta/sales_delta/.metadata-snapshots/
```

**Fix**:
- Ensure at least one snapshot was generated successfully
- Check S3 path is correct (no trailing slashes)
- Verify table format matches (delta/iceberg/hudi)

---

## Technical Specifications

### Component Versions

| Component | Version | Purpose |
|-----------|---------|---------|
| **Python** | 3.12 | FastAPI runtime |
| **FastAPI** | 0.109.0 | Web framework |
| **PySpark** | 3.5.1 | Spark Python API |
| **Apache Spark** | 3.5.1 | Distributed processing engine |
| **Delta Lake** | 3.2.0 | Delta table format support |
| **Java** | 21 LTS | JVM runtime for Spark |
| **Hadoop** | 3.3.4 | Bundled with Spark 3.5.1 |
| **boto3** | 1.34.20 | AWS S3 SDK |
| **Docker** | 20.10+ | Container runtime |
| **Docker Compose** | v2.x | Container orchestration |

### Version Compatibility Matrix

| Spark | PySpark | Delta Lake | Scala | Java | Hadoop |
|-------|---------|------------|-------|------|--------|
| 3.5.1 | 3.5.1 | 3.2.0 | 2.12 | 17/21 | 3.3.4 |

**Critical**: All versions must match exactly to avoid serialization errors.

### Resource Requirements

#### Development Environment
- **CPU**: 4 cores (2 for Spark worker, 1 for master, 1 for FastAPI)
- **RAM**: 4GB minimum
  - Spark Worker: 2GB
  - Spark Master: 512MB
  - FastAPI: 512MB
  - Docker overhead: 1GB
- **Disk**: 5GB
  - Docker images: 2GB
  - Spark work directories: 1GB
  - Maven cache (JARs): 500MB
  - Logs: 500MB

#### Production Environment
- **Spark Workers**: Scale horizontally based on workload
- **Spark Worker RAM**: 8-16GB per worker recommended
- **Spark Worker Cores**: 4-8 cores per worker
- **FastAPI Replicas**: 2-3 for high availability
- **Load Balancer**: Nginx or AWS ALB for FastAPI

### Network Architecture

```
Host Machine (Windows)
├── Port 8000 → lakehouse-api:8000 (FastAPI)
├── Port 8081 → spark-master:8080 (Spark UI)
└── Port 7077 → spark-master:7077 (Spark cluster)

Docker Network (meta_lakehouse-network)
├── spark-master (172.18.0.2)
│   - Listens on 7077 (cluster port)
│   - Listens on 8080 (Web UI)
├── spark-worker (172.18.0.3)
│   - Connects to spark://spark-master:7077
│   - Registers with master
└── lakehouse-api (172.18.0.4)
    - Connects to spark://spark-master:7077
    - Submits Spark jobs to cluster
```

### Storage Pattern

```
S3 Bucket: metadataproject
└── test-data/
    └── sample-data/
        └── delta/
            └── sales_delta/               ← Table root
                ├── _delta_log/            ← Delta transaction log
                │   ├── 00000000000000000000.json
                │   ├── 00000000000000000001.json
                │   └── 00000000000000000002.json
                ├── part-00000-*.parquet   ← Data files
                ├── part-00001-*.parquet
                └── .metadata-snapshots/   ← OUR SNAPSHOTS
                    ├── snapshot_20260208_140802_d1e6bb63.json
                    ├── snapshot_20260208_151030_a3f2c891.json
                    └── snapshot_20260208_162145_f7b9d234.json
```

**Benefits of Co-located Storage**:
- ✅ Snapshots stay with table (no orphaned metadata)
- ✅ Easy to copy/move tables (metadata moves too)
- ✅ Clear ownership (per-table snapshots)
- ✅ No central metadata database to maintain

### Snapshot Format

```json
{
  "snapshot_id": "snapshot_20260208_140802_d1e6bb63",
  "table_path": "s3a://metadataproject/test-data/sample-data/delta/sales_delta",
  "table_format": "delta",
  "generated_at": "2026-02-08T14:09:54.686147Z",
  "schema": {
    "type": "struct",
    "fields": [
      {
        "name": "order_id",
        "type": "string",
        "nullable": true,
        "metadata": {}
      }
    ]
  },
  "partitions": {
    "is_partitioned": false,
    "partition_columns": [],
    "partition_count": 0
  },
  "files": {
    "file_count": 12,
    "total_size_bytes": 2458624,
    "sample_files": ["part-00000.parquet", "part-00001.parquet"]
  },
  "version_info": {
    "format": "delta",
    "version": "2"
  }
}
```

**Snapshot ID Format**: `snapshot_YYYYMMDD_HHMMSS_<uuid8>`
- **YYYYMMDD_HHMMSS**: Sortable timestamp (lexicographic order)
- **uuid8**: First 8 characters of UUID4 (collision prevention)

---

## Summary

### What We Accomplished

✅ **Implemented** 5 core components:
1. Spark metadata engine (418 lines)
2. Snapshot storage manager (395 lines)
3. Pydantic schemas (235 lines)
4. API router with 4 endpoints (368 lines)
5. Docker deployment infrastructure

✅ **Solved** fundamental Windows + Spark incompatibility by containerizing

✅ **Achieved** production-ready deployment with:
- Zero configuration hassle
- 100% reproducible environment
- Horizontal scalability
- Production parity

### Key Takeaways

1. **Start with Docker for polyglot systems** - Don't waste time fighting platform issues
2. **LTS versions for production** - Bleeding edge (Spark 4.x) has bugs
3. **Version compatibility matters** - Spark/PySpark/Scala/Java must align perfectly
4. **Co-located metadata** - Simplifies operations and avoids orphaned data
5. **Per-request Spark sessions** - Cleaner than long-running sessions

### Next Steps (Phase 7)

Phase 7 will add **MinIO** (local S3-compatible storage) to docker-compose.yml for local development without needing AWS credentials. This enables:
- Offline development
- Faster iteration cycles
- CI/CD testing without AWS costs
- Complete local lakehouse stack

---

**Phase 6 Status**: ✅ **COMPLETE AND PRODUCTION-READY**

**Documentation Version**: 1.0  
**Last Updated**: February 8, 2026  
**Author**: Lakehouse Explorer Team
