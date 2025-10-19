import { gql } from "@apollo/client";
import { useLazyQuery, useMutation, useQuery } from "@apollo/client/react";

/**
 * Types aligning with the AGI backend GraphQL schema.
 */
export type Memory = {
  id: string;
  content: string;
  metadata: Record<string, unknown> | null;
  sourceType: string;
  createdAt: string;
  similarityScore?: number | null;
};

export type SearchResult = {
  memory: Memory;
  highlights: string[];
  score: number;
};

export type SearchVariables = {
  query: string;
  topK?: number;
  searchType?: "hybrid" | "semantic" | "bm25";
  threshold?: number;
};

export type CreateMemoryInput = {
  content: string;
  metadata?: Record<string, unknown>;
  sourceType?: string;
};

export type CreateRelationInput = {
  sourceId: string;
  targetId: string;
  relationType: string;
  weight?: number;
  metadata?: Record<string, unknown>;
};

export type HealthStatus = {
  service: string;
  status: boolean;
  message?: string | null;
};

// ============================================================================
// GRAPHQL DOCUMENTS
// ============================================================================

const SEARCH_MEMORIES_QUERY = gql`
  query SearchMemories($input: SearchInput!) {
    searchMemories(search: $input) {
      memory {
        id
        content
        metadata
        sourceType
        createdAt
        similarityScore
      }
      highlights
      score
    }
  }
`;

const CREATE_MEMORY_MUTATION = gql`
  mutation CreateMemory($memory: MemoryInput!) {
    createMemory(memory: $memory) {
      id
      content
      metadata
      sourceType
      createdAt
      similarityScore
    }
  }
`;

const CREATE_RELATION_MUTATION = gql`
  mutation CreateRelation($relation: RelationInput!) {
    createRelation(relation: $relation) {
      id
      sourceId
      targetId
      relationType
      weight
      metadata
    }
  }
`;

const HEALTH_CHECK_QUERY = gql`
  query HealthStatuses {
    healthCheck {
      service
      status
      message
    }
  }
`;

const SEND_MESSAGE_MUTATION = gql`
  mutation SendMessage($threadId: String!, $message: String!) {
    sendMessage(threadId: $threadId, message: $message) {
      role
      content
      timestamp
      metadata
    }
  }
`;

// ============================================================================
// HOOKS
// ============================================================================

export const useSearchMemories = (
  variables: SearchVariables,
  options?: { skip?: boolean }
) => {
  const { query, topK, searchType, threshold } = variables;

  const {
    data,
    loading,
    error,
    refetch,
  } = useQuery(SEARCH_MEMORIES_QUERY, {
    skip: options?.skip || !query?.trim(),
    variables: {
      input: {
        query,
        topK: topK ?? 10,
        searchType: searchType ?? "hybrid",
        threshold: threshold ?? 0.7,
      },
    },
    fetchPolicy: "cache-and-network",
    errorPolicy: "all",
  });

  const results: SearchResult[] = data?.searchMemories?.map(
    (entry: SearchResult) => ({
      memory: {
        ...entry.memory,
        metadata: entry.memory.metadata ?? {},
      },
      highlights: entry.highlights ?? [],
      score: entry.score ?? 0,
    })
  ) ?? [];

  return {
    data: results,
    loading,
    error,
    refetch,
  };
};

export const useLazySearchMemories = () => {
  const [execute, state] = useLazyQuery(SEARCH_MEMORIES_QUERY, {
    fetchPolicy: "network-only",
    errorPolicy: "all",
  });

  const trigger = async (variables: SearchVariables) => {
    const response = await execute({
      variables: {
        input: {
          query: variables.query,
          topK: variables.topK ?? 10,
          searchType: variables.searchType ?? "hybrid",
          threshold: variables.threshold ?? 0.7,
        },
      },
    });

    const results: SearchResult[] =
      response.data?.searchMemories?.map((entry: SearchResult) => ({
        memory: {
          ...entry.memory,
          metadata: entry.memory.metadata ?? {},
        },
        highlights: entry.highlights ?? [],
        score: entry.score ?? 0,
      })) ?? [];

    return results;
  };

  return [trigger, state] as const;
};

