import React, { useState } from "react";
import { ActionCard } from "../api/client";
import { CheckSquare, Square, CheckCircle } from "lucide-react";

interface ActionCenterProps {
  actions: ActionCard[];
  onUpdateStatus: (actionId: string, status: string) => Promise<void>;
}

export const ActionCenter: React.FC<ActionCenterProps> = ({
  actions,
  onUpdateStatus,
}) => {
  const [filterStatus, setFilterStatus] = useState<string>("open");
  const [checkedSteps, setCheckedSteps] = useState<Record<string, boolean>>({});

  const filteredActions = actions.filter((a) => a.status === filterStatus);

  const toggleStep = (cardId: string, stepIdx: number) => {
    const key = `${cardId}-${stepIdx}`;
    setCheckedSteps((prev) => ({
      ...prev,
      [key]: !prev[key],
    }));
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header and Filter */}
      <div className="glass-panel p-6 rounded-2xl flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h2 className="text-base font-bold text-white tracking-tight">
            Remediation Action Center
          </h2>
          <p className="text-xs text-gray-500">
            Prioritized checklists to reconcile meaning offsets and reduce
            semantic debt
          </p>
        </div>

        <div className="flex space-x-1 bg-[#0a0d16] p-1 border border-white/5 rounded-xl w-fit">
          {["open", "acknowledged", "resolved"].map((status) => (
            <button
              key={status}
              onClick={() => setFilterStatus(status)}
              className={`px-3.5 py-1.5 rounded-lg text-[10px] font-bold uppercase tracking-wider transition-colors ${
                filterStatus === status
                  ? "bg-indigo-600/15 border border-indigo-500/30 text-indigo-400 shadow-sm"
                  : "text-gray-500 hover:text-gray-300 border border-transparent"
              }`}
            >
              {status}
            </button>
          ))}
        </div>
      </div>

      {/* Cards List */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {filteredActions.map((card) => (
          <div
            key={card.id}
            className="glass-panel p-6 rounded-2xl flex flex-col justify-between border border-white/5 relative overflow-hidden group min-h-[300px]"
          >
            {/* Top Indicator bar */}
            <div
              className={`absolute top-0 left-0 w-full h-[2px] ${
                card.priority > 0.8
                  ? "bg-rose-500"
                  : card.priority > 0.5
                    ? "bg-orange-500"
                    : "bg-blue-500"
              }`}
            />

            <div className="space-y-4">
              <div className="flex items-start justify-between">
                <div className="space-y-1">
                  <span className="text-[9px] font-bold uppercase tracking-wider text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded border border-indigo-500/20">
                    {card.action_type}
                  </span>
                  <h3 className="text-sm font-bold text-white mt-2 leading-snug tracking-tight">
                    {card.title}
                  </h3>
                </div>
                <div className="text-right pl-3">
                  <div className="text-[9px] text-gray-500 font-bold uppercase tracking-wider">
                    Score
                  </div>
                  <div className="text-base font-extrabold text-indigo-300 mt-0.5">
                    {card.priority.toFixed(2)}
                  </div>
                </div>
              </div>

              <hr className="border-white/5" />

              {/* Step checklist */}
              <div className="space-y-2.5">
                <span className="text-[9px] font-bold text-gray-500 uppercase tracking-widest block">
                  Remediation workflow steps
                </span>
                <div className="space-y-3">
                  {card.steps.map((step, idx) => {
                    const isChecked =
                      checkedSteps[`${card.id}-${idx}`] || false;
                    const isSdsStep = step.includes("Expected SDS");

                    if (isSdsStep) {
                      return (
                        <div
                          key={idx}
                          className="mt-3 text-[10px] font-bold text-indigo-400/90 bg-indigo-500/5 p-2 rounded-lg border border-indigo-500/10 tracking-wide uppercase"
                        >
                          {step}
                        </div>
                      );
                    }

                    return (
                      <div
                        key={idx}
                        onClick={() => toggleStep(card.id, idx)}
                        className="flex items-start space-x-3 cursor-pointer text-xs group"
                      >
                        {isChecked ? (
                          <CheckSquare className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                        ) : (
                          <Square className="w-4 h-4 text-gray-600 group-hover:text-gray-500 shrink-0 mt-0.5" />
                        )}
                        <span
                          className={`leading-relaxed font-medium transition-all ${isChecked ? "text-gray-650 line-through" : "text-gray-300 group-hover:text-white"}`}
                        >
                          {step}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>

            {/* Action buttons */}
            <div className="mt-6 pt-4 border-t border-white/5 flex items-center justify-end space-x-2">
              {card.status === "open" && (
                <button
                  onClick={() => onUpdateStatus(card.id, "acknowledged")}
                  className="px-3.5 py-1.5 rounded-lg border border-white/5 text-[11px] font-bold text-gray-400 hover:text-white hover:border-white/10 transition-colors"
                >
                  Acknowledge
                </button>
              )}
              {card.status !== "resolved" && (
                <button
                  onClick={() => onUpdateStatus(card.id, "resolved")}
                  className="px-3.5 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-[11px] font-bold text-white transition-colors flex items-center shadow-lg shadow-indigo-600/10"
                >
                  Resolve Item <CheckCircle className="w-3.5 h-3.5 ml-1" />
                </button>
              )}
            </div>
          </div>
        ))}

        {filteredActions.length === 0 && (
          <div className="glass-panel p-12 rounded-2xl text-center text-gray-500 col-span-2">
            <CheckCircle className="w-10 h-10 text-emerald-500/30 mx-auto mb-2.5" />
            <p className="text-xs font-semibold text-gray-400">
              No tasks in the "{filterStatus}" queue.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
