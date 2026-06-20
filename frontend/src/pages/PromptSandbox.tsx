import React, { useState, useEffect } from "react";
import { api } from "../api/client";
import {
  Sparkles,
  ShieldAlert,
  AlertTriangle,
  Play,
  RefreshCw,
  FileCode,
  HelpCircle,
  Variable,
  CheckCircle,
} from "lucide-react";

interface PromptSandboxProps {
  projectId: string;
}

interface Warning {
  concept: string;
  type: string;
  severity: string;
  message: string;
  recommendation: string;
}

interface PreloadedTemplate {
  name: string;
  description: string;
  template: string;
  inputs: Record<string, string>;
  mockModel: string;
}

const PRELOADED_TEMPLATES: PreloadedTemplate[] = [
  {
    name: "Urgency Classification (Triggers Metric Conflict)",
    description: "Contains an explicit 2-hour SLA instructions which conflicts with the active 4-hour SLA concept definition in the registry.",
    template: `You are a customer support triage AI. Classify the customer request as low, medium, urgent, or critical.

If a ticket mentions billing, payment failures, or VIP tier, classify it as urgent.
Note that the response SLA for urgent is 2 hours.

Ticket context:
{{ticket_text}}`,
    inputs: {
      ticket_text: "My credit card payment failed twice and I cannot access my dashboard. Please assist as my service is suspended.",
    },
    mockModel: "gemini-2.5-pro",
  },
  {
    name: "Support Routing (Triggers Legacy Term Mismatch)",
    description: "Uses the legacy term 'two hours' and outdated 'SLA policy v2' which represents obsolete definitions in the concept registry.",
    template: `Analyze this user inquiry:
{{ticket_text}}

If the issue is urgent, classify as urgent and follow SLA policy v2 guidelines. Ticket response requires resolution within two hours.`,
    inputs: {
      ticket_text: "Urgent: We have a critical outage on the login server, no user can log in.",
    },
    mockModel: "gemini-2.5-flash",
  },
  {
    name: "Standard Classifier (Clean / No Semantic Debt)",
    description: "Aligned with current business concepts and active SLA policy definitions.",
    template: `You are an AI support assistant.
Classify the following ticket into low, medium, urgent, or critical:
{{ticket_text}}

Urgent rules:
- Urgent tickets require a response within 4 hours per SLA policy v3.
- Includes VIP escalations and payment failures.`,
    inputs: {
      ticket_text: "URGENT: I need to update my billing address before the invoice is sent tomorrow.",
    },
    mockModel: "gemini-2.5-pro",
  },
];