export const useCreateMemory = (options?: {
  onCompleted?: (memory: Memory) => void;
  onError?: (error: Error) => void;
}) => {
  const [mutate, result] = useMutation(CREATE_MEMORY_MUTATION, {
    errorPolicy: "all",
    onCompleted: (response) => {
      const memory: Memory | undefined = response?.createMemory;
      if (memory && options?.onCompleted) {
        options.onCompleted(memory);
      }
    },
    onError: options?.onError,
  });

  const createMemory = (input: CreateMemoryInput) =>
    mutate({
      variables: {
        memory: {
          content: input.content,
          metadata: input.metadata ?? {},
          sourceType: input.sourceType ?? "user",
        },
      },
    });

  return [createMemory, result] as const;
};

export const useCreateRelation = () =>
  useMutation(CREATE_RELATION_MUTATION, {
    errorPolicy: "all",
  });

export const useHealthStatuses = (options?: { pollIntervalMs?: number }) => {
  const interval = options?.pollIntervalMs ?? 30_000;

  const { data, loading, error, refetch } = useQuery(HEALTH_CHECK_QUERY, {
    fetchPolicy: "cache-and-network",
    errorPolicy: "all",
    pollInterval: interval,
  });

  const statuses: HealthStatus[] = data?.healthCheck ?? [];

  return { data: statuses, loading, error, refetch };
};

export const useSendMessage = () =>
  useMutation(SEND_MESSAGE_MUTATION, {
    errorPolicy: "all",
  });

// ============================================================================
// AGI TABLE TYPES
// ============================================================================

export type KnowledgeEntry = {
  id: string;
  section: string;
  content: string;
  tags: string[];
  priority: number;
  created_at: string;
  updated_at: string;
};

export type RoadmapItem = {
  id: string;
  phase: string;
  status: string;
  next_actions: string[];
  priority: number;
  created_at: string;
  updated_at: string;
};

export type WorkerTask = {
  id: string;
  task_type: string;
  status: string;
  result: string | null;
  created_at: string;
  updated_at: string;
  error_message: string | null;
};

export type KnownMCP = {
  id: string;
  mcp_id: string;
  display_name: string;
  capabilities: string[];
  description: string | null;
  usage_count: number;
  last_used_at: string | null;
};

// ============================================================================
// AGI GRAPHQL DOCUMENTS
// ============================================================================

const GET_ALL_KNOWLEDGE_QUERY = gql`
  query GetAllKnowledge($section: String, $priorityMin: Int) {
    getAllKnowledge(section: $section, priorityMin: $priorityMin) {
      id
      section
      content
      tags
      priority
      createdAt
      updatedAt
    }
  }
`;

const GET_ALL_ROADMAP_QUERY = gql`
  query GetAllRoadmap($status: String, $priorityMin: Int) {
    getAllRoadmap(status: $status, priorityMin: $priorityMin) {
      id
      phase
      status
      nextActions
      priority
      createdAt
      updatedAt
    }
  }
`;

const GET_ALL_TASKS_QUERY = gql`
  query GetAllTasks($status: String, $taskType: String) {
    getAllTasks(status: $status, taskType: $taskType) {
      id
      taskType
      status
      result
      createdAt
      updatedAt
      errorMessage
    }
  }
`;

const GET_ALL_MCPS_QUERY = gql`
  query GetAllMCPs($capability: String) {
    getAllMcps(capability: $capability) {
      id
      mcpId
      displayName
      capabilities
      description
      usageCount
      lastUsedAt
    }
  }
`;

