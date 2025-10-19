import { useState, useEffect, useCallback } from 'react';
import { graphqlFetch } from './graphql-client';

// ============= MOCK DATA =============

function getMockMemoryStats(): MemoryStats {
  return {
    success: true,
    qdrantVectors: 1247,
    neo4jNodes: 523,
    relations: 834,
    cache: {
      hits: 1245,
      misses: 89,
      size: 1334,
      hitRate: 0.933,
    },
    status: 'healthy',
  };
}

function getMockTaskStats(): TaskStats {
  return {
    success: true,
    totalTasks: 42,
    pending: 12,
    inProgress: 8,
    completed: 20,
    cancelled: 2,
    completedToday: 3,
    totalPomodoros: 156,
  };
}

function getMockTasks(): Task[] {
  return [
    {
      id: '1',
      title: 'Implémenter GraphQL API',
      description: 'Créer les endpoints GraphQL pour le backend',
      priority: 'high',
      status: 'in-progress',
      type: 'strategic',
      assignedTo: null,
      createdAt: new Date(Date.now() - 86400000).toISOString(),
      updatedAt: new Date().toISOString(),
      dueDate: new Date(Date.now() + 172800000).toISOString(),
      tags: ['backend', 'api'],
    },
    {
      id: '2',
      title: 'Optimiser le cache Neo4j',
      description: 'Améliorer les performances des requêtes',
      priority: 'medium',
      status: 'in-progress',
      type: 'strategic',
      assignedTo: null,
      createdAt: new Date(Date.now() - 172800000).toISOString(),
      updatedAt: new Date().toISOString(),
      tags: ['performance', 'database'],
    },
    {
      id: '3',
      title: 'Documentation API',
      description: 'Rédiger la documentation complète',
      priority: 'low',
      status: 'pending',
      type: 'operational',
      assignedTo: null,
      createdAt: new Date(Date.now() - 259200000).toISOString(),
      updatedAt: new Date(Date.now() - 259200000).toISOString(),
      tags: ['documentation'],
    },
  ];
}

function getMockMemories(): Memory[] {
  return [
    {
      id: '1',
      text: 'Le système BCI utilise une architecture microservices avec FastAPI',
      type: 'context',
      tags: ['architecture', 'bci'],
      timestamp: new Date(Date.now() - 3600000).toISOString(),
      status: 'active',
      score: 0.95,
      relations: [
        {
          relationType: 'RELATES_TO',
          text: 'GraphQL est utilisé pour les APIs',
          type: 'context',
        },
      ],
    },
    {
      id: '2',
      text: 'Migration vers GraphQL complétée avec succès',
      type: 'achievement',
      tags: ['graphql', 'migration'],
      timestamp: new Date(Date.now() - 7200000).toISOString(),
      status: 'active',
      score: 0.88,
      relations: [],
    },
    {
      id: '3',
      text: 'Neo4j stocke les relations entre les mémoires',
      type: 'context',
      tags: ['database', 'neo4j'],
      timestamp: new Date(Date.now() - 10800000).toISOString(),
      status: 'active',
      score: 0.92,
      relations: [],
    },
  ];
}

function getMockNeo4jSchema(): Neo4jSchema {
  return {
    success: true,
    tables: [
      { label: 'Memory', count: 523 },
      { label: 'Task', count: 42 },
      { label: 'Context', count: 156 },
      { label: 'Project', count: 8 },
    ],
    relationshipTypes: ['RELATES_TO', 'DEPENDS_ON', 'REFERENCES', 'PART_OF'],
    totalTables: 4,
  };
}

function getMockNeo4jNodes(): Neo4jNode[] {
  return [
    {
      id: 'mem_1',
      text: 'Architecture microservices du système BCI',
      type: 'Memory',
      status: 'active',
      project: 'BCI',
      timestamp: new Date(Date.now() - 86400000).toISOString(),
    },
    {
      id: 'mem_2',
      text: 'Intégration GraphQL avec FastAPI',
      type: 'Memory',
      status: 'active',
      project: 'BCI',
      timestamp: new Date(Date.now() - 172800000).toISOString(),
    },
    {
      id: 'task_1',
      text: 'Optimisation des performances',
      type: 'Task',
      status: 'in-progress',
      timestamp: new Date(Date.now() - 259200000).toISOString(),
    },
  ];
}

