import { useQuery, useMutation } from '@apollo/client/react';
import { useCallback } from 'react';
import type { BlockContainer, ContainerBlock, BlockTask } from '../types/timeblock';
import {
  GET_ALL_CONTAINERS,
  CREATE_CONTAINER,
  UPDATE_CONTAINER,
  DELETE_CONTAINER,
  UPDATE_BLOCKS,
  ADD_TASK,
  TOGGLE_TASK,
} from '../graphql/containers';

export function useContainers() {
  // Query: Fetch all containers
  const { data, loading, error, refetch } = useQuery(GET_ALL_CONTAINERS, {
    fetchPolicy: 'cache-and-network',
  });

  // Mutations
  const [createContainerMutation] = useMutation(CREATE_CONTAINER);
  const [updateContainerMutation] = useMutation(UPDATE_CONTAINER);
  const [deleteContainerMutation] = useMutation(DELETE_CONTAINER);
  const [updateBlocksMutation] = useMutation(UPDATE_BLOCKS);
  const [addTaskMutation] = useMutation(ADD_TASK);
  const [toggleTaskMutation] = useMutation(TOGGLE_TASK);

  const containers: BlockContainer[] = data?.getAllContainers || [];

  // Create container
  const createContainer = useCallback(
    async (container: BlockContainer) => {
      try {
        await createContainerMutation({
          variables: {
            input: {
              name: container.name,
              totalDuration: container.totalDuration,
              pauseAfter: container.pauseAfter,
              color: container.color,
            },
          },
          refetchQueries: [{ query: GET_ALL_CONTAINERS }],
        });
      } catch (err) {
        console.error('Failed to create container:', err);
        throw err;
      }
    },
    [createContainerMutation]
  );

  // Update container
  const updateContainer = useCallback(
    async (containerId: string, updates: Partial<BlockContainer>) => {
      try {
        await updateContainerMutation({
          variables: {
            id: containerId,
            input: {
              name: updates.name,
              totalDuration: updates.totalDuration,
              pauseAfter: updates.pauseAfter,
              status: updates.status,
              locked: updates.locked,
              progress: updates.progress,
              currentBlockIndex: updates.currentBlockIndex,
              color: updates.color,
            },
          },
          refetchQueries: [{ query: GET_ALL_CONTAINERS }],
        });
      } catch (err) {
        console.error('Failed to update container:', err);
        throw err;
      }
    },
    [updateContainerMutation]
  );

  // Delete container
  const deleteContainer = useCallback(
    async (containerId: string) => {
      try {
        await deleteContainerMutation({
          variables: { id: containerId },
          refetchQueries: [{ query: GET_ALL_CONTAINERS }],
        });
      } catch (err) {
        console.error('Failed to delete container:', err);
        throw err;
      }
    },
    [deleteContainerMutation]
  );

  // Duplicate container
  const duplicateContainer = useCallback(
    async (containerId: string) => {
      const container = containers.find((c) => c.id === containerId);
      if (!container) return;

      try {
        await createContainerMutation({
          variables: {
            input: {
              name: `${container.name} (copy)`,
              totalDuration: container.totalDuration,
              pauseAfter: container.pauseAfter,
              color: container.color,
            },
          },
          refetchQueries: [{ query: GET_ALL_CONTAINERS }],
        });
      } catch (err) {
        console.error('Failed to duplicate container:', err);
        throw err;
      }
    },
    [containers, createContainerMutation]
  );

  // Start container (lock it)
  const startContainer = useCallback(
    async (containerId: string) => {
      try {
        await updateContainerMutation({
          variables: {
            id: containerId,
            input: {
              status: 'locked',
              locked: true,
            },
          },
          refetchQueries: [{ query: GET_ALL_CONTAINERS }],
        });
      } catch (err) {
        console.error('Failed to start container:', err);
        throw err;
      }
    },
    [updateContainerMutation]
  );

  // Update container progress
  const updateProgress = useCallback(
    async (containerId: string, minutes: number) => {
      const container = containers.find((c) => c.id === containerId);
      if (!container) return;

      const newProgress = container.progress + minutes;
      const completed = newProgress >= container.totalDuration;

      try {
        await updateContainerMutation({
          variables: {
            id: containerId,
            input: {
              progress: newProgress,
              status: completed ? 'completed' : container.status,
              locked: !completed,
            },
          },
          refetchQueries: [{ query: GET_ALL_CONTAINERS }],
        });
      } catch (err) {
        console.error('Failed to update progress:', err);
        throw err;
      }
    },
    [containers, updateContainerMutation]
  );

  // Add task to block
  const addTask = useCallback(
    async (containerId: string, blockId: string, taskTitle: string) => {
      try {
        await addTaskMutation({
          variables: {
            blockId,
            title: taskTitle,
          },
          refetchQueries: [{ query: GET_ALL_CONTAINERS }],
        });
      } catch (err) {
        console.error('Failed to add task:', err);
        throw err;
      }
    },
    [addTaskMutation]
  );

  // Toggle task completion
  const toggleTask = useCallback(
    async (containerId: string, blockId: string, taskId: string) => {
      const container = containers.find((c) => c.id === containerId);
      if (!container) return;

      const block = container.blocks.find((b) => b.id === blockId);
      if (!block) return;

      const task = block.tasks?.find((t) => t.id === taskId);
      if (!task) return;

      try {
        await toggleTaskMutation({
          variables: {
            taskId,
            completed: !task.completed,
          },
          refetchQueries: [{ query: GET_ALL_CONTAINERS }],
        });
      } catch (err) {
        console.error('Failed to toggle task:', err);
        throw err;
      }
    },
    [containers, toggleTaskMutation]
  );

  // Delete task
  const deleteTask = useCallback(
    async (containerId: string, blockId: string, taskId: string) => {
      // TODO: Add DELETE_TASK mutation
      console.warn('deleteTask not implemented yet');
    },
    []
  );

  // Get active container
  const activeContainer = containers.find((c) => c.locked);

  // Get stats
  const stats = {
    total: containers.length,
    idle: containers.filter((c) => c.status === 'idle').length,
    active: containers.filter((c) => c.locked).length,
    completed: containers.filter((c) => c.status === 'completed').length,
  };

  return {
    containers,
    activeContainer,
    stats,
    loading,
    error,
    refetch,
    createContainer,
    updateContainer,
    deleteContainer,
    duplicateContainer,
    startContainer,
    updateProgress,
    addTask,
    toggleTask,
    deleteTask,
  };
}
