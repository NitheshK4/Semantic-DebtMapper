import React, { useEffect, useState } from "react";
import { api } from "../api/client";
import { FileText, Download, RefreshCw, HelpCircle } from "lucide-react";

interface ReportsProps {
  projectId: string;
}

const formatInlineText = (text: string): React.ReactNode[] => {
  let parts: React.ReactNode[] = [text];

  // 1. Parse Bold (**text**)
  let newParts: React.ReactNode[] = [];
  for (const part of parts) {
    if (typeof part === "string") {
      const splitBold = part.split(/\*\*([^*]+)\*\*/g);
      for (let i = 0; i < splitBold.length; i++) {
        if (i % 2 === 1) {
          newParts.push(
            <strong key={`b-${i}`} className="font-bold text-white">
              {splitBold[i]}
            </strong>,
          );
        } else {
          newParts.push(splitBold[i]);
        }
      }
    } else {
      newParts.push(part);
    }
  }
  parts = newParts;

  // 2. Parse Inline Code (`code`)
  newParts = [];
  for (const part of parts) {
    if (typeof part === "string") {
      const splitCode = part.split(/`([^`]+)`/g);
      for (let i = 0; i < splitCode.length; i++) {
        if (i % 2 === 1) {
          newParts.push(
            <code
              key={`c-${i}`}
              className="font-mono bg-white/5 border border-white/10 px-1.5 py-0.5 rounded text-indigo-300 text-[11px]"
            >
              {splitCode[i]}
            </code>,
          );
        } else {
          newParts.push(splitCode[i]);
        }
      }
    } else {
      newParts.push(part);
    }
  }
  return newParts;
};

const renderMarkdown = (markdown: string | null): React.ReactNode => {
  if (!markdown) return null;
  const lines = markdown.split("\n");
  const elements: React.ReactNode[] = [];

  let i = 0;
  while (i < lines.length) {
    const line = lines[i];

    // 1. Table Grouping
    if (line.trim().startsWith("|")) {
      const tableRows: string[] = [];
      while (i < lines.length && lines[i].trim().startsWith("|")) {
        tableRows.push(lines[i]);
        i++;
      }

      if (tableRows.length > 0) {
        const parseRow = (rowStr: string) => {
          const parts = rowStr.split("|");
          return parts.slice(1, parts.length - 1).map((p) => p.trim());
        };

        const headers = parseRow(tableRows[0]);
        const bodyRows = tableRows.slice(1).filter((r) => !r.includes("---"));

        elements.push(
          <div key={`table-${i}`} className="overflow-x-auto my-4 border border-white/5 rounded-xl">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="bg-white/5 border-b border-white/5">
                  {headers.map((h, idx) => (
                    <th key={idx} className="p-3 font-bold text-gray-300 uppercase tracking-wider">
                      {formatInlineText(h)}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {bodyRows.map((rowStr, rIdx) => {
                  const cells = parseRow(rowStr);
                  return (
                    <tr key={rIdx} className="hover:bg-white/[0.02] transition-colors">
                      {cells.map((c, cIdx) => (
                        <td key={cIdx} className="p-3 text-gray-400 font-medium">
                          {formatInlineText(c)}
                        </td>
                      ))}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        );
      }
      continue;
    }

    // 2. Unordered/Task Lists Grouping
    if (line.trim().startsWith("- ") || line.trim().startsWith("* ")) {
      const listItems: { text: string; isTask: boolean; isChecked: boolean; isIndented: boolean }[] = [];
      while (
        i < lines.length &&
        (lines[i].trim().startsWith("- ") ||
          lines[i].trim().startsWith("* ") ||
          (lines[i].startsWith(" ") && lines[i].trim().length > 0))
      ) {
        const itemLine = lines[i];
        const trimmed = itemLine.trim();
        const isIndented = itemLine.startsWith(" ");
        let text = trimmed.startsWith("- ") ? trimmed.slice(2) : trimmed.startsWith("* ") ? trimmed.slice(2) : trimmed;

        let isTask = false;
        let isChecked = false;
        if (text.startsWith("[ ] ")) {
          isTask = true;
          isChecked = false;
          text = text.slice(4);
        } else if (text.startsWith("[x] ") || text.startsWith("[X] ")) {
          isTask = true;
          isChecked = true;
          text = text.slice(4);
        }

        listItems.push({ text, isTask, isChecked, isIndented });
        i++;
      }

      elements.push(
        <ul key={`list-${i}`} className="space-y-1.5 my-3 list-none">
          {listItems.map((item, idx) => (
            <li
              key={idx}
              className={`flex items-start text-xs text-gray-400 ${item.isIndented ? "ml-6" : "ml-2"}`}
            >
              {item.isTask ? (
                <input
                  type="checkbox"
                  checked={item.isChecked}
                  readOnly
                  className="mr-2 mt-0.5 rounded border-white/10 bg-white/5 text-indigo-500 focus:ring-0 cursor-default"
                />
              ) : (
                <span className="mr-2 text-indigo-400 font-bold select-none">•</span>
              )}
              <span className="flex-1 leading-relaxed">{formatInlineText(item.text)}</span>
            </li>
          ))}
        </ul>
      );
      continue;
    }

    // 3. Headers
    if (line.startsWith("# ")) {
      elements.push(
        <h1 key={`h1-${i}`} className="text-xl font-bold text-white border-b border-white/5 pb-2 mt-6 mb-4">
          {formatInlineText(line.replace("# ", ""))}
        </h1>
      );
      i++;
      continue;
    }
    if (line.startsWith("## ")) {
      elements.push(
        <h2 key={`h2-${i}`} className="text-base font-bold text-indigo-400 mt-6 mb-3">
          {formatInlineText(line.replace("## ", ""))}
        </h2>
      );
      i++;
      continue;
    }
    if (line.startsWith("### ")) {
      elements.push(
        <h3 key={`h3-${i}`} className="text-sm font-bold text-sky-400 mt-4 mb-2">
          {formatInlineText(line.replace("### ", ""))}
        </h3>
      );
      i++;
      continue;
    }

    // 4. Spacer / Paragraph
    if (line.trim() === "") {
      elements.push(<div key={`space-${i}`} className="h-2" />);
    } else {
      elements.push(
        <p key={`p-${i}`} className="text-xs text-gray-400 leading-relaxed my-2">
          {formatInlineText(line)}
        </p>
      );
    }
    i++;
  }

  return elements;
};

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
            {renderMarkdown(reportMd)}
          </div>
        </div>
      )}
    </div>
  );
};
