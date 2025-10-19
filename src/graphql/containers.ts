/**
 * GraphQL Queries & Mutations for Containers/Blocks/Tasks
 */

import { gql } from '@apollo/client/core';

// ============================================================================
// FRAGMENTS
// ============================================================================

export const TASK_FRAGMENT = gql`
  fragment TaskFields on Task {
    id
    title
    description
    completed
    blockId
    createdAt
    completedAt
  }
`;

export const BLOCK_FRAGMENT = gql`
  fragment BlockFields on Block {
    id
    name
    duration
    position
    color
    tasks {
      ...TaskFields
    }
  }
  ${TASK_FRAGMENT}
`;

export const CONTAINER_FRAGMENT = gql`
  fragment ContainerFields on Container {
    id
    name
    totalDuration
    pauseAfter
    status
    locked
    progress
    currentBlockIndex
    color
    isTemplate
    createdAt
    startedAt
    completedAt
    blocks {
      ...BlockFields
    }
  }
  ${BLOCK_FRAGMENT}
`;

// ============================================================================
// QUERIES
// ============================================================================

export const GET_ALL_CONTAINERS = gql`
  query GetAllContainers {
    getAllContainers {
      ...ContainerFields
    }
  }
  ${CONTAINER_FRAGMENT}
`;

export const GET_CONTAINER = gql`
  query GetContainer($id: String!) {
    getContainer(id: $id) {
      ...ContainerFields
    }
  }
  ${CONTAINER_FRAGMENT}
`;

// ============================================================================
// MUTATIONS
// ============================================================================

export const CREATE_CONTAINER = gql`
  mutation CreateContainer($input: CreateContainerInput!) {
    createContainer(input: $input) {
      ...ContainerFields
    }
  }
  ${CONTAINER_FRAGMENT}
`;

export const UPDATE_CONTAINER = gql`
  mutation UpdateContainer($id: String!, $input: UpdateContainerInput!) {
    updateContainer(id: $id, input: $input) {
      ...ContainerFields
    }
  }
  ${CONTAINER_FRAGMENT}
`;

export const DELETE_CONTAINER = gql`
  mutation DeleteContainer($id: String!) {
    deleteContainer(id: $id)
  }
`;

export const UPDATE_BLOCKS = gql`
  mutation UpdateBlocks($containerId: String!, $blocks: [BlockInput!]!) {
    updateBlocks(containerId: $containerId, blocks: $blocks) {
      ...ContainerFields
    }
  }
  ${CONTAINER_FRAGMENT}
`;

export const ADD_TASK = gql`
  mutation AddTask($blockId: String!, $title: String!, $description: String) {
    addTask(blockId: $blockId, title: $title, description: $description) {
      ...TaskFields
    }
  }
  ${TASK_FRAGMENT}
`;

export const TOGGLE_TASK = gql`
  mutation ToggleTask($taskId: String!, $completed: Boolean!) {
    toggleTask(taskId: $taskId, completed: $completed) {
      ...TaskFields
    }
  }
  ${TASK_FRAGMENT}
`;