function getMockNeo4jRelations(): Neo4jRelation[] {
  return [
    {
      sourceId: 'mem_1',
      sourceText: 'Architecture microservices du système BCI',
      relationType: 'RELATES_TO',
      targetId: 'mem_2',
      targetText: 'Intégration GraphQL avec FastAPI',
    },
    {
      sourceId: 'task_1',
      sourceText: 'Optimisation des performances',
      relationType: 'DEPENDS_ON',
      targetId: 'mem_1',
      targetText: 'Architecture microservices du système BCI',
    },
  ];
}

function getMockDashboardData() {
  return {
    health: 'healthy',
    memoryStats: getMockMemoryStats(),
    taskStats: getMockTaskStats(),
    tasks: getMockTasks().slice(0, 2),
    memories: getMockMemories().slice(0, 2),
  };
}

// ============= TYPES =============

// Memory types
export interface Memory {
  id: string;
  text: string;
  type: string;
  tags: string[];
  project?: string;
  score?: number;
  timestamp: string;
  status: string;
  relations: Relation[];
}

export interface Relation {
  relationType: string;
  text: string;
  type: string;
}

export interface MemoryStats {
  success: boolean;
  qdrantVectors: number;
  neo4jNodes: number;
  relations: number;
  cache: CacheStats;
  status: string;
}

export interface CacheStats {
  hits: number;
  misses: number;
  size: number;
  hitRate: number;
}

export interface Neo4jNode {
  id: string;
  text: string;
  type: string;
  status?: string;
  project?: string;
  timestamp?: string;
}

export interface Neo4jRelation {
  sourceId: string;
  sourceText: string;
  relationType: string;
  targetId: string;
  targetText: string;
}

export interface Neo4jTable {
  label: string;
  count: number;
}

export interface Neo4jSchema {
  success: boolean;
  tables: Neo4jTable[];
  relationshipTypes: string[];
  totalTables: number;
}

export interface StoreMemoryResult {
  success: boolean;
  memoryId: string;
  message: string;
  relationsCreated: number;
  autoExtracted: number;
}

export interface MemoryInput {
  text: string;
  type?: string;
  status?: string;
  tags?: string[];
  project?: string;
  relations?: RelationInput[];
}

export interface RelationInput {
  targetText: string;
  relationType?: string;
}

// Task types
export interface Task {
  id: string;
  title: string;
  description?: string;
  type: string;
  priority: string;
  status: string;
  assignedTo?: string;
  createdAt: string;
  updatedAt: string;
  dueDate?: string;
  completedAt?: string;
  tags: string[];
}

export interface PomodoroSession {
  id: string;
  taskId: string;
  durationMinutes: number;
  startedAt: string;
  completedAt?: string;
  status: string;
}

export interface TaskStats {
  success: boolean;
  totalTasks: number;
  pending: number;
  inProgress: number;
  completed: number;
  cancelled: number;
  completedToday: number;
  totalPomodoros: number;
}

export interface CreateTaskResult {
  success: boolean;
  task: Task;
  message: string;
}

export interface UpdateTaskResult {
  success: boolean;
  task: Task;
  message: string;
}

export interface DeleteTaskResult {
  success: boolean;
  taskId: string;
  message: string;
}

export interface PomodoroResult {
  success: boolean;
  session: PomodoroSession;
  message: string;
}

export interface CreateTaskInput {
  title: string;
  description?: string;
  type?: string;
  priority?: string;
  status?: string;
  assignedTo?: string;
  dueDate?: string;
  tags?: string[];
}

export interface UpdateTaskInput {
  title?: string;
  description?: string;
  priority?: string;
  status?: string;
  assignedTo?: string;
  dueDate?: string;
  tags?: string[];
}

export interface StartPomodoroInput {
  taskId: string;
  durationMinutes?: number;
}

// ============= QUERY HELPERS =============

interface UseQueryOptions {
  skip?: boolean;
  pollInterval?: number;
}

interface UseQueryResult<T> {
  data: T | undefined;
  loading: boolean;
  error: Error | undefined;
  refetch: () => Promise<void>;
}

interface UseMutationOptions<TData, TVariables> {
  onCompleted?: (data: TData) => void;
  onError?: (error: Error) => void;
}

