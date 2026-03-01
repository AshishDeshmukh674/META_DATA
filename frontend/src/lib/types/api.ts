// ============================================================================
// API Request & Response Types
// ============================================================================

// Health Check
export interface HealthResponse {
  status: string;
  timestamp: string;
  service: string;
  version: string;
}

// Metadata Generation
export interface GenerateMetadataRequest {
  storage_type: 'aws' | 'minio';
  bucket: string;
  path: string;
  table_format?: 'delta' | 'iceberg' | 'hudi' | 'parquet';
  force_refresh?: boolean;
  convert_to_lakehouse?: boolean;
  target_format?: 'delta' | 'iceberg' | 'hudi';
  source_format?: 'csv' | 'json' | 'parquet' | 'avro' | 'orc';
  partition_columns?: string[];
}

export interface GenerateMetadataResponse {
  success: boolean;
  snapshot_id: string;
  table_path: string;
  table_format: string;
  generated_at: string;
  snapshot_location: string;
  metadata_summary: {
    column_count: number;
    file_count: number;
    total_size_bytes: number;
  };
  error?: string;
}

// Metadata Operations (Schema, Partitions, Snapshots, Files)
export interface MetadataRequest {
  storage_type: 'aws' | 'minio';
  bucket: string;
  path: string;
  format?: 'delta' | 'iceberg' | 'hudi' | 'parquet';
}

export interface MetadataResponse {
  success: boolean;
  table_format: string;
  data: any;
  timestamp: string;
}

// Snapshot Management
export interface SnapshotListResponse {
  success: boolean;
  table_path: string;
  snapshot_count: number;
  snapshots: Array<{
    snapshot_id: string;
    timestamp: string;
    size_bytes: number;
    s3_key: string;
  }>;
  error?: string;
}

export interface SnapshotDiffRequest {
  storage_type: 'aws' | 'minio';
  bucket: string;
  path: string;
  snapshot_id_1: string;
  snapshot_id_2: string;
}

export interface SnapshotDiffResponse {
  success: boolean;
  snapshot1_id: string;
  snapshot2_id: string;
  schema_changes: {
    added_columns: string[];
    removed_columns: string[];
    type_changes: Array<{
      column: string;
      old_type: string;
      new_type: string;
    }>;
  };
  file_changes: {
    file_count_change: number;
    size_change_bytes: number;
  };
}

// Query Execution
export interface QueryRequest {
  storage_type: 'aws' | 'minio';
  bucket: string;
  table_path: string;
  query: string;
}

export interface QueryResponse {
  success: boolean;
  data: any[];
  columns: string[];
  row_count: number;
  execution_time_ms: number;
}

// Natural Language Query
export interface NLQueryRequest {
  storage_type: 'aws' | 'minio';
  bucket: string;
  table_path: string;
  question: string;
}

export interface NLQueryResponse {
  success: boolean;
  question: string;
  generated_sql: string;
  data: any[];
  columns: string[];
  row_count: number;
  explanation: string;
}

// Connection Test
export interface ConnectionTestResponse {
  success: boolean;
  message: string;
}
