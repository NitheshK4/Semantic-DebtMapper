const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";
const API_KEY = import.meta.env.VITE_API_KEY;

if (!API_KEY) {
  console.error("VITE_API_KEY is not set in the environment.");
}

const headers = {
  "Content-Type": "application/json",
  "X-API-Key": API_KEY,
};

export interface Project {
  id: string;
  name: string;
  domain: string;
  created_at: string;
}

export interface ConceptVersion {
  id: string;
  version: string;
  definition: string;
  effective_from: string;
  effective_to?: string;
  created_at: string;
}

export interface Concept {
  id: string;
  concept_key: string;
  created_at: string;
  versions: ConceptVersion[];
}

export interface Finding {
  id: string;
  detector: string;
  severity: string;
  target?: string;
  payload: Record<string, unknown>;
  created_at: string;
}

export interface ActionCard {
  id: string;
  action_type: string;
  priority: number;
  title: string;
  steps: string[];
  status: string;
}

export interface DetectorRun {
  id: string;
  project_id: string;
  started_at: string;
  finished_at?: string;
  status: string;
  sds_score?: number;
  summary?: {
    breakdown: Record<string, number>;
    findings_count: number;
  };
  findings?: Finding[];
  action_cards?: ActionCard[];
}

export interface GraphNode {
  id: string;
  type: string;
  label: string;
  metadata?: Record<string, unknown>;
}

export interface GraphEdge {
  source: string;
  target: string;
  type: string;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export const api = {
  getProjects: async (): Promise<Project[]> => {
    const res = await fetch(`${API_URL}/projects`, { headers });
    return res.json();
  },

  createProject: async (name: string, domain: string): Promise<Project> => {
    const res = await fetch(`${API_URL}/projects`, {
      method: "POST",
      headers,
      body: JSON.stringify({ name, domain }),
    });
    return res.json();
  },

  getProject: async (id: string): Promise<Project> => {
    const res = await fetch(`${API_URL}/projects/${id}`, { headers });
    return res.json();
  },

  deleteProject: async (id: string): Promise<void> => {
    await fetch(`${API_URL}/projects/${id}`, {
      method: "DELETE",
      headers,
    });
  },

  getConcepts: async (projectId: string): Promise<Concept[]> => {
    const res = await fetch(`${API_URL}/projects/${projectId}/concepts`, {
      headers,
    });
    return res.json();
  },

  createConcept: async (
    projectId: string,
    data: {
      concept_key: string;
      version: string;
      definition: string;
      effective_from: string;
    },
  ): Promise<Concept> => {
    const res = await fetch(`${API_URL}/projects/${projectId}/concepts`, {
      method: "POST",
      headers,
      body: JSON.stringify(data),
    });
    return res.json();
  },

  runAudit: async (
    projectId: string,
    detectors: string[],
    asOf?: string,
    sync = true,
  ): Promise<Record<string, unknown>> => {
    const res = await fetch(
      `${API_URL}/projects/${projectId}/audits/run?sync=${sync}`,
      {
        method: "POST",
        headers,
        body: JSON.stringify({
          as_of: asOf || null,
          detectors,
        }),
      },
    );
    return res.json();
  },

  getLatestAudit: async (projectId: string): Promise<DetectorRun | null> => {
    const res = await fetch(`${API_URL}/projects/${projectId}/audits/latest`, {
      headers,
    });
    if (res.status === 404) return null;
    const data = await res.json();
    return data;
  },

  getAuditById: async (
    projectId: string,
    runId: string,
  ): Promise<DetectorRun> => {
    const res = await fetch(
      `${API_URL}/projects/${projectId}/audits/${runId}`,
      { headers },
    );
    return res.json();
  },

  getFindings: async (
    projectId: string,
    severity?: string,
  ): Promise<Finding[]> => {
    const url = severity
      ? `${API_URL}/projects/${projectId}/findings?severity=${severity}`
      : `${API_URL}/projects/${projectId}/findings`;
    const res = await fetch(url, { headers });
    return res.json();
  },

  getActions: async (
    projectId: string,
    status?: string,
  ): Promise<ActionCard[]> => {
    const url = status
      ? `${API_URL}/projects/${projectId}/actions?status=${status}`
      : `${API_URL}/projects/${projectId}/actions`;
    const res = await fetch(url, { headers });
    return res.json();
  },

  updateActionStatus: async (
    projectId: string,
    actionId: string,
    status: string,
  ): Promise<ActionCard> => {
    const res = await fetch(
      `${API_URL}/projects/${projectId}/actions/${actionId}`,
      {
        method: "PATCH",
        headers,
        body: JSON.stringify({ status }),
      },
    );
    return res.json();
  },

  getLatestLineage: async (projectId: string): Promise<GraphData> => {
    const res = await fetch(`${API_URL}/projects/${projectId}/lineage/latest`, {
      headers,
    });
    if (!res.ok) throw new Error("Lineage not found");
    return res.json();
  },

  getWeeklyReportMarkdown: async (projectId: string): Promise<string> => {
    const res = await fetch(`${API_URL}/projects/${projectId}/reports/weekly`, {
      headers,
    });
    return res.text();
  },

  getWeeklyReportPdfUrl: async (projectId: string): Promise<string> => {
    const res = await fetch(
      `${API_URL}/projects/${projectId}/reports/weekly.pdf`,
      { headers },
    );
    if (!res.ok) throw new Error("Failed to fetch PDF report");
    const blob = await res.blob();
    return URL.createObjectURL(blob);
  },

  ingestData: async (
    projectId: string,
    type: string,
    payload: Record<string, unknown>[],
  ): Promise<Record<string, unknown>> => {
    const res = await fetch(`${API_URL}/projects/${projectId}/ingest/${type}`, {
      method: "POST",
      headers,
      body: JSON.stringify(payload),
    });
    return res.json();
  },
};