interface UseMutationResult<TData, TVariables> {
  mutate: (options: { variables: TVariables }) => Promise<void>;
  loading: boolean;
  data: TData | undefined;
  error: Error | undefined;
}

function useQuery<T>(
  query: string,
  variables?: Record<string, any>,
  options?: UseQueryOptions
): UseQueryResult<T> {
  const [data, setData] = useState<T>();
  const [loading, setLoading] = useState(!options?.skip);
  const [error, setError] = useState<Error>();

  const fetchData = useCallback(async () => {
    if (options?.skip) return;

    try {
      setLoading(true);
      setError(undefined);
      const result = await graphqlFetch<T>(query, variables);
      setData(result);
    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err));
      setError(error);
      // Don't set loading to false yet - it will be set in finally
    } finally {
      setLoading(false);
    }
  }, [query, JSON.stringify(variables), options?.skip]);

  useEffect(() => {
    fetchData();

    if (options?.pollInterval) {
      const interval = setInterval(fetchData, options.pollInterval);
      return () => clearInterval(interval);
    }
  }, [fetchData, options?.pollInterval]);

  return { data, loading, error, refetch: fetchData };
}

function useMutation<TData, TVariables>(
  mutation: string,
  options?: UseMutationOptions<TData, TVariables>
): [UseMutationResult<TData, TVariables>['mutate'], Omit<UseMutationResult<TData, TVariables>, 'mutate'>] {
  const [data, setData] = useState<TData>();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error>();

  const mutate = useCallback(
    async ({ variables }: { variables: TVariables }) => {
      try {
        setLoading(true);
        setError(undefined);
        const result = await graphqlFetch<TData>(mutation, variables);
        setData(result);
        if (options?.onCompleted) {
          options.onCompleted(result);
        }
      } catch (err) {
        const error = err instanceof Error ? err : new Error(String(err));
        setError(error);
        if (options?.onError) {
          options.onError(error);
        }
      } finally {
        setLoading(false);
      }
    },
    [mutation, options]
  );

  return [mutate, { data, loading, error }];
}

// ============= CUSTOM HOOKS =============

// Health
export const useHealth = (options?: UseQueryOptions) => {
  return useQuery<{ health: string }>(
    `query { health }`,
    undefined,
    options
  );
};

// Memory hooks with fallback
export const useSearchMemories = (
  variables: {
    query: string;
    limit?: number;
    type?: string;
    project?: string;
    includeRelations?: boolean;
  },
  options?: UseQueryOptions
) => {
  const result = useQuery<{ memories: Memory[] }>(
    `query SearchMemories($query: String!, $limit: Int, $type: String, $project: String, $includeRelations: Boolean) {
      memories(query: $query, limit: $limit, type: $type, project: $project, includeRelations: $includeRelations) {
        id
        text
        type
        tags
        project
        score
        timestamp
        status
        relations {
          relationType
          text
          type
        }
      }
    }`,
    variables,
    options
  );

  if (result.error && !result.data) {
    return {
      ...result,
      data: { memories: getMockMemories() },
      loading: false,
    };
  }

  return result;
};

export const useMemoryStats = (options?: UseQueryOptions) => {
  const result = useQuery<{ memoryStats: MemoryStats }>(
    `query {
      memoryStats {
        success
        qdrantVectors
        neo4jNodes
        relations
        cache {
          hits
          misses
          size
          hitRate
        }
        status
      }
    }`,
    undefined,
    options
  );

  if (result.error && !result.data) {
    return {
      ...result,
      data: { memoryStats: getMockMemoryStats() },
      loading: false,
    };
  }

  return result;
};

export const useNeo4jNodes = (
  variables?: { limit?: number },
  options?: UseQueryOptions
) => {
  const result = useQuery<{ neo4jNodes: Neo4jNode[] }>(
    `query Neo4jNodes($limit: Int) {
      neo4jNodes(limit: $limit) {
        id
        text
        type
        status
        project
        timestamp
      }
    }`,
    variables,
    options
  );

  if (result.error && !result.data) {
    return {
      ...result,
      data: { neo4jNodes: getMockNeo4jNodes() },
      loading: false,
    };
  }

  return result;
};

