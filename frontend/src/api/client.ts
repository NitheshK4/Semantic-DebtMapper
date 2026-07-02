const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8005/api/v1";
const API_KEY = import.meta.env.VITE_API_KEY;

if (!API_KEY) {
  console.error("VITE_API_KEY is not set in the environment.");
}

const baseHeaders: Record<string, string> = {
  "Content-Type": "application/json",
  "X-API-Key": API_KEY,
};

let authToken: string | null = localStorage.getItem("sdm_token");

const getHeaders = () => {
  const headers = { ...baseHeaders };
  if (authToken) {
    headers["Authorization"] = `Bearer ${authToken}`;
  }
  return headers;
};

export interface User {
  id: string;
  email: string;
  role: string;
}

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
  notes?: string;
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
  setToken: (token: string | null) => {
    authToken = token;
  },

  login: async (email: string, password: string): Promise<{ access_token: string }> => {
    const formData = new URLSearchParams();
    formData.append("username", email);
    formData.append("password", password);
    const res = await fetch(`${API_URL}/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
        "X-API-Key": API_KEY,
      },
      body: formData,
    });
    if (!res.ok) throw new Error("Login failed");
    return res.json();
  },

  register: async (email: string, password: string): Promise<User> => {
    const res = await fetch(`${API_URL}/register`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify({ email, password }),
    });
    if (!res.ok) throw new Error("Registration failed");
    return res.json();
  },

  getCurrentUser: async (): Promise<User> => {
    const res = await fetch(`${API_URL}/users/me`, { headers: getHeaders() });
    if (!res.ok) throw new Error("Failed to fetch user");
    return res.json();
  },

  getProjects: async (): Promise<Project[]> => {
    const res = await fetch(`${API_URL}/projects`, { headers: getHeaders() });
    return res.json();
  },

  createProject: async (name: string, domain: string): Promise<Project> => {
    const res = await fetch(`${API_URL}/projects`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify({ name, domain }),
    });
    return res.json();
  },

  getProject: async (id: string): Promise<Project> => {
    const res = await fetch(`${API_URL}/projects/${id}`, { headers: getHeaders() });
    return res.json();
  },

  deleteProject: async (id: string): Promise<void> => {
    await fetch(`${API_URL}/projects/${id}`, {
      method: "DELETE",
      headers: getHeaders(),
    });
  },

  getConcepts: async (projectId: string): Promise<Concept[]> => {
    const res = await fetch(`${API_URL}/projects/${projectId}/concepts`, {
      headers: getHeaders(),
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
      headers: getHeaders(),
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
        headers: getHeaders(),
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
      headers: getHeaders(),
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
      { headers: getHeaders() },
    );
    return res.json();
  },

  getFindings: async (
    projectId: string,
    severity?: string,
    detector?: string,
    limit?: number,
    offset?: number,
  ): Promise<Finding[]> => {
    const params = new URLSearchParams();
    if (severity && severity !== "all") params.append("severity", severity);
    if (detector && detector !== "all") params.append("detector", detector);
    if (limit !== undefined) params.append("limit", String(limit));
    if (offset !== undefined) params.append("offset", String(offset));
    
    const queryString = params.toString();
    const url = queryString 
      ? `${API_URL}/projects/${projectId}/findings?${queryString}`
      : `${API_URL}/projects/${projectId}/findings`;
    const res = await fetch(url, { headers: getHeaders() });
    return res.json();
  },

  getActions: async (
    projectId: string,
    status?: string,
    limit?: number,
    offset?: number,
  ): Promise<ActionCard[]> => {
    const params = new URLSearchParams();
    if (status && status !== "all") params.append("status", status);
    if (limit !== undefined) params.append("limit", String(limit));
    if (offset !== undefined) params.append("offset", String(offset));
    
    const queryString = params.toString();
    const url = queryString
      ? `${API_URL}/projects/${projectId}/actions?${queryString}`
      : `${API_URL}/projects/${projectId}/actions`;
    const res = await fetch(url, { headers: getHeaders() });
    return res.json();
  },

  exportFindings: async (projectId: string): Promise<Record<string, unknown>> => {
    const res = await fetch(`${API_URL}/projects/${projectId}/findings/export`, {
      headers: getHeaders(),
    });
    if (!res.ok) throw new Error("Failed to export findings");
    return res.json();
  },

  updateActionStatus: async (
    projectId: string,
    actionId: string,
    status: string,
    notes?: string,
  ): Promise<ActionCard> => {
    const res = await fetch(
      `${API_URL}/projects/${projectId}/actions/${actionId}`,
      {
        method: "PATCH",
        headers: getHeaders(),
        body: JSON.stringify({ status, notes }),
      },
    );
    return res.json();
  },

  getLatestLineage: async (projectId: string): Promise<GraphData> => {
    const res = await fetch(`${API_URL}/projects/${projectId}/lineage/latest`, {
      headers: getHeaders(),
    });
    if (!res.ok) throw new Error("Lineage not found");
    return res.json();
  },

  getWeeklyReportMarkdown: async (projectId: string): Promise<string> => {
    const res = await fetch(`${API_URL}/projects/${projectId}/reports/weekly`, {
      headers: getHeaders(),
    });
    return res.text();
  },

  getWeeklyReportPdfUrl: async (projectId: string): Promise<string> => {
    const res = await fetch(
      `${API_URL}/projects/${projectId}/reports/weekly.pdf`,
      { headers: getHeaders() },
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
      headers: getHeaders(),
      body: JSON.stringify(payload),
    });
    return res.json();
  },

  evaluatePrompt: async (
    projectId: string,
    template: string,
    inputs: Record<string, string>,
    mockModel: string,
  ): Promise<{
    rendered_prompt: string;
    mock_response: string;
    warnings: {
      concept: string;
      type: string;
      severity: string;
      message: string;
      recommendation: string;
    }[];
  }> => {
    const res = await fetch(
      `${API_URL}/projects/${projectId}/sandbox/evaluate`,
      {
        method: "POST",
        headers: getHeaders(),
        body: JSON.stringify({
          template,
          inputs,
          mock_model: mockModel,
        }),
      },
    );
    return res.json();
  },

  rewritePrompt: async (
    projectId: string,
    template: string,
  ): Promise<{
    rewritten_template: string;
  }> => {
    const res = await fetch(
      `${API_URL}/projects/${projectId}/sandbox/rewrite`,
      {
        method: "POST",
        headers: getHeaders(),
        body: JSON.stringify({
          template,
        }),
      },
    );
    return res.json();
  },
};

