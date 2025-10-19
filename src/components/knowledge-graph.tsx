import { useCallback, useMemo } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  addEdge,
  Connection,
  Node,
  Edge,
  MarkerType,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import type { GraphNode as GraphNodeType, GraphRelation } from '../lib/graphql-hooks';

interface KnowledgeGraphProps {
  nodes: GraphNodeType[];
  relations: GraphRelation[];
}

const nodeColors = {
  Memory: '#3b82f6',
  Knowledge: '#10b981',
  Task: '#f59e0b',
};

export function KnowledgeGraph({ nodes: graphNodes, relations }: KnowledgeGraphProps) {
  // Convert GraphQL nodes to React Flow nodes
  const initialNodes: Node[] = useMemo(() => {
    return graphNodes.map((node, index) => {
      const angle = (index / graphNodes.length) * 2 * Math.PI;
      const radius = Math.min(300, graphNodes.length * 20);

      return {
        id: node.id,
        type: 'default',
        data: {
          label: node.label,
        },
        position: {
          x: Math.cos(angle) * radius + 400,
          y: Math.sin(angle) * radius + 300,
        },
        style: {
          background: nodeColors[node.type as keyof typeof nodeColors] || '#6b7280',
          color: '#ffffff',
          border: 'none',
          borderRadius: '8px',
          padding: '10px 15px',
          fontSize: '12px',
          fontWeight: 500,
        },
      };
    });
  }, [graphNodes]);

  // Convert GraphQL relations to React Flow edges
  const initialEdges: Edge[] = useMemo(() => {
    return relations.map((relation) => ({
      id: relation.id,
      source: relation.source,
      target: relation.target,
      type: 'smoothstep',
      animated: relation.weight > 0.7,
      style: {
        stroke: '#94a3b8',
        strokeWidth: Math.max(1, relation.weight * 3),
      },
      markerEnd: {
        type: MarkerType.ArrowClosed,
        color: '#94a3b8',
      },
      label: relation.type,
      labelStyle: {
        fontSize: '10px',
        fill: '#64748b',
      },
      labelBgStyle: {
        fill: '#ffffff',
      },
    }));
  }, [relations]);

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges],
  );

  return (
    <div className="w-full h-[600px] border rounded-lg bg-background">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        fitView
        attributionPosition="bottom-left"
      >
        <Background />
        <Controls />
        <MiniMap
          nodeColor={(node) => {
            const typeNode = graphNodes.find((n) => n.id === node.id);
            return nodeColors[typeNode?.type as keyof typeof nodeColors] || '#6b7280';
          }}
          nodeBorderRadius={8}
        />
      </ReactFlow>
    </div>
  );
}
