import React from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import {
  ShieldAlert,
  CheckCircle,
  Layers,
  Settings,
  FileText,
  ArrowUpRight,
} from "lucide-react";
import { DetectorRun, Finding } from "../api/client";

interface OverviewProps {
  run: DetectorRun | null;
  findings: Finding[];
  onNavigate: (page: string) => void;
}

export const Overview: React.FC<OverviewProps> = ({
  run,
  findings,
  onNavigate,
}) => {
  const sds = run?.sds_score !== undefined ? run.sds_score : 0;

  // Historical trend data for chart
  const trendData = [
    { name: "Week 1", score: 24 },
    { name: "Week 2", score: 28 },
    { name: "Week 3", score: 41 },
    { name: "Week 4", score: 55 },
    { name: "Current", score: sds },
  ];

  // Determine score band info
  const getBandInfo = (val: number) => {
    if (val <= 20)
      return {
        text: "Healthy",
        color: "text-emerald-400",
        stroke: "#10b981",
        bg: "bg-emerald-500/10",
        border: "border-emerald-500/30",
      };
    if (val <= 40)
      return {
        text: "Watch",
        color: "text-yellow-400",
        stroke: "#facc15",
        bg: "bg-yellow-500/10",
        border: "border-yellow-500/30",
      };
    if (val <= 60)
      return {
        text: "Elevated",
        color: "text-amber-500",
        stroke: "#f59e0b",
        bg: "bg-amber-500/10",
        border: "border-amber-500/30",
      };
    if (val <= 80)
      return {
        text: "High Risk",
        color: "text-orange-500",
        stroke: "#f97316",
        bg: "bg-orange-500/10",
        border: "border-orange-500/30",
      };
    return {
      text: "Critical",
      color: "text-rose-500",
      stroke: "#f43f5e",
      bg: "bg-rose-500/10",
      border: "border-rose-500/30",
    };
  };

  const band = getBandInfo(sds);

  // SVG Gauge Calculations
  const radius = 80;
  const strokeWidth = 12;
  const normalizedRadius = radius - strokeWidth * 2;
  const circumference = normalizedRadius * 2 * Math.PI;
  const strokeDashoffset =
    circumference - (Math.min(sds, 100) / 100) * circumference;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Top Banner Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* SDS Gauge Card */}
        <div className="glass-panel p-6 rounded-2xl flex flex-col items-center justify-center relative overflow-hidden min-h-[260px]">
          <div className="absolute top-4 left-5 text-[10px] font-bold text-gray-500 uppercase tracking-widest">
            Semantic Debt Index
          </div>

          <div className="relative mt-6 flex items-center justify-center">
            {/* Fine tick indicators in circular layout */}
            <div className="absolute inset-0 flex items-center justify-center scale-110 pointer-events-none">
              <div className="w-full h-full border border-dashed border-white/[0.02] rounded-full"></div>
            </div>
            <svg
              height={radius * 2}
              width={radius * 2}
              className="gauge-svg z-10"
            >
              <circle
                className="gauge-circle-bg"
                strokeWidth={strokeWidth}
                r={normalizedRadius}
                cx={radius}
                cy={radius}
              />
              <circle
                className="gauge-circle-val"
                stroke={band.stroke}
                strokeWidth={strokeWidth}
                strokeDasharray={circumference + " " + circumference}
                style={{ strokeDashoffset }}
                r={normalizedRadius}
                cx={radius}
                cy={radius}
              />
            </svg>
            <div className="absolute flex flex-col items-center justify-center z-20">
              <span className="text-4xl font-extrabold text-white tracking-tight">
                {Math.round(sds)}
              </span>
              <span className="text-[9px] text-gray-500 font-bold tracking-widest mt-0.5">
                MAX 100
              </span>
            </div>
          </div>

          <div
            className={`mt-6 px-3.5 py-1 rounded-full text-[9px] font-bold ${band.bg} ${band.color} ${band.border} border uppercase tracking-wider`}
          >
            {band.text} System State
          </div>
        </div>

        {/* SDS Trend Chart Card */}
        <div className="glass-panel p-6 rounded-2xl lg:col-span-2 relative min-h-[260px]">
          <div className="text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-6">
            Semantic Debt Trend (SDS Timeline)
          </div>
          <div className="h-44 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart
                data={trendData}
                margin={{ top: 5, right: 5, left: -25, bottom: 0 }}
              >
                <defs>
                  <linearGradient id="colorScore" x1="0" y1="0" x2="0" y2="1">
                    <stop
                      offset="5%"
                      stopColor={band.stroke}
                      stopOpacity={0.15}
                    />
                    <stop
                      offset="95%"
                      stopColor={band.stroke}
                      stopOpacity={0.0}
                    />
                  </linearGradient>
                </defs>
                <CartesianGrid
                  strokeDasharray="4 4"
                  stroke="rgba(255,255,255,0.02)"
                  vertical={false}
                />
                <XAxis
                  dataKey="name"
                  stroke="#475569"
                  fontSize={9}
                  fontWeight="bold"
                  tickLine={false}
                  axisLine={false}
                  dy={10}
                />
                <YAxis
                  stroke="#475569"
                  fontSize={9}
                  fontWeight="bold"
                  tickLine={false}
                  axisLine={false}
                  domain={[0, 100]}
                  dx={-5}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#0d111c",
                    borderColor: "rgba(255,255,255,0.04)",
                    borderRadius: "12px",
                    boxShadow: "0 10px 25px -5px rgba(0,0,0,0.5)",
                  }}
                  labelStyle={{
                    color: "#64748b",
                    fontWeight: "bold",
                    fontSize: "10px",
                  }}
                  itemStyle={{
                    color: "#ffffff",
                    fontWeight: "bold",
                    fontSize: "11px",
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="score"
                  stroke={band.stroke}
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#colorScore)"
                  dot={{
                    stroke: band.stroke,
                    strokeWidth: 1.5,
                    r: 3,
                    fill: "#07090e",
                  }}
                  activeDot={{
                    stroke: band.stroke,
                    strokeWidth: 2,
                    r: 5,
                    fill: band.stroke,
                  }}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          {
            label: "Active Findings",
            val: findings.length,
            icon: ShieldAlert,
            color: "text-rose-400",
            bg: "bg-rose-500/5 border border-rose-500/10",
          },
          {
            label: "Business Rules",
            val: 3,
            icon: Settings,
            color: "text-amber-400",
            bg: "bg-amber-500/5 border border-amber-500/10",
          },
          {
            label: "Concept Registry",
            val: 4,
            icon: Layers,
            color: "text-indigo-400",
            bg: "bg-indigo-500/5 border border-indigo-500/10",
          },
          {
            label: "Inferences Audited",
            val: 30,
            icon: FileText,
            color: "text-emerald-400",
            bg: "bg-emerald-500/5 border border-emerald-500/10",
          },
        ].map((m, idx) => (
          <div
            key={idx}
            className="glass-panel p-4 rounded-xl flex items-center space-x-3.5"
          >
            <div className={`p-2 rounded-lg ${m.bg}`}>
              <m.icon className={`w-4 h-4 ${m.color}`} />
            </div>
            <div>
              <div className="text-[10px] text-gray-500 font-bold uppercase tracking-wider">
                {m.label}
              </div>
              <div className="text-lg font-bold text-white tracking-tight mt-0.5">
                {m.val}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Findings Preview Table */}
      <div className="glass-panel p-6 rounded-2xl">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-base font-bold text-white tracking-tight">
              Drift & Mismatch Findings
            </h2>
            <p className="text-xs text-gray-500">
              Drill down into active pipeline telemetry debt
            </p>
          </div>
          <button
            onClick={() => onNavigate("findings")}
            className="flex items-center text-xs font-bold text-indigo-400 hover:text-indigo-300 transition-colors group"
          >
            Open Explorer{" "}
            <ArrowUpRight className="w-3.5 h-3.5 ml-1 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-white/5 text-[10px] font-bold text-gray-500 uppercase tracking-wider">
                <th className="pb-3">Detector</th>
                <th className="pb-3">Severity</th>
                <th className="pb-3">Target Entity</th>
                <th className="pb-3">Actionable Remediation</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/[0.03] text-xs">
              {findings.slice(0, 5).map((f) => (
                <tr
                  key={f.id}
                  className="group hover:bg-white/[0.01] transition-colors"
                >
                  <td className="py-3 font-bold text-indigo-400/95">
                    {f.detector}
                  </td>
                  <td className="py-3">
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
                  </td>
                  <td className="py-3 font-mono text-gray-300">
                    {f.target || "Global"}
                  </td>
                  <td className="py-3 text-gray-400 group-hover:text-white transition-colors leading-relaxed">
                    {(f.payload?.recommendation as string) ||
                      "Needs evaluation"}
                  </td>
                </tr>
              ))}
              {findings.length === 0 && (
                <tr>
                  <td colSpan={4} className="py-12 text-center text-gray-500">
                    <CheckCircle className="w-8 h-8 text-emerald-500/30 mx-auto mb-2.5" />
                    <p className="text-xs font-semibold text-gray-400">
                      No semantic mismatches detected.
                    </p>
                    <p className="text-[11px] text-gray-500 mt-1">
                      Run an audit in the Ingestion Center to analyze the
                      pipeline.
                    </p>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
