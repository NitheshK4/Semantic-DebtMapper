import React, { useEffect, useState } from "react";
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  MarkerType,
} from "reactflow";
import "reactflow/dist/style.css";
import { api, GraphData, GraphNode } from "../api/client";
import { Info, HelpCircle } from "lucide-react";

interface LineageGraphProps {
  projectId: string;
}

export const LineageGraph: React.FC<LineageGraphProps> = ({ projectId }) => {
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);

  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  useEffect(() => {
    const fetchLineage = async () => {
      try {
        const data = await api.getLatestLineage(projectId);
        setGraphData(data);
        setError(null);
      } catch {
        setError(
          "Please run an audit first to generate the Semantic Lineage Graph.",
        );
      }
    };
    fetchLineage();
  }, [projectId]);

  useEffect(() => {
    if (!graphData) return;

    // Structure coordinates in vertical columns (X) based on node types
    const colWidths: Record<string, number> = {
      concept: 50,
      label_class: 250,
      model_version: 450,
      rule: 650,
      prompt_version: 650,
      feature: 850,
      segment: 1050,
    };

    // Calculate Y coordinates per type to stack them vertically
    const yOffsets: Record<string, number> = {};

    const rfNodes = graphData.nodes.map((node) => {
      const type = node.type;
      const x = colWidths[type] || 500;

      if (yOffsets[type] === undefined) {
        yOffsets[type] = 50;
      } else {
        yOffsets[type] += 90;
      }
      const y = yOffsets[type];

      // Custom node color styling matching our enterprise theme
      let bgStyle = "bg-[#0c0f18] border-white/5 text-white";
      if (type === "concept")
        bgStyle =
          "bg-[#0d1121] border-indigo-500/20 text-indigo-300 hover:border-indigo-400/40";
      else if (type === "label_class")
        bgStyle =
          "bg-[#09121d] border-sky-500/20 text-sky-300 hover:border-sky-400/40";
      else if (type === "model_version")
        bgStyle =
          "bg-[#100e21] border-purple-500/20 text-purple-300 hover:border-purple-400/40";
      else if (type === "rule")
        bgStyle =
          "bg-[#130f0b] border-amber-500/20 text-amber-300 hover:border-amber-400/40";
      else if (type === "prompt_version")
        bgStyle =
          "bg-[#081315] border-teal-500/20 text-teal-300 hover:border-teal-400/40";
      else if (type === "feature")
        bgStyle =
          "bg-[#08130e] border-emerald-500/20 text-emerald-300 hover:border-emerald-400/40";
      else if (type === "segment")
        bgStyle =
          "bg-[#11131b] border-white/5 text-slate-350 hover:border-white/10";

      return {
        id: node.id,
        position: { x, y },
        data: { label: node.label, nodeData: node },
        className: `px-3.5 py-2.5 rounded-xl border text-[10px] font-bold uppercase tracking-wider shadow-lg cursor-pointer transition-all hover:scale-[1.03] duration-150 ${bgStyle}`,
        style: { width: 155 },
      };
    });

    const rfEdges = graphData.edges.map((edge, idx) => {
      // Color matching edge source type
      let edgeColor = "rgba(255, 255, 255, 0.08)";
      if (edge.type === "defines") edgeColor = "rgba(99, 102, 241, 0.35)";
      else if (edge.type === "predicts") edgeColor = "rgba(14, 165, 233, 0.35)";
      else if (edge.type === "post_processes")
        edgeColor = "rgba(245, 158, 11, 0.35)";
      else if (edge.type === "uses_feature")
        edgeColor = "rgba(16, 185, 129, 0.35)";

      return {
        id: `e-${idx}`,
        source: edge.source,
        target: edge.target,
        type: "smoothstep",
        animated: edge.type === "predicts" || edge.type === "defines",
        style: { stroke: edgeColor, strokeWidth: 1.5 },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: edgeColor,
        },
      };
    });

    setNodes(rfNodes);
    setEdges(rfEdges);
  }, [graphData, setNodes, setEdges]);

  const onNodeClick = (
    _event: React.MouseEvent,
    node: { data: { nodeData: GraphNode } },
  ) => {
    setSelectedNode(node.data.nodeData);
  };

  return (
    <div className="glass-panel p-6 rounded-2xl animate-fade-in flex flex-col h-[650px] relative">
      <div className="mb-4">
        <h2 className="text-base font-bold text-white tracking-tight">
          Semantic Lineage Graph
        </h2>
        <p className="text-xs text-gray-500">
          Trace lineage maps across prompt templates, active feature inputs,
          legacy models, and rules
        </p>
      </div>

      {error ? (
        <div className="flex-1 flex items-center justify-center text-center text-gray-550">
          <div>
            <HelpCircle className="w-10 h-10 text-gray-700 mx-auto mb-2.5" />
            <p className="text-xs font-semibold">{error}</p>
          </div>
        </div>
      ) : (
        <div className="flex-1 flex flex-col lg:flex-row gap-6 relative">
          {/* React Flow Box */}
          <div className="flex-1 border border-white/5 rounded-xl overflow-hidden bg-[#07090e]/40 relative min-h-[300px]">
            <ReactFlow
              nodes={nodes}
              edges={edges}
              onNodeClick={onNodeClick}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              fitView
              maxZoom={1.5}
              minZoom={0.5}
            >
              <Background
                color="#1e293b"
                gap={20}
                size={1.0}
                className="opacity-[0.15]"
              />
              <Controls className="bg-[#0c0f18] border border-white/5 text-white" />
              <MiniMap
                nodeStrokeColor={(n: { className?: string }) => {
                  if (n.className?.includes("border-indigo-500"))
                    return "#6366f1";
                  if (n.className?.includes("border-sky-500")) return "#0ea5e9";
                  if (n.className?.includes("border-purple-500"))
                    return "#a855f7";
                  return "#374151";
                }}
                nodeColor={() => "rgba(13, 17, 28, 0.9)"}
                className="bg-[#0c0f18] border border-white/5"
              />
            </ReactFlow>
          </div>

          {/* Node Metadata Details Pane */}
          <div className="w-full lg:w-72 border border-white/5 bg-[#0a0d16]/30 rounded-xl p-5 overflow-y-auto max-h-[500px] space-y-4">
            {selectedNode ? (
              <div className="space-y-4">
                <div>
                  <span className="text-[9px] font-bold uppercase tracking-widest text-indigo-400 block mb-0.5">
                    {selectedNode.type}
                  </span>
                  <h3 className="text-sm font-bold text-white tracking-tight leading-snug">
                    {selectedNode.label}
                  </h3>
                </div>

                <hr className="border-white/5" />

                <div className="space-y-3.5 text-xs">
                  {selectedNode.metadata &&
                    Object.entries(selectedNode.metadata).map(([k, v]) => {
                      if (!v) return null;
                      return (
                        <div key={k} className="space-y-1">
                          <span className="text-gray-500 block font-medium capitalize">
                            {k.replace(/_/g, " ")}:
                          </span>
                          {typeof v === "object" ? (
                            <div className="flex flex-wrap gap-1.5 pt-1">
                              {Object.entries(v).map(([segKey, segVal]) => (
                                <span
                                  key={segKey}
                                  className="px-2 py-0.5 bg-white/5 border border-white/5 text-[10px] rounded font-mono text-gray-300"
                                >
                                  {segKey}={String(segVal)}
                                </span>
                              ))}
                            </div>
                          ) : (
                            <span className="text-gray-200 leading-relaxed block font-mono bg-white/[0.01] border border-white/[0.02] p-2 rounded">
                              {String(v)}
                            </span>
                          )}
                        </div>
                      );
                    })}
                </div>
              </div>
            ) : (
              <div className="text-center py-16 text-gray-500 flex flex-col items-center justify-center">
                <Info className="w-8 h-8 text-gray-700 mb-2.5" />
                <p className="text-xs font-semibold text-gray-400">
                  Node telemetry details
                </p>
                <p className="text-[11px] text-gray-500 leading-relaxed mt-1 px-4">
                  Select a node on the canvas to trace its version state,
                  schemas, and dependencies.
                </p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
