# Lakehouse Explorer - Frontend Testing Guide

## 🎉 What Has Been Created

I've built a complete full-stack Lakehouse Explorer with all backend APIs integrated into the frontend UI.

### Backend API Endpoints Available:

1. **Metadata Generation** - POST `/metadata/generate`
   - Convert CSV files to Delta Lake format
   - Generate metadata snapshots

2. **Schema Viewer** - POST `/metadata/schema`
   - View table schema with column names and types
   - Auto-detect table format (Delta/Iceberg/Hudi/Parquet)

3. **Partition Viewer** - POST `/metadata/partitions`
   - View table partitioning information
   - Understand data organization

4. **Snapshot/Version Viewer** - POST `/metadata/snapshots`
   - View table version history
   - See evolution over time

5. **Files Viewer** - POST `/metadata/files`
   - List all data files in the table
   - View file sizes and paths

6. **Snapshot Comparison** - POST `/metadata/snapshots/diff`
   - Compare two metadata snapshots
   - Track schema changes, file count changes, size changes

7. **Snapshot Management** - GET `/metadata/snapshots/list`
   - List all available snapshots for a table
   - Load latest snapshot

## 📁 Files Created

### Frontend Structure:
```
frontend/
├── src/
│   ├── app/
│   │   ├── layout.tsx                  # App layout with toast notifications
│   │   ├── page.tsx                    # Home page with feature cards
│   │   ├── globals.css                 # Tailwind CSS styles
│   │   └── metadata/
│   │       └── page.tsx                # **Main Metadata Explorer UI** ⭐
│   │
│   ├── components/
│   │   ├── navigation.tsx              # Top navigation bar
│   │   ├── code-block.tsx              # JSON display with copy button
│   │   ├── data-table.tsx              # Table data display
│   │   └── ui/
│   │       ├── button.tsx              # Button component
│   │       ├── card.tsx                # Card component
│   │       ├── input.tsx               # Input component
│   │       ├── label.tsx               # Label component
│   │       ├── textarea.tsx            # Textarea component
│   │       ├── alert.tsx               # Alert component
│   │       └── loading.tsx             # Loading spinner
│   │
│   └── lib/
│       ├── api/
│       │   ├── client.ts               # Axios client with interceptors
│       │   └── queries.ts              # All API endpoint functions ⭐
│       ├── types/
│       │   └── api.ts                  # TypeScript interfaces ⭐
│       └── utils.ts                    # Utility functions
│
├── package.json                        # Dependencies installed ✅
├── next.config.js                      # Next.js configuration
├── tailwind.config.ts                  # Tailwind CSS configuration
├── tsconfig.json                       # TypeScript configuration
└── .env.local                          # Environment variables
```

## 🚀 How to Start and Test

### Step 1: Start Backend (if not already running)

Open PowerShell in `C:\Users\ashis\Desktop\META`:

```powershell
.\start_backend.ps1
```

Verify backend is running:
```powershell
curl http://localhost:8001/health
```

You should see: `{"status":"healthy",...}`

### Step 2: Start Frontend

Open another PowerShell terminal in `C:\Users\ashis\Desktop\META\frontend`:

```powershell
npm run dev
```

This will start the Next.js development server on **http://localhost:3001**

### Step 3: Open Browser

Navigate to: **http://localhost:3001**

You should see the home page with 4 feature cards.

## 🧪 Testing Each Feature

### Test 1: Generate Metadata (CSV to Delta)

1. Click **"Metadata Explorer"** from home page
2. In the left sidebar, **"Generate Metadata"** should be selected by default
3. Fill in the form:
   - **Storage Type**: AWS S3
   - **Bucket Name**: `metadataproject`
   - **Table Format**: Auto-detect (leave empty)
   - **CSV File Path**: `test-data/customer_data/customer_data.csv`
4. Click **"Generate Metadata"**
5. Wait for Spark to process (first run takes 1-2 minutes)
6. **Expected Results**:
   - Green success toast: "Metadata generated! Snapshot: snapshot_..."
   - JSON response showing:
     - `snapshot_id`
     - `table_path` ending with `_delta`
     - `metadata_summary` with column_count, file_count, total_size_bytes

### Test 2: View Schema

1. Click **"Schema"** tab in left sidebar
2. Fill in the form:
   - **Storage Type**: AWS S3
   - **Bucket Name**: `metadataproject`
   - **Table Path**: `test-data/customer_data/customer_data_delta`
   - **Table Format**: Delta Lake (or leave empty for auto-detect)
3. Click **"Get Schema"**
4. **Expected Results**:
   - JSON response with:
     - `success: true`
     - `table_format: "delta"`
     - `data.schema.fields` - array of columns with:
       - `name`: Column name (e.g., "customer_id", "name", "email", "city")
       - `type`: Data type (e.g., "string", "integer")
       - `nullable`: true/false

### Test 3: View Partitions

1. Click **"Partitions"** tab
2. Fill in form (same as schema test)
3. Click **"Get Partitions"**
4. **Expected Results**:
   - JSON response showing:
     - `partition_columns`: Array of partition column names
     - `is_partitioned`: true/false
     - `partition_count`: Number of partitions

