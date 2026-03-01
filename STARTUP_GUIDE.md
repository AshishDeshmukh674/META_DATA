# Lakehouse Explorer - Quick Start & Diagnostics

> **✅ RECOMMENDED: Use Docker** - The backend should run in Docker (port 8000) for proper Spark connectivity.  
> See [Quick Docker Start](#quick-docker-start) below.
> 
> **⚠️ Local Backend (port 8001)** - Only for development without Spark. Has Java gateway issues on Windows.

---

## 🐳 Quick Docker Start (Recommended)

### Step 1: Start All Services with Docker Compose

```powershell
cd C:\Users\ashis\Desktop\META
docker-compose up -d
```

This starts:
- **Spark Master** (port 7077, UI on 8081)
- **Spark Worker** (connects to master)
- **FastAPI Backend** (port 8000)

**Verify services are running:**
```powershell
docker ps
```

### Step 2: Start Frontend

```powershell
cd frontend
npm run dev
```

**Frontend will be at:** http://localhost:3001  
**Backend API will be at:** http://localhost:8000  
**Backend Swagger docs:** http://localhost:8000/docs

### Step 3: Test

```powershell
# Test backend health
curl http://localhost:8000/health

# Frontend should load at http://localhost:3001
# Click "Generate Metadata" to test end-to-end
```

---

## 🔧 Local Backend Start (Not Recommended)

<details>
<summary>Click to expand local backend instructions</summary>

### Step 1: Start Backend Locally

Open PowerShell in `C:\Users\ashis\Desktop\META`:

```powershell
# Method 1: Using start script (recommended)
.\start_backend.ps1

# Method 2: Manual start with environment variables
$env:JAVA_HOME = "C:\Program Files\Java\jdk-17"
$env:HADOOP_HOME = "C:\Users\ashis\Desktop\META\hadoop"
$env:SPARK_HOME = ""
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

**Wait for this message:**
```
INFO:     Uvicorn running on http://0.0.0.0:8001 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

</details>

### Step 2: Verify Backend is Running

Open **NEW** PowerShell window:

```powershell
curl http://localhost:8001/health
```

**Expected response:**
```json
{"status":"healthy","timestamp":"2026-03-01T...","service":"LakehouseExplorer","version":"0.1.0"}
```

If you get an error or empty response, backend is NOT running. See troubleshooting below.

### Step 3: Start Frontend

Open **ANOTHER NEW** PowerShell window in `C:\Users\ashis\Desktop\META\frontend`:

```powershell
npm run dev
```

**Wait for this message:**
```
- ready started server on 0.0.0.0:3001, url: http://localhost:3001
- event compiled client and server successfully
```

### Step 4: Open Browser

Navigate to: **http://localhost:3001**

You should see the Lakehouse Explorer home page with 4 feature cards.

### Step 5: Test Each Endpoint

#### Test 1: Generate Metadata

1. Click "Metadata Explorer"
2. Keep default tab "Generate Metadata"
3. Fill in:
   - Storage Type: **AWS S3**
   - Bucket Name: **metadataproject**
   - Table Format: Leave empty (auto-detect)
   - CSV File Path: **test-data/customer_data/customer_data.csv**
4. Click "Generate Metadata"
5. **Open Browser Console (F12)** to see API requests/responses

**Expected:**
- Green toast: "Metadata generated! Snapshot: snapshot_..."
- JSON result showing snapshot_id, table_path, metadata_summary

**If it fails:**
- Check console for error messages
- Look for CORS errors
- Verify backend is running on port 8001

#### Test 2: View Schema

1. Click "Schema" tab
2. Fill in:
   - Storage Type: **AWS S3**
   - Bucket Name: **metadataproject**  
   - Table Path: **test-data/customer_data/customer_data_delta**
   - Table Format: **delta** (or leave empty)
3. Click "Get Schema"

**Expected:**
- JSON showing schema.fields with columns: customer_id, name, email, city

#### Test 3: View Partitions

1. Click "Partitions" tab
2. Same values as Schema test
3. Click "Get Partitions"

**Expected:**
- JSON showing partition_columns array and is_partitioned boolean

#### Test 4: View Versions

1. Click "Versions" tab
2. Same values as Schema test
3. Click "Get Snapshots"

**Expected:**
- JSON showing version history with operations (CREATE TABLE, WRITE, etc.)

#### Test 5: View Files

1. Click "Files" tab
2. Same values as Schema test
3. Click "Get Files"

**Expected:**
- JSON showing files array with paths, sizes, modification times

#### Test 6: Compare Snapshots

1. Click "Compare Snapshots" tab
2. Fill in table path
3. Click "Load Available Snapshots"
4. Select two snapshots from dropdowns
5. Click "Compare Snapshots"

**Expected:**
- JSON showing schema_changes and file_changes

## 🔍 Troubleshooting

### Backend won't start

**Symptom:** `curl http://localhost:8001/health` returns empty or error

**Solutions:**

1. **Check if Python virtual environment is activated:**
   ```powershell
   Get-Command python
   # Should show path to .venv\Scripts\python.exe
   ```

2. **Check if port 8001 is already in use:**
   ```powershell
   netstat -ano | Select-String "8001"
   # If you see output, kill that process or use different port
   ```

3. **Try starting manually with verbose logging:**
   ```powershell
   cd C:\Users\ashis\Desktop\META\   .\.venv\Scripts\Activate.ps1
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload --log-level debug
   ```

4. **Check for import errors:**
   ```powershell
   python -c "from app.main import app; print('OK')"
   ```

### Frontend shows "Network Error" or "Failed to fetch"

**Symptom:** Browser console shows connection refused or CORS errors

**Solutions:**

1. **Verify backend is running:**
   ```powershell
   curl http://localhost:8001/health
   ```

2. **Check .env.local file has correct URL:**
   ```
   c:\Users\ashis\Desktop\META\frontend\.env.local
   ```
   Should contain:
   ```
   NEXT_PUBLIC_API_URL=http://localhost:8001
   ```

3. **Restart frontend after changing .env.local:**
   ```powershell
   # Stop frontend (Ctrl+C)
   npm run dev
   ```

4. **Clear browser cache:**
   - Press Ctrl+Shift+R (hard refresh)
   - Or clear browser cache completely

### API returns 404 Not Found

**Symptom:** API request shows 404 in browser console

**Solutions:**

1. **Check the endpoint URL in console:**
   - Should be `http://localhost:8001/metadata/...`
   - NOT `http://localhost:3001/metadata/...`

2. **Verify API routes are registered:**
   ```powershell
   curl http://localhost:8001/docs
   # Should show Swagger UI with all endpoints
   ```

### API returns 422 Validation Error

**Symptom:** API returns validation error about missing or invalid fields

**Solutions:**

1. **Check request payload in browser console**
2. **Verify field names match backend expectations:**
   - storage_type (not storageType)
   - bucket (not bucket_name)
   - path (not table_path)
3. **Check data types:**
   - storage_type must be "aws" or "minio"
   - All other fields must be strings

### CORS Error

**Symptom:** Browser console shows "CORS policy" error

**Solutions:**

1. **Backend must be running** - CORS middleware only works when backend is up
2. **Check allowed origins in backend settings** - should include http://localhost:3001
3. **Restart backend** after any settings changes

## 🧪 Manual API Testing

Test backend endpoints directly with curl:

### Test Health
```powershell
curl http://localhost:8001/health
```

### Test Generate Metadata
```powershell
$body = @{
    storage_type = "aws"
    bucket = "metadataproject"
    path = "test-data/customer_data/customer_data.csv"
    table_format = "delta"
    force_refresh = $false
} | ConvertTo-Json

Invoke-RestMethod -Uri http://localhost:8001/metadata/generate -Method Post -Body $body -ContentType "application/json"
```

### Test Get Schema
```powershell
$body = @{
    storage_type = "aws"
    bucket = "metadataproject"
    path = "test-data/customer_data/customer_data_delta"
    format = "delta"
} | ConvertTo-Json

Invoke-RestMethod -Uri http://localhost:8001/metadata/schema -Method Post -Body $body -ContentType "application/json"
```

## 📊 Browser Console Tips

**Open Console:** Press F12 or Right-click > Inspect > Console tab

**What to look for:**

1. **API Request logs:**
   ```
   API Request: POST /metadata/generate
   ```

2. **Errors:**
   - Network errors (backend not running)
   - CORS errors (backend not configured)
   - 404 errors (wrong endpoint)
   - 422 errors (validation failed)
   - 500 errors (backend crashed)

3. **Response data:**
   - Check if response status is 200
   - Verify response has expected JSON structure

## 🎯 Success Checklist

Before testing UI:
- ✅ Backend running on port 8001
- ✅ `curl http://localhost:8001/health` returns JSON
- ✅ `curl http://localhost:8001/docs` shows Swagger UI
- ✅ Frontend running on port 3001
- ✅ Browser open to http://localhost:3001
- ✅ Browser console shows no errors on page load

If all checked, UI should work! If endpoints still don't work, check browser console for specific error messages.

## 📞 Getting Help

If you're still stuck:

1. **Check browser console** - F12 > Console tab
2. **Check backend terminal** - Look for error messages
3. **Check frontend terminal** - Look for compilation errors
4. **Test backend directly** - Use curl commands above to isolate issues
5. **Share error messages** - Copy exact error from console or terminal

Happy exploring! 🚀
