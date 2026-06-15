import React, { useState } from "react";
import { api } from "../api/client";
import {
  Database,
  Settings,
  ArrowRight,
  Play,
  CheckCircle,
  RefreshCw,
} from "lucide-react";

interface IngestionCenterProps {
  projectId: string;
  onAuditComplete: () => Promise<void>;
}

export const IngestionCenter: React.FC<IngestionCenterProps> = ({
  projectId,
  onAuditComplete,
}) => {
  const [seeding, setSeeding] = useState<boolean>(false);
  const [auditing, setAuditing] = useState<boolean>(false);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);

  const [jsonType, setJsonType] = useState<string>("model-versions");
  const [jsonPayload, setJsonPayload] = useState<string>("");
  const [ingesting, setIngesting] = useState<boolean>(false);

  const handleSeed = async () => {
    setSeeding(true);
    setStatusMsg("Bootstrapping Support Ticket Classifier demo dataset...");
    try {
      // Create project is done. We can trigger demo imports.
      // Fetch models, label schemas, rules, prompts, and CSVs.
      // Since seed_demo.py does this, we can call a series of ingest requests via api client using mock loads or read datasets locally in browser.
      // Wait, we can implement the exact seeding sequence in this browser function since the browser has access to the workspace if needed,
      // but wait! The frontend runs inside a browser sandbox, so it can't read files directly from the local file system.
      // But we can add a seed endpoint in the backend, or we can write a backend route `POST /projects/{project_id}/seed`
      // which loads files from `datasets/demo_support_tickets` and seeds the database directly!
      // This is a brilliant, highly reliable idea! Let's check:
      // If we create a route in FastAPI `POST /api/v1/projects/{project_id}/seed` that seeds the database using the datasets folder,
      // then the frontend can trigger it with a single click! Let's implement this endpoint!
      // Let's first make sure the frontend calls: `await fetch('/api/v1/projects/{projectId}/seed')`.
      const API_URL =
        import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";
      const res = await fetch(`${API_URL}/projects/${projectId}/seed`, {
        method: "POST",
        headers: {
          "X-API-Key": import.meta.env.VITE_API_KEY || "",
        },
      });
      if (!res.ok) throw new Error(await res.text());

      setStatusMsg("Seeding completed successfully! Dataset active.");
      // Trigger audit run automatically after seeding
      handleRunAudit();
    } catch (e) {
      console.error(e);
      setStatusMsg(
        `Seeding failed: ${e instanceof Error ? e.message : String(e)}`,
      );
    } finally {
      setSeeding(false);
    }
  };

  const handleRunAudit = async () => {
    setAuditing(true);
    setStatusMsg(
      "Running detectors (CMD, ESF, RMC, HMD, GFM) and computing score...",
    );
    try {
      await api.runAudit(
        projectId,
        ["CMD", "ESF", "RMC", "HMD", "GFM"],
        undefined,
        true,
      );
      setStatusMsg("Semantic lineage audit finished. Score updated.");
      await onAuditComplete();
    } catch (e) {
      setStatusMsg(
        `Audit failed: ${e instanceof Error ? e.message : String(e)}`,
      );
    } finally {
      setAuditing(false);
    }
  };

  const handleIngestJson = async () => {
    if (!jsonPayload.trim()) return;
    setIngesting(true);
    setStatusMsg(`Ingesting custom ${jsonType} data...`);
    try {
      const parsed = JSON.parse(jsonPayload);
      const data = Array.isArray(parsed) ? parsed : [parsed];
      await api.ingestData(projectId, jsonType, data);
      setStatusMsg(`Successfully ingested custom ${jsonType} record.`);
      setJsonPayload("");
    } catch (e) {
      setStatusMsg(
        `Ingestion failed: ${e instanceof Error ? e.message : "Invalid JSON"}`,
      );
    } finally {
      setIngesting(false);
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Top Controller: Seed / Run Audit */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Bootstrap Card */}
        <div className="glass-panel p-6 rounded-2xl flex flex-col justify-between space-y-4 border border-gray-800">
          <div className="space-y-2">
            <div className="flex items-center space-x-2">
              <Database className="w-5 h-5 text-indigo-400" />
              <h3 className="text-base font-bold text-white">
                Bootstrap Demo Dataset
              </h3>
            </div>
            <p className="text-xs text-gray-400 leading-relaxed">
              Populate the pipeline with deployment histories, v2/v3 label
              schemas, business rules, prompts, 30 inference records, and 18
              manual overrides containing intentional semantic debt events.
            </p>
          </div>
          <button
            onClick={handleSeed}
            disabled={seeding || auditing}
            className="w-full bg-indigo-600 hover:bg-indigo-500 disabled:bg-indigo-800 disabled:opacity-50 text-xs font-bold text-white py-2.5 rounded-xl transition-colors flex items-center justify-center space-x-1"
          >
            {seeding ? (
              <RefreshCw className="w-4 h-4 animate-spin mr-1" />
            ) : (
              <Database className="w-4 h-4 mr-1" />
            )}
            {seeding ? "Importing Data..." : "Load Support Ticket Demo"}
          </button>
        </div>

        {/* Audit Controller */}
        <div className="glass-panel p-6 rounded-2xl flex flex-col justify-between space-y-4 border border-gray-800">
          <div className="space-y-2">
            <div className="flex items-center space-x-2">
              <Play className="w-5 h-5 text-emerald-400" />
              <h3 className="text-base font-bold text-white">
                Run Semantic Audit
              </h3>
            </div>
            <p className="text-xs text-gray-400 leading-relaxed">
              Orchestrate a pipeline sweep: compute cosine text-embeddings
              difference (CMD), index geometric drift (ESF), rule calibration
              conflicts (RMC), override divergence (HMD), and ghost features
              (GFM).
            </p>
          </div>
          <button
            onClick={handleRunAudit}
            disabled={seeding || auditing}
            className="w-full bg-emerald-600 hover:bg-emerald-500 disabled:bg-emerald-800 disabled:opacity-50 text-xs font-bold text-white py-2.5 rounded-xl transition-colors flex items-center justify-center space-x-1"
          >
            {auditing ? (
              <RefreshCw className="w-4 h-4 animate-spin mr-1" />
            ) : (
              <Play className="w-4 h-4 mr-1" />
            )}
            {auditing ? "Analyzing Pipeline..." : "Execute Audit Now"}
          </button>
        </div>
      </div>

      {/* Seeding / Audit Status Output Banner */}
      {statusMsg && (
        <div className="glass-panel px-5 py-3.5 rounded-xl flex items-center space-x-2.5 border border-indigo-500/20 text-xs text-indigo-300">
          <CheckCircle className="w-4 h-4 text-indigo-400 shrink-0" />
          <span>{statusMsg}</span>
        </div>
      )}

      {/* Manual JSON Ingestion Form */}
      <div className="glass-panel p-6 rounded-2xl border border-gray-800 space-y-4">
        <div>
          <h3 className="text-base font-bold text-white flex items-center">
            <Settings className="w-4.5 h-4.5 text-gray-400 mr-2" /> Manual
            Ingestion API Console
          </h3>
          <p className="text-xs text-gray-400 mt-1">
            Submit custom model versions, label definitions, or telemetry logs
            directly to the project
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
          <div className="lg:col-span-1 space-y-2">
            <label className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
              Record Type
            </label>
            <select
              value={jsonType}
              onChange={(e) => setJsonType(e.target.value)}
              className="w-full bg-gray-950/80 border border-gray-800 rounded-xl px-3 py-2 text-xs text-gray-200 focus:outline-none focus:border-indigo-500 capitalize"
            >
              <option value="model-versions">Model Versions</option>
              <option value="label-schemas">Label Schemas</option>
              <option value="rules">Business Rules</option>
              <option value="prompts">Prompt Versions</option>
              <option value="inferences:batch">Inference Log Batch</option>
              <option value="overrides:batch">Override Log Batch</option>
            </select>
          </div>

          <div className="lg:col-span-3 space-y-2">
            <label className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
              JSON Payload
            </label>
            <textarea
              rows={6}
              value={jsonPayload}
              onChange={(e) => setJsonPayload(e.target.value)}
              placeholder='[ { "key": "value" } ]'
              className="w-full bg-gray-950/80 border border-gray-800 rounded-xl p-3 text-xs text-indigo-300 font-mono focus:outline-none focus:border-indigo-500"
            />
          </div>
        </div>

        <div className="flex items-center justify-end">
          <button
            onClick={handleIngestJson}
            disabled={ingesting || !jsonPayload.trim()}
            className="bg-gray-800 hover:bg-gray-700 disabled:opacity-40 text-xs font-bold text-white px-5 py-2 rounded-xl transition-colors flex items-center"
          >
            {ingesting ? (
              <RefreshCw className="w-3.5 h-3.5 animate-spin mr-1" />
            ) : null}
            Submit Payload <ArrowRight className="w-3.5 h-3.5 ml-1" />
          </button>
        </div>
      </div>
    </div>
  );
};