const CREATE_KNOWLEDGE_MUTATION = gql`
  mutation CreateKnowledge($knowledge: KnowledgeInput!) {
    createKnowledge(knowledge: $knowledge) {
      id
      section
      content
      tags
      priority
      createdAt
      updatedAt
    }
  }
`;

const CREATE_ROADMAP_MUTATION = gql`
  mutation CreateRoadmap($roadmap: RoadmapInput!) {
    createRoadmap(roadmap: $roadmap) {
      id
      phase
      status
      nextActions
      priority
      createdAt
      updatedAt
    }
  }
`;

// ============================================================================
// AGI HOOKS
// ============================================================================

export const useAllKnowledge = (options?: {
  section?: string;
  priorityMin?: number;
  skip?: boolean;
}) => {
  const { data, loading, error, refetch } = useQuery(GET_ALL_KNOWLEDGE_QUERY, {
    variables: {
      section: options?.section,
      priorityMin: options?.priorityMin,
    },
    skip: options?.skip,
    fetchPolicy: "cache-and-network",
    errorPolicy: "all",
    pollInterval: 10000, // Poll every 10 seconds
  });

  const knowledge: KnowledgeEntry[] = data?.getAllKnowledge ?? [];

  return { data: knowledge, loading, error, refetch };
};

export const useAllRoadmap = (options?: {
  status?: string;
  priorityMin?: number;
  skip?: boolean;
}) => {
  const { data, loading, error, refetch } = useQuery(GET_ALL_ROADMAP_QUERY, {
    variables: {
      status: options?.status,
      priorityMin: options?.priorityMin,
    },
    skip: options?.skip,
    fetchPolicy: "cache-and-network",
    errorPolicy: "all",
    pollInterval: 10000,
  });

  const roadmap: RoadmapItem[] = data?.getAllRoadmap ?? [];

  return { data: roadmap, loading, error, refetch };
};

export const useAllTasks = (options?: {
  status?: string;
  taskType?: string;
  skip?: boolean;
}) => {
  const { data, loading, error, refetch } = useQuery(GET_ALL_TASKS_QUERY, {
    variables: {
      status: options?.status,
      taskType: options?.taskType,
    },
    skip: options?.skip,
    fetchPolicy: "cache-and-network",
    errorPolicy: "all",
    pollInterval: 10000,
  });

  const tasks: WorkerTask[] = data?.getAllTasks ?? [];

  return { data: tasks, loading, error, refetch };
};

export const useAllMCPs = (options?: {
  capability?: string;
  skip?: boolean;
}) => {
  const { data, loading, error, refetch } = useQuery(GET_ALL_MCPS_QUERY, {
    variables: {
      capability: options?.capability,
    },
    skip: options?.skip,
    fetchPolicy: "cache-and-network",
    errorPolicy: "all",
  });

  const mcps: KnownMCP[] = data?.getAllMcps ?? [];

  return { data: mcps, loading, error, refetch };
};

export const useCreateKnowledge = (options?: {
  onCompleted?: (knowledge: KnowledgeEntry) => void;
  onError?: (error: Error) => void;
}) => {
  const [mutate, result] = useMutation(CREATE_KNOWLEDGE_MUTATION, {
    errorPolicy: "all",
    onCompleted: (response) => {
      if (response?.createKnowledge && options?.onCompleted) {
        options.onCompleted(response.createKnowledge);
      }
    },
    onError: options?.onError,
    refetchQueries: [{ query: GET_ALL_KNOWLEDGE_QUERY }],
  });

  const createKnowledge = (input: {
    section: string;
    content: string;
    tags: string[];
    priority: number;
  }) =>
    mutate({
      variables: {
        knowledge: input,
      },
    });

  return [createKnowledge, result] as const;
};

