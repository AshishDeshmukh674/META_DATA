"""
Configuration Management using Pydantic Settings.

This module loads environment variables from .env file and validates them.
It provides type-safe access to all application settings.

Why Pydantic Settings?
- Automatic validation (fail fast on startup if config is invalid)
- Type conversion (string "8000" becomes int 8000)
- Default values with documentation
- Environment variable prefix support
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from pathlib import Path

# Get the project root directory (2 levels up from this file)
PROJECT_ROOT = Path(__file__).parent.parent.parent
ENV_FILE = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Settings are loaded in this order (later overrides earlier):
    1. .env file
    2. Environment variables
    3. Default values defined here
    """
    
    # ===== Application Settings =====
    app_name: str = "LakehouseExplorer"
    app_version: str = "0.1.0"
    environment: str = "development"
    log_level: str = "INFO"
    
    # ===== API Server Settings =====
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = True
    allowed_origins: str = "http://localhost:3000,http://localhost:3001"
    
    # ===== AWS Credentials =====
    # These will be validated when user calls /connect/aws endpoint
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_region: str = "us-east-1"
    aws_s3_bucket: Optional[str] = None
    
    # ===== MinIO Configuration (Local S3) =====
    minio_endpoint: str = "http://localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "lakehouse"
    
    # ===== Trino Configuration =====
    trino_host: str = "localhost"
    trino_port: int = 8080
    trino_catalog: str = "iceberg"
    trino_schema: str = "default"
    trino_user: str = "admin"
    
    # ===== Spark Configuration =====
    spark_master: str = "spark://localhost:7077"
    spark_app_name: str = "LakehouseExplorer"
    spark_driver_memory: str = "2g"
    spark_executor_memory: str = "2g"
    
    # ===== LLM Configuration (Natural Language Queries) =====
    groq_api_key: Optional[str] = None
    groq_model: str = "llama-3.3-70b-versatile"  # Fast and accurate
    groq_temperature: float = 0.1  # Low temperature for consistent SQL generation
    groq_max_tokens: int = 2000
    
    # ===== Security =====
    secret_key: str = "dev-secret-key-change-in-production"
    
    # ===== Feature Flags =====
    enable_mcp: bool = True
    enable_llm: bool = False
    enable_metrics: bool = True
    
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"  # Ignore unknown env vars
    )
    
    def model_post_init(self, __context) -> None:
        """Log settings after initialization."""
        import sys
        print(f"[SETTINGS DEBUG] ENV_FILE path: {ENV_FILE}", file=sys.stderr)
        print(f"[SETTINGS DEBUG] ENV_FILE exists: {ENV_FILE.exists()}", file=sys.stderr)
        print(f"[SETTINGS DEBUG] Instance ID: {id(self)}", file=sys.stderr)
        print(f"[SETTINGS DEBUG] Groq API Key loaded: {bool(self.groq_api_key)}", file=sys.stderr)
        if self.groq_api_key:
            print(f"[SETTINGS DEBUG] Key prefix: {self.groq_api_key[:20]}...", file=sys.stderr)
            print(f"[SETTINGS DEBUG] Key length: {len(self.groq_api_key)}", file=sys.stderr)
        else:
            print(f"[SETTINGS DEBUG] API key is NONE!", file=sys.stderr)
    
    def get_allowed_origins_list(self) -> list[str]:
        """Convert comma-separated origins to list."""
        return [origin.strip() for origin in self.allowed_origins.split(",")]
    
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"
    
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() == "development"


# Singleton instance - loaded once at startup
settings = Settings()
