# 🔍 Natural Language Query with Approval Workflow

## ✨ What's New

Added **two-step approval workflow** for natural language queries:

1. **Preview** - See generated SQL before execution
2. **Approve & Execute** - Run query only after confirmation

---

## 🎯 Two-Step Workflow

### **Step 1: Preview Query (Generate SQL)**

```powershell
$body = @{
    query = "Show me all customers from Mumbai"
    storage_type = "aws"
    bucket = "metadataproject"
    table_path = "test-data/customer_data/customer_data_delta"
} | ConvertTo-Json

# Get SQL without executing
$preview = Invoke-RestMethod -Uri "http://localhost:8000/query/natural/preview" `
    -Method Post -ContentType "application/json" -Body $body

# Show the generated SQL
Write-Host "Generated SQL:" -ForegroundColor Cyan
Write-Host $preview.sql -ForegroundColor Yellow
Write-Host "`nExplanation:" -ForegroundColor Cyan
Write-Host $preview.explanation -ForegroundColor Green
```

**Response:**
```json
{
  "success": true,
  "operation": "query",
  "sql": "SELECT * FROM delta.default.customer_data_delta WHERE City = 'Mumbai' LIMIT 100",
  "explanation": "Filtering customers by city Mumbai",
  "parameters": {
    "filter": "City = 'Mumbai'",
    "limit": 100
  },
  "natural_query": "Show me all customers from Mumbai",
  "ready_to_execute": true,
  "approval_required": true,
  "estimated_rows": "≤100",
  "engine": "trino",
  "execution_time_estimate": "100-500ms"
}
```

---

### **Step 2: Review & Approve**

User sees:
- ✅ **SQL:** `SELECT * FROM delta.default.customer_data_delta WHERE City = 'Mumbai' LIMIT 100`
- ✅ **Explanation:** "Filtering customers by city Mumbai"
- ✅ **Estimated rows:** ≤100
- ✅ **Execution time:** 100-500ms

User decides: **Approve** ✅ or **Reject** ❌

---

### **Step 3: Execute Approved Query**

```powershell
# If approved, execute using the preview response
$executeBody = @{
    operation = $preview.operation
    sql = $preview.sql
    storage_type = $preview.table_info.storage_type
    bucket = $preview.table_info.bucket
    table_path = $preview.table_info.table_path
    catalog = $preview.table_info.catalog
    schema_name = $preview.table_info.schema
    use_trino = $true
    parameters = $preview.parameters
} | ConvertTo-Json

# Execute the approved query
$result = Invoke-RestMethod -Uri "http://localhost:8000/query/natural/execute" `
    -Method Post -ContentType "application/json" -Body $executeBody

# Show results
Write-Host "Query executed successfully!" -ForegroundColor Green
Write-Host "Rows returned: $($result.row_count)" -ForegroundColor Cyan
$result.data | Format-Table
```

**Response:**
```json
{
  "success": true,
  "operation": "query",
  "sql": "SELECT * FROM delta.default.customer_data_delta WHERE City = 'Mumbai' LIMIT 100",
  "row_count": 2,
  "columns": ["CustomerID", "Name", "Email", "City"],
  "data": [
    {"CustomerID": "1", "Name": "Alice", "Email": "alice@email.com", "City": "Mumbai"},
    {"CustomerID": "3", "Name": "Carol", "Email": "carol@email.com", "City": "Mumbai"}
  ],
  "execution_time_ms": 156,
  "engine": "trino"
}
```

---

## 🔄 Complete Example Script

Save as `test_nl_approval.ps1`:

```powershell
# Natural Language Query with Approval Workflow

Write-Host "🔍 Step 1: Previewing Query..." -ForegroundColor Cyan

# Step 1: Preview
$previewBody = @{
    query = "Count customers by city"
    storage_type = "aws"
    bucket = "metadataproject"
    table_path = "test-data/customer_data/customer_data_delta"
} | ConvertTo-Json

$preview = Invoke-RestMethod -Uri "http://localhost:8000/query/natural/preview" `
    -Method Post -ContentType "application/json" -Body $previewBody

# Show generated SQL
Write-Host "`n📝 Generated SQL:" -ForegroundColor Yellow
Write-Host $preview.sql -ForegroundColor White

Write-Host "`n💡 Explanation:" -ForegroundColor Yellow
Write-Host $preview.explanation -ForegroundColor White

Write-Host "`n📊 Estimated rows: $($preview.estimated_rows)" -ForegroundColor Yellow
Write-Host "⚡ Execution time: $($preview.execution_time_estimate)" -ForegroundColor Yellow
Write-Host "🔧 Engine: $($preview.engine)" -ForegroundColor Yellow

# Step 2: Ask for approval
Write-Host "`n⚠️ Do you want to execute this query? (Y/N): " -ForegroundColor Cyan -NoNewline
$approval = Read-Host

