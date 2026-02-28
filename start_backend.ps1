# Lakehouse Explorer Backend Startup Script
# Sets JAVA_HOME and starts the FastAPI backend with uvicorn

Write-Host "Starting Lakehouse Explorer Backend..." -ForegroundColor Cyan

# Activate virtual environment
& "$PSScriptRoot\.venv\Scripts\Activate.ps1"

# Set JAVA_HOME to Java 17 (required for Spark/Hadoop compatibility)
$env:JAVA_HOME = "C:\Program Files\Java\jdk-17"
Write-Host "JAVA_HOME=$env:JAVA_HOME" -ForegroundColor Green

# Set HADOOP_HOME for Windows Spark compatibility
$env:HADOOP_HOME = "C:\Users\ashis\Desktop\META\hadoop"
Write-Host "HADOOP_HOME=$env:HADOOP_HOME" -ForegroundColor Green

# CRITICAL: Remove SPARK_HOME to avoid conflicts with system Spark installations
# PySpark has its own bundled Spark (3.5.0) and should not use system Spark (4.1.1)
if ($env:SPARK_HOME) {
    Write-Host "Removing SPARK_HOME=$env:SPARK_HOME to avoid version conflicts" -ForegroundColor Yellow
    Remove-Item Env:\SPARK_HOME
}

# Verify SPARK_HOME is not set
if (-not $env:SPARK_HOME) {
    Write-Host "SPARK_HOME is not set (PySpark will use bundled Spark 3.5.0)" -ForegroundColor Green
}

# Verify Java 17 is accessible
$javaVersion = & "$env:JAVA_HOME\bin\java.exe" -version 2>&1 | Select-String "version"
Write-Host "Java Version: $javaVersion" -ForegroundColor Green

# Start backend with hot reload
Write-Host "Starting uvicorn on http://0.0.0.0:8001..." -ForegroundColor Yellow
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