export const PromptSandbox: React.FC<PromptSandboxProps> = ({ projectId }) => {
  const [template, setTemplate] = useState<string>(PRELOADED_TEMPLATES[0].template);
  const [inputs, setInputs] = useState<Record<string, string>>(PRELOADED_TEMPLATES[0].inputs);
  const [mockModel, setMockModel] = useState<string>(PRELOADED_TEMPLATES[0].mockModel);
  const [detectedVars, setDetectedVars] = useState<string[]>([]);

  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  
  // Results
  const [evaluated, setEvaluated] = useState<boolean>(false);
  const [renderedPrompt, setRenderedPrompt] = useState<string>("");
  const [mockResponse, setMockResponse] = useState<string>("");
  const [warnings, setWarnings] = useState<Warning[]>([]);

  // Parse variables from template
  useEffect(() => {
    const doubleBraceRegex = /\{\{\s*([a-zA-Z0-9_-]+)\s*\}\}/g;
    const singleBraceRegex = /\{([a-zA-Z0-9_-]+)\}/g;
    const vars = new Set<string>();

    let match;
    while ((match = doubleBraceRegex.exec(template)) !== null) {
      vars.add(match[1]);
    }
    
    // Fallback or secondary search for {var} format
    while ((match = singleBraceRegex.exec(template)) !== null) {
      // Avoid capturing double-braces as single ones
      const matchedStr = match[0];
      const precedingChar = template[match.index - 1];
      const succeedingChar = template[match.index + matchedStr.length];
      if (precedingChar === "{" || succeedingChar === "}") {
        continue;
      }
      vars.add(match[1]);
    }

    const varList = Array.from(vars);
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setDetectedVars(varList);

    // Synchronize inputs state: retain existing values, add empty for new keys
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setInputs((prev) => {
      const next: Record<string, string> = {};
      varList.forEach((v) => {
        next[v] = prev[v] !== undefined ? prev[v] : "";
      });
      return next;
    });
  }, [template]);

  const handleLoadTemplate = (t: PreloadedTemplate) => {
    setTemplate(t.template);
    setInputs(t.inputs);
    setMockModel(t.mockModel);
    setError(null);
    setEvaluated(false);
  };

  const handleInputChange = (key: string, val: string) => {
    setInputs((prev) => ({
      ...prev,
      [key]: val,
    }));
  };

  const handleEvaluate = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.evaluatePrompt(projectId, template, inputs, mockModel);
      setRenderedPrompt(res.rendered_prompt);
      setMockResponse(res.mock_response);
      setWarnings(res.warnings || []);
      setEvaluated(true);
    } catch (err) {
      console.error(err);
      setError("Evaluation failed. Please verify that the backend server is running and the database is seeded.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8 animate-fade-in pb-12">
      {/* Page Header */}
      <div>
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-indigo-500/10 rounded-xl border border-indigo-500/20 text-indigo-400">
            <Sparkles className="w-6 h-6 animate-pulse" />
          </div>
          <div>
            <h1 className="text-xl font-extrabold text-white uppercase tracking-wider">
              Prompt Sandbox & Evaluation Center
            </h1>
            <p className="text-xs text-gray-400 mt-0.5">
              Draft, render, and evaluate LLM prompt templates while scanning for Semantic Debt warnings and concept drifts in real time.
            </p>
          </div>
        </div>
      </div>

      {/* Preloaded Template Quick Selector */}
      <div className="glass-panel p-5 rounded-2xl border border-white/5 space-y-3">
        <h3 className="text-xs font-bold text-gray-400 uppercase tracking-widest flex items-center">
          <FileCode className="w-4 h-4 text-indigo-400 mr-2" /> Preloaded Configurations
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {PRELOADED_TEMPLATES.map((t, idx) => (
            <button
              key={idx}
              onClick={() => handleLoadTemplate(t)}
              className="glass-card hover:bg-white/[0.03] transition-all p-4 rounded-xl border border-white/5 text-left flex flex-col justify-between space-y-2 group"
            >
              <div className="space-y-1">
                <div className="text-xs font-bold text-indigo-400 group-hover:text-indigo-300">
                  {t.name}
                </div>
                <div className="text-[10px] text-gray-400 leading-relaxed">
                  {t.description}
                </div>
              </div>
              <span className="text-[9px] font-bold text-indigo-500/80 group-hover:text-indigo-400 uppercase tracking-wider self-end mt-2 flex items-center">
                Load Config &rarr;
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* Workspace Sandbox Split Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* Editor Inputs Panel */}
        <div className="lg:col-span-7 space-y-6">
          <div className="glass-panel p-6 rounded-2xl border border-white/5 space-y-6">
            
            {/* Prompt Template Textarea */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <label className="text-xs font-bold text-gray-400 uppercase tracking-wider">
                  Prompt Template
                </label>
                <div className="text-[10px] text-indigo-400 font-medium">
                  Supports double-brace variables <span className="font-mono bg-indigo-500/10 px-1 py-0.5 rounded">{"{{variable}}"}</span>
                </div>
              </div>
              <textarea
                value={template}
                onChange={(e) => setTemplate(e.target.value)}
                placeholder="Write your prompt template here..."
                rows={12}
                className="w-full bg-[#050811]/90 border border-white/5 rounded-xl p-4 text-xs font-mono text-gray-300 focus:outline-none focus:border-indigo-500/50 focus:ring-1 focus:ring-indigo-500/20 leading-relaxed shadow-inner"
              />
            </div>

            {/* Template Variables Section */}
            <div className="space-y-3">
              <div className="flex items-center space-x-2 border-b border-white/5 pb-2">
                <Variable className="w-4 h-4 text-indigo-400" />
                <span className="text-xs font-bold text-white uppercase tracking-wider">
                  Template Variables ({detectedVars.length})
                </span>
              </div>

              {detectedVars.length === 0 ? (
                <div className="text-[11px] text-gray-500 italic p-3 bg-white/[0.01] rounded-xl border border-white/[0.02] flex items-center">
                  <HelpCircle className="w-3.5 h-3.5 mr-2 text-gray-600" />
                  No variables found. Add double-brace identifiers like{" "}
                  <code className="mx-1 px-1 bg-white/5 rounded">{"{{ticket_text}}"}</code> to map custom inputs.
                </div>
              ) : (
                <div className="space-y-4">
                  {detectedVars.map((v) => (
                    <div key={v} className="space-y-1">
                      <label className="text-[10px] font-bold text-indigo-400/90 font-mono tracking-wider">
                        {v.toUpperCase()}
                      </label>
                      <textarea
                        value={inputs[v] || ""}
                        onChange={(e) => handleInputChange(v, e.target.value)}
                        placeholder={`Enter value for ${v}...`}
                        rows={3}
                        className="w-full bg-[#050811]/90 border border-white/5 rounded-xl px-3 py-2 text-xs text-gray-300 focus:outline-none focus:border-indigo-500/50"
                      />
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Model Selector & Action */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pt-4 border-t border-white/5">
              <div className="flex items-center space-x-3">
                <label className="text-xs font-bold text-gray-400 uppercase tracking-wider shrink-0">
                  Target Model:
                </label>
                <select
                  value={mockModel}
                  onChange={(e) => setMockModel(e.target.value)}
                  className="bg-[#050811]/90 border border-white/5 rounded-xl px-3 py-2 text-xs text-indigo-300 font-bold focus:outline-none focus:border-indigo-500/50 focus:ring-1 focus:ring-indigo-500/30"
                >
                  <option value="gemini-2.5-pro">Gemini 2.5 Pro (Simulated)</option>
                  <option value="gemini-2.5-flash">Gemini 2.5 Flash (Simulated)</option>
                  <option value="claude-3-5-sonnet">Claude 3.5 Sonnet (Simulated)</option>
                  <option value="gpt-4o">GPT-4o (Simulated)</option>
                </select>
              </div>

              <button
                onClick={handleEvaluate}
                disabled={loading}
                className="bg-indigo-600 hover:bg-indigo-500 disabled:bg-indigo-800 disabled:opacity-50 text-xs font-bold text-white px-6 py-2.5 rounded-xl transition-all shadow-[0_0_20px_rgba(99,102,241,0.25)] hover:shadow-[0_0_25px_rgba(99,102,241,0.4)] flex items-center justify-center space-x-2 border border-indigo-500/30 cursor-pointer"
              >
                {loading ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    <span>Analyzing...</span>
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4 fill-white" />
                    <span>Run Simulation</span>
                  </>
                )}
              </button>
            </div>

            {error && (
              <div className="p-3.5 bg-red-950/20 border border-red-500/20 text-red-300 text-xs rounded-xl">
                {error}
              </div>
            )}

          </div>
        </div>

        {/* Results Panel */}
        <div className="lg:col-span-5 space-y-6">
          
          {/* Default State */}
          {!evaluated && !loading && (
            <div className="glass-panel p-8 rounded-2xl border border-white/5 h-full flex flex-col items-center justify-center text-center space-y-4 min-h-[400px]">
              <div className="p-3 bg-indigo-500/5 rounded-full border border-indigo-500/10 text-indigo-400">
                <Sparkles className="w-8 h-8 opacity-40 animate-pulse" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                  Await Simulation Run
                </h3>
                <p className="text-xs text-gray-400 max-w-xs leading-relaxed mt-1">
                  Draft your prompt, insert dynamic variables, and hit <strong className="text-indigo-400 font-semibold">Run Simulation</strong> to compute Semantic Debt findings.
                </p>
              </div>
            </div>
          )}

          {/* Evaluating State Placeholder */}
          {loading && (
            <div className="glass-panel p-8 rounded-2xl border border-white/5 h-full flex flex-col items-center justify-center text-center space-y-4 min-h-[400px]">
              <RefreshCw className="w-8 h-8 text-indigo-500 animate-spin" />
              <div>
                <h3 className="text-sm font-bold text-white uppercase tracking-wider animate-pulse">
                  Analyzing Semantics
                </h3>
                <p className="text-xs text-indigo-300/80 max-w-xs leading-relaxed mt-1">
                  Subbing template values, executing simulation completion, and checking for Concept Registry alignment...
                </p>
              </div>
            </div>
          )}

          {/* Results State */}
          {evaluated && !loading && (
            <div className="space-y-6 animate-fade-in">

              {/* Semantic Analysis Warnings Banner */}
              <div className="glass-panel p-6 rounded-2xl border border-white/5 space-y-4">
                <div className="flex items-center justify-between border-b border-white/5 pb-3">
                  <h3 className="text-xs font-extrabold text-white uppercase tracking-widest flex items-center">
                    <ShieldAlert className="w-4 h-4 text-orange-400 mr-2" /> Semantic Audit Results
                  </h3>
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider ${
                    warnings.length > 0
                      ? "bg-red-500/10 text-red-400 border border-red-500/20"
                      : "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                  }`}>
                    {warnings.length} {warnings.length === 1 ? "Warning" : "Warnings"}
                  </span>
                </div>

                {warnings.length === 0 ? (
                  <div className="p-4 bg-emerald-950/10 border border-emerald-500/20 text-emerald-400 text-xs rounded-xl flex items-center space-x-2.5">
                    <CheckCircle className="w-4.5 h-4.5 text-emerald-400 shrink-0" />
                    <span>Excellent! No outdated reference or conflicting metric debt discovered in this prompt.</span>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {warnings.map((w, idx) => {
                      const isHigh = w.severity === "high";
                      return (
                        <div
                          key={idx}
                          className={`p-4 rounded-xl border flex flex-col space-y-2.5 shadow-sm transition-all duration-300 ${
                            isHigh
                              ? "bg-red-950/10 border-red-500/20 text-red-300 shadow-[0_0_15px_rgba(239,68,68,0.02)]"
                              : "bg-amber-950/10 border-amber-500/20 text-amber-300 shadow-[0_0_15px_rgba(245,158,11,0.02)]"
                          }`}
                        >
                          <div className="flex items-start justify-between">
                            <div className="flex items-center space-x-1.5 font-bold uppercase tracking-wider text-[10px]">
                              {isHigh ? (
                                <ShieldAlert className="w-3.5 h-3.5 text-red-400" />
                              ) : (
                                <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
                              )}
                              <span>{w.type.replace(/_/g, " ")}</span>
                            </div>
                            <span className={`text-[8px] font-extrabold uppercase px-1.5 py-0.5 rounded tracking-widest ${
                              isHigh ? "bg-red-500/25 text-red-200" : "bg-amber-500/25 text-amber-200"
                            }`}>
                              {w.severity}
                            </span>
                          </div>

                          <div className="text-[11px] leading-relaxed text-gray-200">
                            {w.message}
                          </div>

                          <div className={`p-2.5 rounded-lg text-[10px] leading-relaxed font-semibold border ${
                            isHigh ? "bg-red-500/5 border-red-500/10 text-red-200" : "bg-amber-500/5 border-amber-500/10 text-amber-200"
                          }`}>
                            <strong className="uppercase text-[9px] tracking-wider block mb-0.5">Recommendation:</strong>
                            {w.recommendation}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>

              {/* Rendered Prompt Output */}
              <div className="glass-panel p-6 rounded-2xl border border-white/5 space-y-3">
                <div className="flex items-center justify-between border-b border-white/5 pb-2">
                  <h3 className="text-xs font-bold text-gray-400 uppercase tracking-widest">
                    Rendered Input Prompt
                  </h3>
                  <span className="text-[9px] font-mono text-gray-500">
                    {renderedPrompt.length} chars
                  </span>
                </div>
                <div className="bg-[#050811]/90 border border-white/5 rounded-xl p-3.5 max-h-[200px] overflow-y-auto font-mono text-[10px] text-gray-400 whitespace-pre-wrap leading-relaxed">
                  {renderedPrompt}
                </div>
              </div>

              {/* Simulated LLM Completion Response */}
              <div className="glass-panel p-6 rounded-2xl border border-white/5 space-y-3">
                <div className="flex items-center justify-between border-b border-white/5 pb-2">
                  <h3 className="text-xs font-bold text-gray-400 uppercase tracking-widest">
                    Simulated LLM Completion
                  </h3>
                  <span className="text-[9px] font-mono text-indigo-400 font-bold uppercase tracking-wider">
                    {mockModel}
                  </span>
                </div>
                <div className="bg-[#050811]/90 border border-white/5 rounded-xl p-3.5 font-cyber-mono text-[10px] text-indigo-300 whitespace-pre-wrap leading-relaxed shadow-inner">
                  {mockResponse}
                </div>
              </div>

            </div>
          )}

        </div>

      </div>
    </div>
  );
};