if ($approval -eq 'Y' -or $approval -eq 'y') {
    Write-Host "`n✅ Query approved! Executing..." -ForegroundColor Green
    
    # Step 3: Execute
    $executeBody = @{
        operation = $preview.operation
        sql = $preview.sql
        storage_type = $preview.table_info.storage_type
        bucket = $preview.table_info.bucket
        table_path = $preview.table_info.table_path
        catalog = $preview.table_info.catalog
        schema_name = $preview.table_info.schema
        use_trino = $true
        parameters = $preview.parameters
    } | ConvertTo-Json
    
    $result = Invoke-RestMethod -Uri "http://localhost:8000/query/natural/execute" `
        -Method Post -ContentType "application/json" -Body $executeBody
    
    Write-Host "`n🎉 Query executed successfully!" -ForegroundColor Green
    Write-Host "📊 Rows returned: $($result.row_count)" -ForegroundColor Cyan
    Write-Host "⏱️ Execution time: $($result.execution_time_ms)ms" -ForegroundColor Cyan
    
    Write-Host "`n📋 Results:" -ForegroundColor Cyan
    $result.data | Format-Table -AutoSize
    
} else {
    Write-Host "`n❌ Query rejected by user." -ForegroundColor Red
}
```

**Run it:**
```powershell
.\test_nl_approval.ps1
```

---

## 📝 More Examples

### Example 1: Simple Query

```powershell
# Preview
$body = '{"query":"Show me all customers","bucket":"metadataproject","table_path":"test-data/customer_data/customer_data_delta"}' | ConvertFrom-Json | ConvertTo-Json
$preview = Invoke-RestMethod -Uri "http://localhost:8000/query/natural/preview" -Method Post -ContentType "application/json" -Body $body

# Generated SQL: SELECT * FROM delta.default.customer_data_delta LIMIT 100
```

### Example 2: Aggregation

```powershell
# Preview
$body = '{"query":"Count customers by city","bucket":"metadataproject","table_path":"test-data/customer_data/customer_data_delta"}' | ConvertFrom-Json | ConvertTo-Json
$preview = Invoke-RestMethod -Uri "http://localhost:8000/query/natural/preview" -Method Post -ContentType "application/json" -Body $body

# Generated SQL: SELECT City, COUNT(*) as count FROM delta.default.customer_data_delta GROUP BY City
```

### Example 3: Filter

```powershell
# Preview
$body = '{"query":"Find customers with gmail email","bucket":"metadataproject","table_path":"test-data/customer_data/customer_data_delta"}' | ConvertFrom-Json | ConvertTo-Json
$preview = Invoke-RestMethod -Uri "http://localhost:8000/query/natural/preview" -Method Post -ContentType "application/json" -Body $body

# Generated SQL: SELECT * FROM delta.default.customer_data_delta WHERE Email LIKE '%gmail%' LIMIT 100
```

---

## 🎯 When to Use Each Endpoint

| Endpoint | Use When |
|----------|----------|
| **POST /query/natural/preview** | Always use first to see generated SQL |
| **POST /query/natural/execute** | After reviewing and approving SQL |
| **POST /query/natural** | Automated/trusted queries (no approval) |

---

## ✅ Benefits

1. **Safety**: See SQL before execution
2. **Learning**: Understand what SQL the AI generates
3. **Control**: Approve or modify queries
4. **Transparency**: Know exactly what runs on your data
5. **Debugging**: Catch incorrect SQL before execution

---

## 🔄 Comparison: Old vs New

### **Old Way (Direct Execution):**
```powershell
# Query executes immediately
POST /query/natural
→ SQL generated
→ Query executed
→ Results returned
```
**Risk:** No chance to review SQL before execution

### **New Way (Approval Workflow):**
```powershell
# Preview first
POST /query/natural/preview
→ SQL generated
→ Show to user
→ User approves

# Then execute
POST /query/natural/execute
→ Run approved SQL
→ Results returned
```
**Safe:** User reviews SQL before execution ✅

---

## 🚀 Quick Test

```powershell
# Test preview endpoint
$body = @{
    query = "Show customers from Mumbai"
    bucket = "metadataproject"
    table_path = "test-data/customer_data/customer_data_delta"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/query/natural/preview" `
    -Method Post -ContentType "application/json" -Body $body | ConvertTo-Json -Depth 10
```

**You should see:**
- ✅ `"approval_required": true`
- ✅ `"ready_to_execute": true`
- ✅ Generated SQL
- ✅ Explanation

**No data returned** - only the query plan! 🎯

---

## 📚 API Documentation

After restarting FastAPI, view docs:
- http://localhost:8000/docs

You'll see:
1. **POST /query/natural/preview** - Preview query (new)
2. **POST /query/natural/execute** - Execute approved query (new)
3. **POST /query/natural** - Direct execution (existing, kept for compatibility)

---

## ✨ Summary

**Before:**
```
User question → Execute → Results (no confirmation)
```

**After:**
```
User question → Preview → Review SQL → Approve → Execute → Results
```

**Your data is now safer!** 🛡️