export const useNeo4jRelations = (
  variables?: { limit?: number },
  options?: UseQueryOptions
) => {
  const result = useQuery<{ neo4jRelations: Neo4jRelation[] }>(
    `query Neo4jRelations($limit: Int) {
      neo4jRelations(limit: $limit) {
        sourceId
        sourceText
        relationType
        targetId
        targetText
      }
    }`,
    variables,
    options
  );

  if (result.error && !result.data) {
    return {
      ...result,
      data: { neo4jRelations: getMockNeo4jRelations() },
      loading: false,
    };
  }

  return result;
};

export const useNeo4jSchema = (options?: UseQueryOptions) => {
  const result = useQuery<{ neo4jSchema: Neo4jSchema }>(
    `query {
      neo4jSchema {
        success
        tables {
          label
          count
          icon
        }
        relationshipTypes
        totalTables
      }
    }`,
    undefined,
    options
  );

  if (result.error && !result.data) {
    return {
      ...result,
      data: { neo4jSchema: getMockNeo4jSchema() },
      loading: false,
    };
  }

  return result;
};

export const useStoreMemory = (
  options?: UseMutationOptions<{ storeMemory: StoreMemoryResult }, { input: MemoryInput }>
) => {
  return useMutation<{ storeMemory: StoreMemoryResult }, { input: MemoryInput }>(
    `mutation StoreMemory($input: MemoryInput!) {
      storeMemory(input: $input) {
        success
        memoryId
        message
        relationsCreated
        autoExtracted
      }
    }`,
    options
  );
};

// Task hooks with fallback
export const useTasks = (
  variables?: {
    status?: string;
    priority?: string;
    assignedTo?: string;
    limit?: number;
  },
  options?: UseQueryOptions
) => {
  const result = useQuery<{ tasks: Task[] }>(
    `query GetTasks($status: String, $priority: String, $assignedTo: String, $limit: Int) {
      tasks(status: $status, priority: $priority, assignedTo: $assignedTo, limit: $limit) {
        id
        title
        description
        type
        priority
        status
        assignedTo
        createdAt
        updatedAt
        dueDate
        completedAt
        tags
      }
    }`,
    variables,
    options
  );

  if (result.error && !result.data) {
    let mockTasks = getMockTasks();
    
    // Apply filters
    if (variables?.status) {
      mockTasks = mockTasks.filter(t => t.status === variables.status);
    }
    if (variables?.priority) {
      mockTasks = mockTasks.filter(t => t.priority === variables.priority);
    }
    
    return {
      ...result,
      data: { tasks: mockTasks },
      loading: false,
    };
  }

  return result;
};

export const useTaskStats = (options?: UseQueryOptions) => {
  const result = useQuery<{ taskStats: TaskStats }>(
    `query {
      taskStats {
        success
        totalTasks
        pending
        inProgress
        completed
        cancelled
        completedToday
        totalPomodoros
      }
    }`,
    undefined,
    options
  );

  if (result.error && !result.data) {
    return {
      ...result,
      data: { taskStats: getMockTaskStats() },
      loading: false,
    };
  }

  return result;
};

export const useCreateTask = (
  options?: UseMutationOptions<{ createTask: CreateTaskResult }, { input: CreateTaskInput }>
) => {
  return useMutation<{ createTask: CreateTaskResult }, { input: CreateTaskInput }>(
    `mutation CreateTask($input: CreateTaskInput!) {
      createTask(input: $input) {
        success
        task {
          id
          title
          description
          type
          priority
          status
          assignedTo
          createdAt
          tags
        }
        message
      }
    }`,
    options
  );
};

export const useUpdateTask = (
  options?: UseMutationOptions<{ updateTask: UpdateTaskResult }, { taskId: string; input: UpdateTaskInput }>
) => {
  return useMutation<{ updateTask: UpdateTaskResult }, { taskId: string; input: UpdateTaskInput }>(
    `mutation UpdateTask($taskId: String!, $input: UpdateTaskInput!) {
      updateTask(taskId: $taskId, input: $input) {
        success
        task {
          id
          title
          description
          priority
          status
          updatedAt
        }
        message
      }
    }`,
    options
  );
};

