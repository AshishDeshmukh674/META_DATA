import { apiClient } from './client';
import type {
  HealthResponse,
  GenerateMetadataRequest,
  GenerateMetadataResponse,
  MetadataRequest,
  MetadataResponse,
  SnapshotListResponse,
  SnapshotDiffRequest,
  SnapshotDiffResponse,
  QueryRequest,
  QueryResponse,
  NLQueryRequest,
  NLQueryResponse,
  ConnectionTestResponse,
} from '@/lib/types/api';

// ============================================================================
// Health Check
// ============================================================================

export const checkHealth = async (): Promise<HealthResponse> => {
  const response = await apiClient.get('/health');
  return response.data;
};

// ============================================================================
// Metadata Generation
// ============================================================================

export const generateMetadata = async (
  data: GenerateMetadataRequest
): Promise<GenerateMetadataResponse> => {
  const response = await apiClient.post('/metadata/generate', data);
  return response.data;
};

// ============================================================================
// Metadata Operations
// ============================================================================

export const getSchema = async (
  data: MetadataRequest
): Promise<MetadataResponse> => {
  const response = await apiClient.post('/metadata/schema', data);
  return response.data;
};

export const getPartitions = async (
  data: MetadataRequest
): Promise<MetadataResponse> => {
  const response = await apiClient.post('/metadata/partitions', data);
  return response.data;
};

export const getSnapshots = async (
  data: MetadataRequest
): Promise<MetadataResponse> => {
  const response = await apiClient.post('/metadata/snapshots', data);
  return response.data;
};

export const getFiles = async (
  data: MetadataRequest
): Promise<MetadataResponse> => {
  const response = await apiClient.post('/metadata/files', data);
  return response.data;
};

// ============================================================================
// Snapshot Management
// ============================================================================

export const listSnapshots = async (
  storageType: string,
  bucket: string,
  tablePath: string
): Promise<SnapshotListResponse> => {
  const response = await apiClient.get('/metadata/snapshots/list', {
    params: {
      storage_type: storageType,
      bucket,
      path: tablePath,
    },
  });
  return response.data;
};

export const getLatestSnapshot = async (
  storageType: string,
  bucket: string,
  tablePath: string
): Promise<any> => {
  const response = await apiClient.get('/metadata/snapshots/latest', {
    params: {
      storage_type: storageType,
      bucket,
      path: tablePath,
    },
  });
  return response.data;
};

export const compareSnapshots = async (
  data: SnapshotDiffRequest
): Promise<SnapshotDiffResponse> => {
  const response = await apiClient.post('/metadata/snapshots/diff', data);
  return response.data;
};

// ============================================================================
// Query Execution
// ============================================================================

export const executeQuery = async (
  data: QueryRequest
): Promise<QueryResponse> => {
  const response = await apiClient.post('/query/execute', data);
  return response.data;
};

export const executeNLQuery = async (
  data: NLQueryRequest
): Promise<NLQueryResponse> => {
  const response = await apiClient.post('/query/natural-language', data);
  return response.data;
};

// ============================================================================
// Connection Test
// ============================================================================

export const testConnection = async (): Promise<ConnectionTestResponse> => {
  const response = await apiClient.post('/query/test-connection', {});
  return response.data;
};
