// Common types
export interface ApiResponse<T = any> {
  success: boolean;
  message?: string;
  data?: T;
  error?: string;
}

export interface TableMetadata {
  storage_type: 'aws' | 'minio';
  bucket: string;
  table_path: string;
  schema_name?: string;
}

// Metadata Generation
export interface GenerateMetadataRequest {
  storage_type: 'aws' | 'minio';
  bucket: string;
  path: string;
  table_format: 'delta';
  force_refresh?: boolean;
}

export interface GenerateMetadataResponse {
  success: boolean;
  message: string;
  table_format: string;
  snapshot_id: string;
  s3_location: string;
  schema: {
    fields: Array<{
      name: string;
      type: string;
    }>;
  };
  row_count: number;
  file_count: number;
  execution_time_ms: number;
}

// Snapshots
export interface Snapshot {
  snapshot_id: string;
  delta_version: number;
  timestamp: string;
  schema_columns: string[];
  file_count: number;
  format: string;
}

export interface SnapshotListResponse {
  success: boolean;
  message: string;
  snapshot_count: number;
  storage_info: {
    storage_type: string;
    bucket: string;
    table_path: string;
  };
  snapshots: Snapshot[];
}

// Query Execution
export interface SQLQueryRequest {
  sql: string;
}

export interface QueryExecuteResponse {
  success: boolean;
  row_count: number;
  columns: string[];
  data: Record<string, any>[];
  execution_time_ms: number;
  query_id?: string;
  sql?: string;
}

export interface SnapshotQueryRequest {
  storage_type: 'aws' | 'minio';
  bucket: string;
  table_path: string;
  snapshot_id: string;
  sql_query?: string;
  limit?: number;
}

export interface SnapshotQueryResponse {
  success: boolean;
  snapshot_id: string;
  row_count: number;
  columns: string[];
  data: Record<string, any>[];
  execution_time_ms: number;
  delta_version: number;
}

// Natural Language Query
export interface NaturalLanguageQueryRequest {
  query: string;
  storage_type: 'aws' | 'minio';
  bucket: string;
  table_path: string;
  use_trino?: boolean;
  snapshot_id?: string;
  limit?: number;
}

export interface NaturalLanguageQueryResponse {
  success: boolean;
  sql: string;
  engine: 'trino' | 'spark';
  row_count: number;
  columns: string[];
  data: Record<string, any>[];
  execution_time_ms: number;
  llm_processing_time_ms: number;
}

// Table Sync
export interface SyncTableResponse {
  success: boolean;
  message: string;
  catalog: string;
  schema: string;
  table: string;
  location: string;
  columns: string[];
  trino_query_example: string;
}

// Table Info
export interface TableInfoResponse {
  success: boolean;
  catalog: string;
  schema: string;
  table_name: string;
  columns: Array<{
    name: string;
    type: string;
    nullable: boolean;
  }>;
}

// Connection Test
export interface ConnectionTestResponse {
  success: boolean;
  trino_version: string;
  catalogs: string[];
  message: string;
}