export const useCreateRoadmap = (options?: {
  onCompleted?: (roadmap: RoadmapItem) => void;
  onError?: (error: Error) => void;
}) => {
  const [mutate, result] = useMutation(CREATE_ROADMAP_MUTATION, {
    errorPolicy: "all",
    onCompleted: (response) => {
      if (response?.createRoadmap && options?.onCompleted) {
        options.onCompleted(response.createRoadmap);
      }
    },
    onError: options?.onError,
    refetchQueries: [{ query: GET_ALL_ROADMAP_QUERY }],
  });

  const createRoadmap = (input: {
    phase: string;
    status: string;
    nextActions: string[];
    priority: number;
  }) =>
    mutate({
      variables: {
        roadmap: input,
      },
    });

  return [createRoadmap, result] as const;
};

// ============================================================================
// DATABASE TABLE TYPES
// ============================================================================

export type DatabaseTable = {
  table_name: string;
  row_count: number;
  column_count: number;
  table_size: string | null;
};

export type TableColumn = {
  column_name: string;
  data_type: string;
  is_nullable: boolean;
  column_default: string | null;
};

export type TableRow = {
  data: Record<string, unknown>;
};

// ============================================================================
// DATABASE GRAPHQL DOCUMENTS
// ============================================================================

const GET_DATABASE_TABLES_QUERY = gql`
  query GetDatabaseTables {
    getDatabaseTables {
      tableName
      rowCount
      columnCount
      tableSize
    }
  }
`;

const GET_TABLE_SCHEMA_QUERY = gql`
  query GetTableSchema($tableName: String!) {
    getTableSchema(tableName: $tableName) {
      columnName
      dataType
      isNullable
      columnDefault
    }
  }
`;

const GET_TABLE_DATA_QUERY = gql`
  query GetTableData($tableName: String!, $limit: Int, $offset: Int) {
    getTableData(tableName: $tableName, limit: $limit, offset: $offset) {
      data
    }
  }
`;

// ============================================================================
// DATABASE HOOKS
// ============================================================================

export const useDatabaseTables = () => {
  const { data, loading, error, refetch } = useQuery(GET_DATABASE_TABLES_QUERY, {
    fetchPolicy: "cache-and-network",
    errorPolicy: "all",
  });

  const tables: DatabaseTable[] = data?.getDatabaseTables?.map((t: DatabaseTable) => ({
    table_name: t.tableName,
    row_count: t.rowCount,
    column_count: t.columnCount,
    table_size: t.tableSize,
  })) ?? [];

  return { data: tables, loading, error, refetch };
};

export const useTableSchema = (tableName: string, skip: boolean = false) => {
  const { data, loading, error, refetch } = useQuery(GET_TABLE_SCHEMA_QUERY, {
    variables: { tableName },
    skip,
    fetchPolicy: "cache-and-network",
    errorPolicy: "all",
  });

  const schema: TableColumn[] = data?.getTableSchema?.map((c: TableColumn) => ({
    column_name: c.columnName,
    data_type: c.dataType,
    is_nullable: c.isNullable,
    column_default: c.columnDefault,
  })) ?? [];

  return { data: schema, loading, error, refetch };
};

export const useTableData = (
  tableName: string,
  options?: { limit?: number; offset?: number; skip?: boolean }
) => {
  const { data, loading, error, refetch } = useQuery(GET_TABLE_DATA_QUERY, {
    variables: {
      tableName,
      limit: options?.limit ?? 100,
      offset: options?.offset ?? 0,
    },
    skip: options?.skip,
    fetchPolicy: "cache-and-network",
    errorPolicy: "all",
  });

  const rows: TableRow[] = data?.getTableData ?? [];

  return { data: rows, loading, error, refetch };
};

// ============================================================================
// GRAPH DATA (Neo4j integration)
// ============================================================================

export interface GraphNode {
  id: string;
  label: string;
  type: string; // Memory, Knowledge, Task
  properties: Record<string, any>;
}

export interface GraphRelation {
  id: string;
  source: string;
  target: string;
  type: string;
  weight: number;
}

export interface GraphData {
  nodes: GraphNode[];
  relations: GraphRelation[];
}