### Test 4: View Versions/Snapshots

1. Click **"Versions"** tab
2. Fill in form (same as schema test)
3. Click **"Get Snapshots"**
4. **Expected Results**:
   - JSON response showing version history:
     - `version`: Version number (0, 1, 2, ...)
     - `timestamp`: When version was created
     - `operation`: Type of operation (CREATE TABLE, WRITE, etc.)
     - `operationMetrics`: Statistics about the operation

### Test 5: View Files

1. Click **"Files"** tab
2. Fill in form (same as schema test)
3. Click **"Get Files"**
4. **Expected Results**:
   - JSON response showing:
     - `files`: Array of data files with:
       - `path`: File path in S3
       - `size`: File size in bytes
       - `modificationTime`: When file was created
     - `file_count`: Total number of files
     - `total_size_bytes`: Total size of all files

### Test 6: Compare Snapshots

1. Click **"Compare Snapshots"** tab
2. Fill in:
   - **Storage Type**: AWS S3
   - **Bucket Name**: `metadataproject`
   - **Table Path**: `test-data/customer_data/customer_data_delta`
3. Click **"Load Available Snapshots"**
4. Wait for snapshots to load
5. Select:
   - **First Snapshot**: Older snapshot
   - **Second Snapshot**: Newer snapshot
6. Click **"Compare Snapshots"**
7. **Expected Results**:
   - JSON response showing:
     - `schema_changes`:
       - `added_columns`: New columns added
       - `removed_columns`: Columns removed
       - `type_changes`: Columns with changed types
     - `file_changes`:
       - `file_count_change`: +/- file count
       - `size_change_bytes`: +/- total size

## 📊 UI Features

### Visual Feedback:
- ✅ **Success Toast**: Green notification on successful operations
- ❌ **Error Toast**: Red notification on failures
- 🔄 **Loading Spinner**: Shows when API call is in progress
- 📄 **JSON Display**: Pretty-printed with syntax highlighting
- 📋 **Copy Button**: Copy JSON results to clipboard

### User Guidance:
- **Info Boxes**: Each tab has an explanation of what it does
- **Placeholder Text**: Shows example values in input fields
- **Tooltips**: Helpful text explaining each field
- **Auto-detect**: Table format can be auto-detected

## 🔍 Troubleshooting

### Frontend won't start:
```powershell
cd frontend
npm install  # Reinstall dependencies
npm run dev
```

### Backend connection error:
1. Check if backend is running: `curl http://localhost:8001/health`
2. If not running: `.\start_backend.ps1`
3. Check .env file has correct AWS credentials

### Metadata generation fails:
1. Ensure file exists in S3:
   ```powershell
   python check_s3.py
   ```
2. Check if Delta table already exists - use "Force Refresh" option
3. First Spark run takes time (downloading JARs)

### "Could not read file" error:
1. Verify S3 path is correct (no leading/trailing slashes)
2. Check bucket name is correct
3. Ensure AWS credentials are valid

## 📝 Expected Values Reference

### For Customer Data Example:

**CSV File Path**: `test-data/customer_data/customer_data.csv`  
**Delta Table Path**: `test-data/customer_data/customer_data_delta`  
**Storage Type**: AWS S3  
**Bucket Name**: `metadataproject`  
**Table Format**: delta

### Schema Should Show:
- customer_id (integer)
- name (string)
- email (string)
- city (string)

## 🎯 Success Criteria

✅ All 6 operations work from the UI  
✅ JSON responses display correctly  
✅ Toast notifications appear  
✅ Loading states show progress  
✅ Error messages are user-friendly  
✅ Navigation between tabs works smoothly  
✅ Auto-detect feature works  
✅ Snapshot comparison loads and displays diffs  

## 🚨 Known Issues

1. **First Spark run is slow** - Downloads Delta Lake JARs (~200MB), takes 1-2 minutes
2. **Subsequent runs are fast** - JARs are cached, ~10-30 seconds

## 📚 API Documentation

All API endpoints return JSON with this structure:

```typescript
{
  success: boolean;
  table_format: string;  // "delta" | "iceberg" | "hudi" | "parquet"
  data: any;             // Format-specific metadata
  timestamp: string;     // ISO 8601 timestamp
}
```

Error responses:

```typescript
{
  detail: string;        // Error message
}
```

## 🎉 What You Can Do Now

1. **Explore your lakehouse tables** - View schema, partitions, files
2. **Track changes over time** - Compare snapshots to see evolution
3. **Convert CSV to Delta** - Auto-convert raw data to lakehouse format
4. **Understand table structure** - See how data is organized
5. **Debug data issues** - List files, check sizes, verify schema

## 🔗 Next Steps

To add more features:
1. **Natural Language Queries** - Already built, needs testing
2. **SQL Query Editor** - Write custom SQL queries
3. **Visualization** - Charts and graphs for metadata
4. **Table Statistics** - Min/max values, histograms
5. **Data Preview** - Show sample rows from tables

Happy exploring! 🚀
