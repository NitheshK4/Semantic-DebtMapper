import { useState, useEffect } from "react";
import { api, Project, DetectorRun, Finding, ActionCard } from "./api/client";
import { Overview } from "./pages/Overview";
import { FindingsExplorer } from "./pages/FindingsExplorer";
import { LineageGraph } from "./pages/LineageGraph";
import { ActionCenter } from "./pages/ActionCenter";
import { IngestionCenter } from "./pages/IngestionCenter";
import { Reports } from "./pages/Reports";
import {
  BarChart3,
  ShieldAlert,
  Layers,
  CheckSquare,
  Database,
  FileText,
  RefreshCw,
} from "lucide-react";

function App() {
  const [currentPage, setCurrentPage] = useState<string>("overview");
  const [project, setProject] = useState<Project | null>(null);
  const [latestRun, setLatestRun] = useState<DetectorRun | null>(null);
  const [findings, setFindings] = useState<Finding[]>([]);
  const [actions, setActions] = useState<ActionCard[]>([]);

  const [initializing, setInitializing] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);

  const loadRunData = async (projectId: string) => {
    setRefreshing(true);
    try {
      const run = await api.getLatestAudit(projectId);
      setLatestRun(run);
      if (run) {
        const f = await api.getFindings(projectId);
        const a = await api.getActions(projectId);
        setFindings(f);
        setActions(a);
      }
    } catch (e) {
      console.error("Failed to load run data:", e);
    } finally {
      setRefreshing(false);
    }
  };

  useEffect(() => {
    const initialize = async () => {
      try {
        const projects = await api.getProjects();
        let demoProj = projects.find(
          (p) => p.name === "Support Ticket Classifier",
        );

        if (!demoProj) {
          demoProj = await api.createProject(
            "Support Ticket Classifier",
            "support_tickets",
          );
        }

        setProject(demoProj);
        await loadRunData(demoProj.id);
      } catch (e) {
        console.error("Failed to initialize project:", e);
      } finally {
        setInitializing(false);
      }
    };
    initialize();
  }, []);

  const handleUpdateActionStatus = async (actionId: string, status: string) => {
    if (!project) return;
    try {
      await api.updateActionStatus(project.id, actionId, status);
      // Refresh actions list
      const a = await api.getActions(project.id);
      setActions(a);
    } catch (e) {
      console.error("Failed to update status:", e);
    }
  };

  if (initializing) {
    return (
      <div className="h-screen w-screen flex flex-col items-center justify-center bg-[#0b0f19] space-y-4">
        <RefreshCw className="w-10 h-10 text-indigo-500 animate-spin" />
        <p className="text-sm text-gray-400 font-semibold tracking-wider uppercase">
          Loading Semantic Debt Workspace...
        </p>
      </div>
    );
  }

  const navItems = [
    { id: "overview", label: "Overview", icon: BarChart3 },
    { id: "findings", label: "Findings Explorer", icon: ShieldAlert },
    { id: "lineage", label: "Lineage Graph", icon: Layers },
    { id: "actions", label: "Action Center", icon: CheckSquare },
    { id: "ingestion", label: "Ingestion Center", icon: Database },
    { id: "reports", label: "Audit Reports", icon: FileText },
  ];

  return (
    <div className="flex min-h-screen">
      {/* Sidebar Navigation */}
      <aside className="w-64 glass-panel border-r border-white/5 flex flex-col justify-between p-6 shrink-0 z-10">
        <div className="space-y-8">
          {/* Minimalist App Header */}
          <div className="flex flex-col space-y-1">
            <div className="flex items-center space-x-2">
              <span className="w-1.5 h-1.5 rounded-full bg-indigo-500 shadow-[0_0_8px_rgba(99,102,241,0.8)]"></span>
              <span className="font-bold text-white text-sm tracking-wider uppercase">
                Debt Mapper
              </span>
            </div>
            <span className="text-[9px] text-gray-500 font-bold tracking-widest uppercase pl-3.5">
              AI Semantics Engine
            </span>
          </div>

          {/* Nav Links */}
          <nav className="space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = currentPage === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setCurrentPage(item.id)}
                  className={`w-full flex items-center space-x-3 px-3.5 py-2.5 rounded-xl text-xs font-bold uppercase tracking-wider transition-all duration-150 ${
                    isActive
                      ? "bg-indigo-600/10 border border-indigo-500/20 text-indigo-400"
                      : "border border-transparent text-gray-400 hover:bg-white/[0.02] hover:text-white"
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </nav>
        </div>

        {/* Workspace details footer */}
        {project && (
          <div className="border-t border-white/5 pt-4 mt-6">
            <div className="flex items-center justify-between text-[9px] font-bold text-gray-500 tracking-wider uppercase mb-1">
              <span>Target Pipeline</span>
              {refreshing && (
                <RefreshCw className="w-3 h-3 animate-spin text-indigo-500" />
              )}
            </div>
            <div className="text-xs font-bold text-white truncate">
              {project.name}
            </div>
            <div className="text-[10px] text-indigo-400/80 font-medium capitalize mt-0.5">
              {project.domain.replace("_", " ")}
            </div>
          </div>
        )}
      </aside>

      {/* Main Panel Content Area */}
      <main className="flex-1 p-8 overflow-y-auto max-h-screen">
        {/* Render Active View */}
        {currentPage === "overview" && (
          <Overview
            run={latestRun}
            findings={findings}
            onNavigate={(page) => setCurrentPage(page)}
          />
        )}
        {currentPage === "findings" && <FindingsExplorer findings={findings} />}
        {currentPage === "lineage" && project && (
          <LineageGraph projectId={project.id} />
        )}
        {currentPage === "actions" && (
          <ActionCenter
            actions={actions}
            onUpdateStatus={handleUpdateActionStatus}
          />
        )}
        {currentPage === "ingestion" && project && (
          <IngestionCenter
            projectId={project.id}
            onAuditComplete={() => loadRunData(project.id)}
          />
        )}
        {currentPage === "reports" && project && (
          <Reports projectId={project.id} />
        )}
      </main>
    </div>
  );
}

export default App;
