import React, { useState } from "react";
import { Finding } from "../api/client";
import { Search, Eye, Filter, CheckCircle, ShieldAlert, ChevronLeft, ChevronRight } from "lucide-react";

interface FindingsExplorerProps {
  findings: Finding[];
}

export const FindingsExplorer: React.FC<FindingsExplorerProps> = ({
  findings,
}) => {
  const [detectorFilter, setDetectorFilter] = useState<string>("all");
  const [severityFilter, setSeverityFilter] = useState<string>("all");
  const [searchTerm, setSearchTerm] = useState<string>("");
  const [selectedFinding, setSelectedFinding] = useState<Finding | null>(null);
  
  // Pagination state
  const [page, setPage] = useState<number>(1);
  const itemsPerPage = 5;

  const detectors = ["all", "CMD", "ESF", "RMC", "HMD", "GFM"];
  const severities = ["all", "critical", "high", "medium", "low"];

  const handleSearchChange = (val: string) => {
    setSearchTerm(val);
    setPage(1);
  };

  const handleDetectorChange = (val: string) => {
    setDetectorFilter(val);
    setPage(1);
  };

  const handleSeverityChange = (val: string) => {
    setSeverityFilter(val);
    setPage(1);
  };

  // Filter logic
  const filteredFindings = findings.filter((f) => {
    const matchesDetector =
      detectorFilter === "all" || f.detector === detectorFilter;
    const matchesSeverity =
      severityFilter === "all" || f.severity === severityFilter;
    const matchesSearch =
      searchTerm === "" ||
      (f.target && f.target.toLowerCase().includes(searchTerm.toLowerCase())) ||
      JSON.stringify(f.payload)
        .toLowerCase()
        .includes(searchTerm.toLowerCase());

    return matchesDetector && matchesSeverity && matchesSearch;
  });

  const totalPages = Math.ceil(filteredFindings.length / itemsPerPage);
  const startIndex = (page - 1) * itemsPerPage;
  const paginatedFindings = filteredFindings.slice(startIndex, startIndex + itemsPerPage);

  return (
    <div className="space-y-6 animate-fade-in relative">
      {/* Header and filters */}
      <div className="glass-panel p-6 rounded-2xl space-y-5">
        <div>
          <h2 className="text-base font-bold text-white tracking-tight">
            Semantic Findings Registry
          </h2>
          <p className="text-xs text-gray-500">
            Diagnostic history of meaning drifts, rule conflicts, and segment
            divergence
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3.5 top-2.5 w-3.5 h-3.5 text-gray-500" />
            <input
              type="text"
              placeholder="Search target, segment, or recommendation..."
              value={searchTerm}
              onChange={(e) => handleSearchChange(e.target.value)}
              className="w-full bg-[#0a0d16] border border-white/5 rounded-xl pl-9 pr-4 py-2 text-xs text-white placeholder-gray-600 focus:outline-none focus:border-indigo-500/50 transition-colors"
            />
          </div>

          {/* Detector Filter */}
          <div className="flex items-center space-x-2 bg-[#0a0d16] border border-white/5 rounded-xl px-3 py-1.5">
            <Filter className="w-3.5 h-3.5 text-gray-500" />
            <select
              value={detectorFilter}
              onChange={(e) => handleDetectorChange(e.target.value)}
              className="bg-transparent text-xs text-gray-400 w-full focus:outline-none capitalize font-semibold"
            >
              {detectors.map((d) => (
                <option
                  key={d}
                  value={d}
                  className="bg-[#0c0f18] text-gray-300"
                >
                  {d === "all" ? "All Detectors" : `Engine: ${d}`}
                </option>
              ))}
            </select>
          </div>

          {/* Severity Filter */}
          <div className="flex items-center space-x-2 bg-[#0a0d16] border border-white/5 rounded-xl px-3 py-1.5">
            <ShieldAlert className="w-3.5 h-3.5 text-gray-500" />
            <select
              value={severityFilter}
              onChange={(e) => handleSeverityChange(e.target.value)}
              className="bg-transparent text-xs text-gray-400 w-full focus:outline-none capitalize font-semibold"
            >
              {severities.map((s) => (
                <option
                  key={s}
                  value={s}
                  className="bg-[#0c0f18] text-gray-300"
                >
                  {s === "all" ? "All Severities" : `Severity: ${s}`}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Main Content Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* List of findings */}
        <div className="lg:col-span-2 space-y-3.5 max-h-[620px] overflow-y-auto pr-1 flex flex-col justify-between">
          <div className="space-y-3.5">
            {paginatedFindings.map((f) => (
              <div
                key={f.id}
                onClick={() => setSelectedFinding(f)}
                className={`glass-panel p-5 rounded-2xl cursor-pointer transition-all border ${
                  selectedFinding?.id === f.id
                    ? "border-indigo-500/40 bg-[#0d1222]/80 shadow-[0_0_20px_rgba(99,102,241,0.04)]"
                    : "border-white/5 hover:border-white/10 hover:bg-white/[0.01]"
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="space-y-1">
                    <span className="text-[9px] font-bold uppercase tracking-wider text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded border border-indigo-500/20">
                      {f.detector}
                    </span>
                    <h3 className="text-sm font-bold text-white mt-1.5 tracking-tight">
                      Drift in: {f.target || "Global Pipeline"}
                    </h3>
                  </div>
                  <span
                    className={`px-2 py-0.5 rounded-md text-[9px] font-bold uppercase tracking-wide border ${
                      f.severity === "critical"
                        ? "bg-rose-500/10 text-rose-400 border-rose-500/20"
                        : f.severity === "high"
                          ? "bg-orange-500/10 text-orange-400 border-orange-500/20"
                          : f.severity === "medium"
                            ? "bg-yellow-500/10 text-yellow-400 border-yellow-500/20"
                            : "bg-blue-500/10 text-blue-400 border-blue-500/20"
                    }`}
                  >
                    {f.severity}
                  </span>
                </div>
                <p className="text-xs text-gray-400 mt-2.5 leading-relaxed">
                  {f.payload?.recommendation as string}
                </p>

                <div className="mt-4 flex items-center justify-between text-[10px] text-gray-500 font-medium">
                  <span>
                    Detected: {new Date(f.created_at).toLocaleDateString()}
                  </span>
                  <span className="flex items-center text-indigo-400 font-bold uppercase tracking-wider">
                    Inspect diagnostic data
                    <Eye className="w-3.5 h-3.5 ml-1" />
                  </span>
                </div>
              </div>
            ))}
          </div>

          {/* Pagination Controls */}
          {filteredFindings.length > 0 && (
            <div className="flex items-center justify-between pt-4 pb-2 px-1 text-[11px] text-gray-500 border-t border-white/5 mt-4">
              <span>
                Showing {startIndex + 1} to {Math.min(startIndex + itemsPerPage, filteredFindings.length)} of {filteredFindings.length} findings
              </span>
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setPage((p) => Math.max(p - 1, 1))}
                  disabled={page === 1}
                  className="p-1.5 rounded-lg border border-white/5 bg-[#0a0d16] text-gray-400 hover:text-white disabled:opacity-40 disabled:hover:text-gray-400 transition-colors"
                >
                  <ChevronLeft className="w-3.5 h-3.5" />
                </button>
                <span className="font-bold text-white">
                  Page {page} of {totalPages || 1}
                </span>
                <button
                  onClick={() => setPage((p) => Math.min(p + 1, totalPages))}
                  disabled={page === totalPages || totalPages === 0}
                  className="p-1.5 rounded-lg border border-white/5 bg-[#0a0d16] text-gray-400 hover:text-white disabled:opacity-40 disabled:hover:text-gray-400 transition-colors"
                >
                  <ChevronRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          )}

          {filteredFindings.length === 0 && (
            <div className="glass-panel p-12 rounded-2xl text-center text-gray-500">
              <CheckCircle className="w-8 h-8 text-emerald-500/30 mx-auto mb-2" />
              <p className="text-xs font-semibold text-gray-400">
                No findings match the active filters.
              </p>
            </div>
          )}
        </div>

        {/* Detailed Pane */}
        <div className="glass-panel p-5 rounded-2xl h-fit border border-white/5 space-y-4">
          {selectedFinding ? (
            <div className="space-y-4">
              <div>
                <span className="text-[9px] font-bold text-gray-500 uppercase tracking-widest block">
                  Diagnostic Metrics
                </span>
                <h3 className="text-sm font-bold text-white mt-1 tracking-tight flex items-center space-x-2">
                  <span className="text-indigo-400">
                    [{selectedFinding.detector}]
                  </span>
                  <span>{selectedFinding.target || "Global"}</span>
                </h3>
              </div>

              <hr className="border-white/5" />

              <div className="space-y-3.5">
                <div className="flex items-center justify-between text-xs py-0.5 border-b border-white/[0.02]">
                  <span className="text-gray-500 font-medium">Engine:</span>
                  <span className="text-white font-bold">
                    {selectedFinding.detector}
                  </span>
                </div>
                <div className="flex items-center justify-between text-xs py-0.5 border-b border-white/[0.02]">
                  <span className="text-gray-500 font-medium">Severity:</span>
                  <span className="text-white font-bold capitalize">
                    {selectedFinding.severity}
                  </span>
                </div>

                {/* Structured Metadata Fields */}
                <div className="space-y-2.5 pt-1">
                  <span className="text-[9px] font-bold text-gray-500 uppercase tracking-widest block">
                    Payload Telemetry
                  </span>
                  {selectedFinding.payload &&
                    Object.entries(selectedFinding.payload).map(([k, v]) => {
                      if (k === "recommendation") return null;

                      // Render dictionary properties like segments elegantly
                      if (typeof v === "object" && v !== null) {
                        return (
                          <div className="text-xs space-y-1" key={k}>
                            <span className="text-gray-500 block font-medium capitalize">
                              {k.replace(/_/g, " ")}:
                            </span>
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
                          </div>
                        );
                      }

                      return (
                        <div
                          className="flex items-center justify-between text-xs py-1 border-b border-white/[0.01]"
                          key={k}
                        >
                          <span className="text-gray-500 font-medium capitalize">
                            {k.replace(/_/g, " ")}:
                          </span>
                          <span className="text-indigo-300 font-bold font-mono">
                            {String(v)}
                          </span>
                        </div>
                      );
                    })}
                </div>
              </div>

              <div className="bg-indigo-500/5 border border-indigo-500/10 p-4 rounded-xl text-xs">
                <span className="text-[9px] font-bold text-indigo-400 uppercase tracking-wider block mb-1">
                  Remediation Guide
                </span>
                <div className="text-gray-300 leading-relaxed font-medium">
                  {selectedFinding.payload?.recommendation as string}
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center py-16 text-gray-500 space-y-2">
              <Eye className="w-10 h-10 text-gray-700 mx-auto" />
              <p className="text-xs font-semibold text-gray-400">
                Select an issue card
              </p>
              <p className="text-[11px] text-gray-500 leading-relaxed px-4">
                Pick a drift indicator on the left to inspect semantic vectors,
                override curves, or target rules.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
