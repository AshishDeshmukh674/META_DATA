import apiClient from './client';
import type {
  GenerateMetadataRequest,
  GenerateMetadataResponse,
  SnapshotListResponse,
  SQLQueryRequest,
  QueryExecuteResponse,
  SnapshotQueryRequest,
  SnapshotQueryResponse,
  NaturalLanguageQueryRequest,
  NaturalLanguageQueryResponse,
  SyncTableResponse,
  TableInfoResponse,
  ConnectionTestResponse,
} from '../types/api';

// Health Check
export const checkHealth = async () => {
  const response = await apiClient.get('/health');
  return response.data;
};

// Metadata Generation
export const generateMetadata = async (
  data: GenerateMetadataRequest
): Promise<GenerateMetadataResponse> => {
  const response = await apiClient.post('/metadata/generate', data);
  return response.data;
};

// Snapshot Management
export const listSnapshots = async (
  storageType: string,
  bucket: string,
  tablePath: string
): Promise<SnapshotListResponse> => {
  const response = await apiClient.get('/query/snapshots/list', {
    params: {
      storage_type: storageType,
      bucket,
      table_path: tablePath,
    },
  });
  return response.data;
};

// Query Execution
export const testConnection = async (): Promise<ConnectionTestResponse> => {
  const response = await apiClient.post('/query/test-connection', {});
  return response.data;
};

export const syncTable = async (
  storageType: string,
  bucket: string,
  tablePath: string,
  schemaName: string = 'default'
): Promise<SyncTableResponse> => {
  const response = await apiClient.post('/query/sync-table', null, {
    params: {
      storage_type: storageType,
      bucket,
      table_path: tablePath,
      schema_name: schemaName,
    },
  });
  return response.data;
};

export const executeSQL = async (
  sql: string
): Promise<QueryExecuteResponse> => {
  const response = await apiClient.post('/query/execute', { sql });
  return response.data;
};

export const executeSnapshotQuery = async (
  data: SnapshotQueryRequest
): Promise<SnapshotQueryResponse> => {
  const response = await apiClient.post('/query/execute/snapshot', data);
  return response.data;
};

export const executeNaturalLanguageQuery = async (
  data: NaturalLanguageQueryRequest
): Promise<NaturalLanguageQueryResponse> => {
  const response = await apiClient.post('/query/natural', data);
  return response.data;
};

export const getTableInfo = async (
  catalog: string,
  schema: string,
  table: string
): Promise<TableInfoResponse> => {
  const response = await apiClient.get('/query/table-info', {
    params: { catalog, schema, table },
  });
  return response.data;
};