export const useStartPomodoro = (
  options?: UseMutationOptions<{ startPomodoro: PomodoroResult }, { input: StartPomodoroInput }>
) => {
  return useMutation<{ startPomodoro: PomodoroResult }, { input: StartPomodoroInput }>(
    `mutation StartPomodoro($input: StartPomodoroInput!) {
      startPomodoro(input: $input) {
        success
        session {
          id
          taskId
          durationMinutes
          startedAt
          status
        }
        message
      }
    }`,
    options
  );
};

// Dashboard hook with fallback mock data
export const useDashboard = (options?: UseQueryOptions) => {
  const result = useQuery<{
    health: string;
    memoryStats: MemoryStats;
    taskStats: TaskStats;
    tasks: Task[];
    memories: Memory[];
  }>(
    `query Dashboard {
      health
      memoryStats {
        success
        qdrantVectors
        neo4jNodes
        relations
        cache {
          hits
          misses
          hitRate
        }
        status
      }
      taskStats {
        success
        totalTasks
        pending
        inProgress
        completed
        completedToday
        totalPomodoros
      }
      tasks(status: "in-progress", limit: 5) {
        id
        title
        priority
        status
        dueDate
      }
      memories(query: "recent context", limit: 3, includeRelations: false) {
        text
        timestamp
        tags
        type
      }
    }`,
    undefined,
    options
  );

  // Return mock data if there's an error and no data
  if (result.error && !result.data) {
    return {
      ...result,
      data: getMockDashboardData(),
      loading: false,
    };
  }

  return result;
};

// ============= REAL NEO4J API HOOKS (from BCI Backend) =============

// Helper to parse Neo4j JSON properties
function parseNodeProperties(propertiesString: string): any {
  try {
    return JSON.parse(propertiesString);
  } catch {
    return {};
  }
}

// Database Schema (real API)
export const useDatabaseSchema = (options?: UseQueryOptions) => {
  const result = useQuery<{
    databaseSchema: {
      success: boolean;
      labels: Array<{ name: string; count: number }>;
      relationshipTypes: Array<{ name: string }>;
    };
  }>(
    `query {
      databaseSchema {
        success
        labels {
          name
          count
        }
        relationshipTypes {
          name
        }
      }
    }`,
    undefined,
    options
  );

  if (result.error && !result.data) {
    // Fallback mock data
    return {
      ...result,
      data: {
        databaseSchema: {
          success: true,
          labels: [
            { name: 'Memory', count: 270 },
            { name: 'Task', count: 42 },
            { name: 'User', count: 5 },
            { name: 'Project', count: 8 },
          ],
          relationshipTypes: [
            { name: 'RELATES_TO' },
            { name: 'DEPENDS_ON' },
            { name: 'USES' },
          ],
        },
      },
      loading: false,
    };
  }

  return result;
};

// Database Nodes (real API) - Returns raw JSON strings
export const useDatabaseNodes = (
  variables: {
    label: string;
    limit?: number;
    offset?: number;
  },
  options?: UseQueryOptions
) => {
  const result = useQuery<{
    databaseNodes: Array<{ properties: string }>;
  }>(
    `query GetDatabaseNodes($label: String!, $limit: Int, $offset: Int) {
      databaseNodes(label: $label, limit: $limit, offset: $offset) {
        properties
      }
    }`,
    variables,
    options
  );

  if (result.error && !result.data) {
    // Fallback mock data
    const mockNodes = variables.label === 'Memory' 
      ? getMockNeo4jNodes().map(node => ({
          properties: JSON.stringify({
            _id: node.id,
            _labels: [variables.label],
            content: node.text,
            type: node.type,
            status: node.status,
            project: node.project,
            created_at: node.timestamp,
          }),
        }))
      : [];

    return {
      ...result,
      data: { databaseNodes: mockNodes },
      loading: false,
    };
  }

  return result;
};

// Custom Cypher Query (real API)
export const useDatabaseQuery = (
  variables: {
    cypher: string;
    parameters?: string; // JSON string
  },
  options?: UseQueryOptions
) => {
  return useQuery<{
    databaseQuery: {
      success: boolean;
      data: string; // JSON string
      count: number;
      message: string;
    };
  }>(
    `query CustomDatabaseQuery($cypher: String!, $parameters: String) {
      databaseQuery(cypher: $cypher, parameters: $parameters) {
        success
        data
        count
        message
      }
    }`,
    variables,
    options
  );
};