const GET_GRAPH_DATA_QUERY = gql`
  query GetGraphData($nodeTypes: [String!], $limit: Int) {
    getGraphData(nodeTypes: $nodeTypes, limit: $limit) {
      nodes {
        id
        label
        type
        properties
      }
      relations {
        id
        source
        target
        type
        weight
      }
    }
  }
`;

const SEARCH_GRAPH_NODES_QUERY = gql`
  query SearchGraphNodes($query: String!, $limit: Int) {
    searchGraphNodes(query: $query, limit: $limit) {
      id
      label
      type
      properties
    }
  }
`;

const GET_NODE_NEIGHBORS_QUERY = gql`
  query GetNodeNeighbors($nodeId: String!, $depth: Int) {
    getNodeNeighbors(nodeId: $nodeId, depth: $depth) {
      nodes {
        id
        label
        type
        properties
      }
      relations {
        id
        source
        target
        type
        weight
      }
    }
  }
`;

export const useGraphData = (
  options?: { nodeTypes?: string[]; limit?: number; skip?: boolean }
) => {
  const { data, loading, error, refetch } = useQuery(GET_GRAPH_DATA_QUERY, {
    variables: {
      nodeTypes: options?.nodeTypes,
      limit: options?.limit || 100,
    },
    skip: options?.skip,
    fetchPolicy: "cache-and-network",
    errorPolicy: "all",
  });

  return {
    data: data?.getGraphData as GraphData | undefined,
    loading,
    error,
    refetch,
  };
};

export const useSearchGraphNodes = (query: string, limit: number = 10) => {
  const { data, loading, error } = useQuery(SEARCH_GRAPH_NODES_QUERY, {
    variables: { query, limit },
    skip: !query,
    fetchPolicy: "cache-and-network",
  });

  return {
    data: (data?.searchGraphNodes as GraphNode[]) || [],
    loading,
    error,
  };
};

export const useNodeNeighbors = (nodeId: string, depth: number = 1) => {
  const { data, loading, error } = useQuery(GET_NODE_NEIGHBORS_QUERY, {
    variables: { nodeId, depth },
    skip: !nodeId,
    fetchPolicy: "cache-and-network",
  });

  return {
    data: data?.getNodeNeighbors as GraphData | undefined,
    loading,
    error,
  };
};

// ============================================================================
// AGI MEMORY SYSTEM (L1/L2/L3)
// ============================================================================

export type ThinkResult = {
  event_id: string;
  thought: string;
  classified_as: string;
  importance: number;
  storage_layer: string;
  stored_ids: {
    redis_key?: string;
    postgres_id?: string;
    neo4j_node_id?: string;
  };
  related_memories: RelatedMemory[];
  processing_time_ms: number;
  enriched: boolean;
  session_id: string;
};

export type RelatedMemory = {
  content: string;
  metadata: Record<string, any>;
  similarity: number;
  source: string;
};

export type MemoryStats = {
  total_memories: number;
  by_source_type: Record<string, number>;
  recent_24h: number;
  quality_distribution: Record<string, number>;
  l1_redis_count?: number;
  l2_postgres_count?: number;
  l3_neo4j_count?: number;
  database_status: string;
  redis_status: string;
};

export type PerformanceMetrics = {
  latency_stats: {
    avg_ms: number;
    p50_ms: number;
    p95_ms: number;
    p99_ms: number;
    min_ms: number;
    max_ms: number;
  };
  token_stats: {
    total_tokens_in: number;
    total_tokens_out: number;
    total_tokens: number;
    avg_tokens_in: number;
    avg_tokens_out: number;
  };
  error_rate: {
    error_rate: number;
    success_count: number;
    error_count: number;
    total_count: number;
  };
  by_layer?: Record<string, any>;
};

export type L1Event = {
  event_id: string;
  event_type: string;
  session_id: string;
  content: string;
  classified_type?: string;
  importance?: number;
  storage_layer?: string;
  created_at: string;
};

