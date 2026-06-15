import React, { useEffect, useState } from "react";
import { api } from "../api/client";
import { FileText, Download, RefreshCw, HelpCircle } from "lucide-react";

interface ReportsProps {
  projectId: string;
}

export const Reports: React.FC<ReportsProps> = ({ projectId }) => {
  const [reportMd, setReportMd] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchReport = async () => {
      setLoading(true);
      try {
        const md = await api.getWeeklyReportMarkdown(projectId);
        setReportMd(md);
        setError(null);
      } catch {
        setError("Please run an audit first to generate reports.");
      } finally {
        setLoading(false);
      }
    };
    fetchReport();
  }, [projectId]);

  const handleDownloadMarkdown = () => {
    if (!reportMd) return;
    const element = document.createElement("a");
    const file = new Blob([reportMd], { type: "text/markdown" });
    element.href = URL.createObjectURL(file);
    element.download = `weekly_audit_report_${projectId}.md`;
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  const handleDownloadPdf = async () => {
    try {
      const url = await api.getWeeklyReportPdfUrl(projectId);
      const element = document.createElement("a");
      element.href = url;
      element.download = `weekly_audit_report_${projectId}.pdf`;
      document.body.appendChild(element);
      element.click();
      document.body.removeChild(element);
      URL.revokeObjectURL(url);
    } catch {
      setError("Failed to download PDF report.");
    }
  };

  return (
    <div className="glass-panel p-6 rounded-2xl animate-fade-in space-y-6">
      {/* Header and Download Buttons */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-gray-800 pb-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center">
            <FileText className="w-5 h-5 text-indigo-400 mr-2" /> Meaning Audit
            Reports
          </h2>
          <p className="text-xs text-gray-400 mt-1">
            Export executive meaning audit reports summarizing pipeline
            integrity and recommendations
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => {
              setLoading(true);
              api
                .getWeeklyReportMarkdown(projectId)
                .then((md) => {
                  setReportMd(md);
                  setError(null);
                })
                .catch(() =>
                  setError("Please run an audit first to generate reports."),
                )
                .finally(() => setLoading(false));
            }}
            disabled={loading}
            className="p-2 rounded-lg border border-gray-800 hover:border-gray-700 text-gray-400 hover:text-white transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          </button>

          <button
            onClick={handleDownloadMarkdown}
            disabled={loading || !reportMd || reportMd.includes("No audit run")}
            className="bg-gray-800 hover:bg-gray-700 disabled:opacity-40 text-xs font-semibold text-white px-4 py-2 rounded-xl transition-colors flex items-center"
          >
            <Download className="w-3.5 h-3.5 mr-1.5" /> Export MD
          </button>

          <button
            onClick={handleDownloadPdf}
            disabled={loading || !reportMd || reportMd.includes("No audit run")}
            className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-xs font-bold text-white px-4 py-2 rounded-xl transition-colors flex items-center"
          >
            <Download className="w-3.5 h-3.5 mr-1.5" /> Export PDF
          </button>
        </div>
      </div>

      {/* Report Preview Panel */}
      {loading ? (
        <div className="py-20 text-center text-gray-500 space-y-3">
          <RefreshCw className="w-8 h-8 text-indigo-400 animate-spin mx-auto" />
          <p className="text-sm">Compiling weekly meaning audit report...</p>
        </div>
      ) : error ? (
        <div className="py-20 text-center text-gray-500">
          <HelpCircle className="w-12 h-12 text-gray-600 mx-auto mb-2" />
          <p className="text-sm">{error}</p>
        </div>
      ) : (
        <div className="bg-gray-950/40 border border-gray-800/80 p-8 rounded-xl max-h-[500px] overflow-y-auto font-sans leading-relaxed text-sm text-gray-300">
          {/* Custom rendered preview */}
          <div className="prose prose-invert max-w-none space-y-4">
            {reportMd?.split("\n").map((line, idx) => {
              if (line.startsWith("# ")) {
                return (
                  <h1
                    key={idx}
                    className="text-2xl font-bold text-white border-b border-gray-800 pb-2 mb-4"
                  >
                    {line.replace("# ", "")}
                  </h1>
                );
              }
              if (line.startsWith("## ")) {
                return (
                  <h2
                    key={idx}
                    className="text-lg font-bold text-indigo-400 mt-6 mb-2"
                  >
                    {line.replace("## ", "")}
                  </h2>
                );
              }
              if (line.startsWith("### ")) {
                return (
                  <h3
                    key={idx}
                    className="text-base font-bold text-sky-400 mt-4 mb-1"
                  >
                    {line.replace("### ", "")}
                  </h3>
                );
              }
              if (line.startsWith("- ")) {
                return (
                  <li key={idx} className="ml-4 list-disc text-gray-300 mb-1">
                    {line.replace("- ", "")}
                  </li>
                );
              }
              if (line.startsWith("|")) {
                // Table line, skip header boundaries for preview, render simple layout or table format
                if (line.includes("---")) return null;
                const cols = line
                  .split("|")
                  .map((c) => c.trim())
                  .filter((c) => c !== "");
                const isHeader =
                  idx === 11 || line.toLowerCase().includes("detector"); // Rough check for header
                return (
                  <div
                    key={idx}
                    className={`grid grid-cols-5 gap-2 py-2 px-3 text-xs ${isHeader ? "bg-gray-900 font-bold border-y border-gray-850" : "border-b border-gray-900 hover:bg-white/5"}`}
                  >
                    {cols.map((c, cIdx) => (
                      <div key={cIdx} className="overflow-hidden truncate">
                        {c.replace(/\*\*/g, "")}
                      </div>
                    ))}
                  </div>
                );
              }
              if (line.trim() === "") return <div key={idx} className="h-2" />;
              return (
                <p key={idx} className="text-gray-300 leading-relaxed mb-2">
                  {line}
                </p>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