// Create Node (mutation)
export const useCreateNode = (
  options?: UseMutationOptions<
    { createNode: { success: boolean; nodeId: string; message: string } },
    { input: { label: string; properties: string } }
  >
) => {
  return useMutation<
    { createNode: { success: boolean; nodeId: string; message: string } },
    { input: { label: string; properties: string } }
  >(
    `mutation CreateNode($input: CreateNodeInput!) {
      createNode(input: $input) {
        success
        nodeId
        message
      }
    }`,
    options
  );
};

// Update Node (mutation)
export const useUpdateNode = (
  options?: UseMutationOptions<
    { updateNode: { success: boolean; data: string; message: string } },
    { nodeId: string; properties: string }
  >
) => {
  return useMutation<
    { updateNode: { success: boolean; data: string; message: string } },
    { nodeId: string; properties: string }
  >(
    `mutation UpdateNode($nodeId: String!, $properties: String!) {
      updateNode(nodeId: $nodeId, properties: $properties) {
        success
        data
        message
      }
    }`,
    options
  );
};

// Delete Node (mutation)
export const useDeleteNode = (
  options?: UseMutationOptions<
    { deleteNode: { success: boolean; count: number; message: string } },
    { nodeId: string }
  >
) => {
  return useMutation<
    { deleteNode: { success: boolean; count: number; message: string } },
    { nodeId: string }
  >(
    `mutation DeleteNode($nodeId: String!) {
      deleteNode(nodeId: $nodeId) {
        success
        count
        message
      }
    }`,
    options
  );
};

// Create Relationship (mutation)
export const useCreateRelationship = (
  options?: UseMutationOptions<
    { createRelationship: { success: boolean; relationshipId: string; message: string } },
    {
      input: {
        sourceId: string;
        targetId: string;
        relationshipType: string;
        properties?: string;
      };
    }
  >
) => {
  return useMutation<
    { createRelationship: { success: boolean; relationshipId: string; message: string } },
    {
      input: {
        sourceId: string;
        targetId: string;
        relationshipType: string;
        properties?: string;
      };
    }
  >(
    `mutation CreateRelationship($input: CreateRelationshipInput!) {
      createRelationship(input: $input) {
        success
        relationshipId
        message
      }
    }`,
    options
  );
};

// ============= HEALTH & MONITORING HOOKS =============

export interface HealthCheckResult {
  healthCheck: {
    overallStatus: string;
    neo4j: {
      status: string;
      message: string;
      responseTimeMs: number | null;
      lastChecked: string;
    };
    qdrant: {
      status: string;
      message: string;
      responseTimeMs: number | null;
      lastChecked: string;
    };
    postgres: {
      status: string;
      message: string;
      responseTimeMs: number | null;
      lastChecked: string;
    };
    redis: {
      status: string;
      message: string;
      responseTimeMs: number | null;
      lastChecked: string;
    };
  };
}

export interface MetricsResult {
  metrics: {
    totalRequests: number;
    errorCount: number;
    errorRate: number;
    avgResponseTimeMs: number;
    lastError: string | null;
    lastErrorTime: string | null;
    uptimeSeconds: number;
  };
}

export interface SystemLog {
  timestamp: string;
  level: string;
  message: string;
  service: string;
  details: string | null;
}

export interface SystemLogsResult {
  systemLogs: SystemLog[];
}

// Health Check
export const useHealthCheck = (options?: UseQueryOptions) => {
  const result = useQuery<HealthCheckResult>(
    `query {
      healthCheck {
        overallStatus
        neo4j {
          status
          message
          responseTimeMs
          lastChecked
        }
        qdrant {
          status
          message
          responseTimeMs
          lastChecked
        }
        postgres {
          status
          message
          responseTimeMs
          lastChecked
        }
        redis {
          status
          message
          responseTimeMs
          lastChecked
        }
      }
    }`,
    undefined,
    options
  );

  if (result.error && !result.data) {
    return {
      ...result,
      data: {
        healthCheck: {
          overallStatus: "unknown",
          neo4j: {
            status: "unknown",
            message: "Unable to connect to backend",
            responseTimeMs: null,
            lastChecked: new Date().toISOString(),
          },
          qdrant: {
            status: "unknown",
            message: "Unable to connect to backend",
            responseTimeMs: null,
            lastChecked: new Date().toISOString(),
          },
          postgres: {
            status: "unknown",
            message: "Unable to connect to backend",
            responseTimeMs: null,
            lastChecked: new Date().toISOString(),
          },
          redis: {
            status: "unknown",
            message: "Unable to connect to backend",
            responseTimeMs: null,
            lastChecked: new Date().toISOString(),
          },
        },
      },
      loading: false,
    };
  }

  return result;
};