// ============================================================================
// AGI MEMORY QUERIES
// ============================================================================

const THINK_MUTATION = gql`
  mutation Think($query: String!, $sessionId: String, $autoEnrich: Boolean, $topRelated: Int) {
    think(query: $query, sessionId: $sessionId, autoEnrich: $autoEnrich, topRelated: $topRelated) {
      eventId
      thought
      classifiedAs
      importance
      storageLayer
      storedIds
      relatedMemories {
        content
        metadata
        similarity
        source
      }
      processingTimeMs
      enriched
      sessionId
    }
  }
`;

const MEMORY_STATS_QUERY = gql`
  query MemoryStats {
    memoryStats {
      totalMemories
      bySourceType
      recent24h
      qualityDistribution
      l1RedisCount
      l2PostgresCount
      l3Neo4jCount
      databaseStatus
      redisStatus
    }
  }
`;

const PERFORMANCE_METRICS_QUERY = gql`
  query PerformanceMetrics($operation: String, $layer: String, $startDate: String, $endDate: String) {
    performanceMetrics(operation: $operation, layer: $layer, startDate: $startDate, endDate: $endDate) {
      latencyStats {
        avgMs
        p50Ms
        p95Ms
        p99Ms
        minMs
        maxMs
      }
      tokenStats {
        totalTokensIn
        totalTokensOut
        totalTokens
        avgTokensIn
        avgTokensOut
      }
      errorRate {
        errorRate
        successCount
        errorCount
        totalCount
      }
      byLayer
    }
  }
`;

const RECENT_L1_EVENTS_QUERY = gql`
  query RecentL1Events($limit: Int, $sessionId: String) {
    recentL1Events(limit: $limit, sessionId: $sessionId) {
      eventId
      eventType
      sessionId
      content
      classifiedType
      importance
      storageLayer
      createdAt
    }
  }
`;

const MEMORY_SEARCH_QUERY = gql`
  query MemorySearch($query: String!, $topK: Int, $expandGraph: Boolean) {
    memorySearch(query: $query, topK: $topK, expandGraph: $expandGraph) {
      content
      metadata
      id
      source
      score
      quality
    }
  }
`;

// ============================================================================
// AGI MEMORY HOOKS
// ============================================================================

export const useThink = (options?: {
  onCompleted?: (result: ThinkResult) => void;
  onError?: (error: Error) => void;
}) => {
  const [mutate, result] = useMutation(THINK_MUTATION, {
    errorPolicy: "all",
    onCompleted: (response) => {
      if (response?.think && options?.onCompleted) {
        const data = response.think;
        const thinkResult: ThinkResult = {
          event_id: data.eventId,
          thought: data.thought,
          classified_as: data.classifiedAs,
          importance: data.importance,
          storage_layer: data.storageLayer,
          stored_ids: data.storedIds || {},
          related_memories: data.relatedMemories || [],
          processing_time_ms: data.processingTimeMs,
          enriched: data.enriched,
          session_id: data.sessionId,
        };
        options.onCompleted(thinkResult);
      }
    },
    onError: options?.onError,
  });

  const think = (
    query: string,
    sessionId?: string,
    autoEnrich: boolean = true,
    topRelated: number = 5
  ) =>
    mutate({
      variables: {
        query,
        sessionId: sessionId || "default",
        autoEnrich,
        topRelated,
      },
    });

  return [think, result] as const;
};

