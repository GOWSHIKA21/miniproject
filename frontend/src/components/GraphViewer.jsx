import { useCallback } from 'react';
import {
  ReactFlow,
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  addEdge,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

const initialNodes = [
  { id: '1', position: { x: 250, y: 50 }, data: { label: 'AI Crop Disease Detection' }, type: 'input', style: { background: '#4f46e5', color: 'white', borderRadius: '8px', border: 'none', padding: '10px 15px', fontWeight: 'bold' } },
  { id: '2', position: { x: 100, y: 150 }, data: { label: 'Artificial Intelligence' }, style: { background: '#e0e7ff', color: '#4f46e5', border: '1px solid #c7d2fe', borderRadius: '8px' } },
  { id: '3', position: { x: 400, y: 150 }, data: { label: 'Agriculture' }, style: { background: '#e0e7ff', color: '#4f46e5', border: '1px solid #c7d2fe', borderRadius: '8px' } },
  { id: '4', position: { x: 250, y: 150 }, data: { label: 'Arun Kumar (Inventor)' }, style: { background: '#fef3c7', color: '#d97706', border: '1px solid #fde68a', borderRadius: '8px' } },
  { id: '5', position: { x: 250, y: 250 }, data: { label: 'ABC Technologies (Org)' }, style: { background: '#dcfce7', color: '#16a34a', border: '1px solid #bbf7d0', borderRadius: '8px' } },
  { id: '6', position: { x: 100, y: 250 }, data: { label: 'Computer Vision' }, style: { background: '#e0e7ff', color: '#4f46e5', border: '1px solid #c7d2fe', borderRadius: '8px' } },
  { id: '7', position: { x: 400, y: 250 }, data: { label: 'IPC: A01G' }, style: { background: '#f3f4f6', color: '#4b5563', border: '1px solid #e5e7eb', borderRadius: '8px' } },
];

const initialEdges = [
  { id: 'e1-2', source: '1', target: '2', animated: true, label: 'has technology', style: { stroke: '#94a3b8' } },
  { id: 'e1-3', source: '1', target: '3', animated: true, label: 'belongs to field', style: { stroke: '#94a3b8' } },
  { id: 'e1-4', source: '1', target: '4', label: 'invented by', style: { stroke: '#94a3b8' } },
  { id: 'e4-5', source: '4', target: '5', label: 'affiliated with', style: { stroke: '#94a3b8' } },
  { id: 'e2-6', source: '2', target: '6', label: 'sub-field', style: { stroke: '#94a3b8' } },
  { id: 'e1-7', source: '1', target: '7', label: 'classified as', style: { stroke: '#94a3b8' } },
];

export default function GraphViewer() {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  const onConnect = useCallback((params) => setEdges((eds) => addEdge(params, eds)), [setEdges]);

  return (
    <div style={{ width: '100%', height: '500px' }} className="border border-slate-200 rounded-xl overflow-hidden bg-white shadow-inner">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        fitView
        attributionPosition="bottom-right"
      >
        <Controls />
        <MiniMap nodeStrokeColor={(n) => {
          if (n.type === 'input') return '#4f46e5';
          return '#cbd5e1';
        }} nodeColor={(n) => {
          if (n.type === 'input') return '#4f46e5';
          return '#fff';
        }} />
        <Background color="#94a3b8" gap={16} size={1} />
      </ReactFlow>
    </div>
  );
}