// System Metrics
export const useMetrics = (options?: UseQueryOptions) => {
  const result = useQuery<MetricsResult>(
    `query {
      metrics {
        totalRequests
        errorCount
        errorRate
        avgResponseTimeMs
        lastError
        lastErrorTime
        uptimeSeconds
      }
    }`,
    undefined,
    options
  );

  if (result.error && !result.data) {
    return {
      ...result,
      data: {
        metrics: {
          totalRequests: 0,
          errorCount: 0,
          errorRate: 0,
          avgResponseTimeMs: 0,
          lastError: null,
          lastErrorTime: null,
          uptimeSeconds: 0,
        },
      },
      loading: false,
    };
  }

  return result;
};

// System Logs
export const useSystemLogs = (
  variables?: {
    limit?: number;
    level?: string;
    service?: string;
  },
  options?: UseQueryOptions
) => {
  const result = useQuery<SystemLogsResult>(
    `query SystemLogs($limit: Int, $level: String, $service: String) {
      systemLogs(limit: $limit, level: $level, service: $service) {
        timestamp
        level
        message
        service
        details
      }
    }`,
    variables,
    options
  );

  if (result.error && !result.data) {
    return {
      ...result,
      data: {
        systemLogs: [
          {
            timestamp: new Date().toISOString(),
            level: "INFO",
            message: "Mock data - Backend offline",
            service: "system",
            details: null,
          },
        ],
      },
      loading: false,
    };
  }

  return result;
};

// Helper hook to get parsed nodes (with automatic JSON parsing)
export const useParsedDatabaseNodes = (
  variables: {
    label: string;
    limit?: number;
    offset?: number;
  },
  options?: UseQueryOptions
) => {
  const result = useDatabaseNodes(variables, options);

  if (!result.data) {
    return result;
  }

  // Parse all properties from JSON strings
  const parsedNodes = result.data.databaseNodes.map((node) => parseNodeProperties(node.properties));

  return {
    ...result,
    data: {
      databaseNodes: parsedNodes,
    },
  };
};

// Neo4j exploration hook with fallback
export const useNeo4jExplore = (options?: UseQueryOptions) => {
  const result = useQuery<{
    neo4jSchema: Neo4jSchema;
    neo4jNodes: Neo4jNode[];
    neo4jRelations: Neo4jRelation[];
  }>(
    `query ExploreNeo4j {
      neo4jSchema {
        success
        tables {
          label
          count
          icon
        }
        relationshipTypes
        totalTables
      }
      neo4jNodes(limit: 20) {
        id
        text
        type
        project
        timestamp
      }
      neo4jRelations(limit: 10) {
        sourceId
        sourceText
        relationType
        targetId
        targetText
      }
    }`,
    undefined,
    options
  );

  if (result.error && !result.data) {
    return {
      ...result,
      data: {
        neo4jSchema: getMockNeo4jSchema(),
        neo4jNodes: getMockNeo4jNodes(),
        neo4jRelations: getMockNeo4jRelations(),
      },
      loading: false,
    };
  }

  return result;
};


// ============= TYPE MANAGEMENT MUTATIONS =============

// Custom Cypher Mutation helper
export const useCypherMutation = (
  options?: UseMutationOptions<
    { databaseQuery: { success: boolean; data: string; count: number; message: string } },
    { cypher: string; parameters?: Record<string, any> }
  >
) => {
  return useMutation<
    { databaseQuery: { success: boolean; data: string; count: number; message: string } },
    { cypher: string; parameters?: Record<string, any> }
  >(
    `mutation ExecuteCypher($cypher: String!, $parameters: String) {
      databaseQuery(cypher: $cypher, parameters: $parameters) {
        success
        data
        count
        message
      }
    }`,
    {
      ...options,
      onCompleted: (data) => {
        options?.onCompleted?.(data);
      },
    }
  );
};