export const useMemoryStats = (options?: { pollIntervalMs?: number }) => {
  const interval = options?.pollIntervalMs ?? 30_000;

  const { data, loading, error, refetch } = useQuery(MEMORY_STATS_QUERY, {
    fetchPolicy: "cache-and-network",
    errorPolicy: "all",
    pollInterval: interval,
  });

  const stats: MemoryStats | undefined = data?.memoryStats
    ? {
        total_memories: data.memoryStats.totalMemories,
        by_source_type: data.memoryStats.bySourceType || {},
        recent_24h: data.memoryStats.recent24h,
        quality_distribution: data.memoryStats.qualityDistribution || {},
        l1_redis_count: data.memoryStats.l1RedisCount,
        l2_postgres_count: data.memoryStats.l2PostgresCount,
        l3_neo4j_count: data.memoryStats.l3Neo4jCount,
        database_status: data.memoryStats.databaseStatus || "unknown",
        redis_status: data.memoryStats.redisStatus || "unknown",
      }
    : undefined;

  return { data: stats, loading, error, refetch };
};

export const usePerformanceMetrics = (options?: {
  operation?: string;
  layer?: string;
  startDate?: string;
  endDate?: string;
  pollIntervalMs?: number;
}) => {
  const interval = options?.pollIntervalMs ?? 60_000;

  const { data, loading, error, refetch } = useQuery(
    PERFORMANCE_METRICS_QUERY,
    {
      variables: {
        operation: options?.operation,
        layer: options?.layer,
        startDate: options?.startDate,
        endDate: options?.endDate,
      },
      fetchPolicy: "cache-and-network",
      errorPolicy: "all",
      pollInterval: interval,
    }
  );

  const metrics: PerformanceMetrics | undefined = data?.performanceMetrics
    ? {
        latency_stats: {
          avg_ms: data.performanceMetrics.latencyStats.avgMs,
          p50_ms: data.performanceMetrics.latencyStats.p50Ms,
          p95_ms: data.performanceMetrics.latencyStats.p95Ms,
          p99_ms: data.performanceMetrics.latencyStats.p99Ms,
          min_ms: data.performanceMetrics.latencyStats.minMs,
          max_ms: data.performanceMetrics.latencyStats.maxMs,
        },
        token_stats: {
          total_tokens_in: data.performanceMetrics.tokenStats.totalTokensIn,
          total_tokens_out: data.performanceMetrics.tokenStats.totalTokensOut,
          total_tokens: data.performanceMetrics.tokenStats.totalTokens,
          avg_tokens_in: data.performanceMetrics.tokenStats.avgTokensIn,
          avg_tokens_out: data.performanceMetrics.tokenStats.avgTokensOut,
        },
        error_rate: {
          error_rate: data.performanceMetrics.errorRate.errorRate,
          success_count: data.performanceMetrics.errorRate.successCount,
          error_count: data.performanceMetrics.errorRate.errorCount,
          total_count: data.performanceMetrics.errorRate.totalCount,
        },
        by_layer: data.performanceMetrics.byLayer || {},
      }
    : undefined;

  return { data: metrics, loading, error, refetch };
};

export const useRecentL1Events = (
  limit: number = 20,
  sessionId?: string,
  options?: { pollIntervalMs?: number }
) => {
  const interval = options?.pollIntervalMs ?? 10_000;

  const { data, loading, error, refetch } = useQuery(RECENT_L1_EVENTS_QUERY, {
    variables: { limit, sessionId },
    fetchPolicy: "cache-and-network",
    errorPolicy: "all",
    pollInterval: interval,
  });

  const events: L1Event[] = data?.recentL1Events?.map((e: any) => ({
    event_id: e.eventId,
    event_type: e.eventType,
    session_id: e.sessionId,
    content: e.content,
    classified_type: e.classifiedType,
    importance: e.importance,
    storage_layer: e.storageLayer,
    created_at: e.createdAt,
  })) || [];

  return { data: events, loading, error, refetch };
};

export const useMemorySearch = () => {
  const [execute, state] = useLazyQuery(MEMORY_SEARCH_QUERY, {
    fetchPolicy: "network-only",
    errorPolicy: "all",
  });

  const search = async (
    query: string,
    topK: number = 10,
    expandGraph: boolean = false
  ) => {
    const response = await execute({
      variables: { query, topK, expandGraph },
    });

    return response.data?.memorySearch || [];
  };

  return [search, state] as const;
};
