import React from "react";
import type { Instance, Platform, Account, Strategy, LogEntry } from "../utils";
import { cls } from "../utils";
import Sparkline from "./Sparkline";

interface RunningTabProps {
  instances: Instance[];
  platforms: Platform[];
  accounts: Account[];
  strategies: Strategy[];
  expanded: Record<string, boolean>;
  setExpanded: React.Dispatch<React.SetStateAction<Record<string, boolean>>>;
  setInstances: React.Dispatch<React.SetStateAction<Instance[]>>;
  logs: LogEntry[];
  waves: Record<string, number[]>;
  setModalOpen: React.Dispatch<React.SetStateAction<boolean>>;
}

export default function RunningTab({
  instances,
  platforms,
  accounts,
  strategies,
  expanded,
  setExpanded,
  setInstances,
  logs,
  waves,
  setModalOpen,
}: RunningTabProps) {
  const card = (it?: Instance) => {
    if (!it) {
      // 新建实例按钮
      return (
        <button
          key="add"
          onClick={() => setModalOpen(true)}
          className="h-full min-h-[140px] rounded-2xl border border-dashed flex items-center justify-center hover:bg-gray-50"
        >
          <div className="text-center">
            <div className="text-3xl">＋</div>
            <div className="text-sm text-gray-600">新建运行实例</div>
          </div>
        </button>
      );
    }

    const platform = platforms.find(p => p.id === it.platformId)?.name || it.platformId;
    const account = accounts.find(a => a.id === it.accountId)?.name || it.accountId;
    const strategy = strategies.find(s => s.id === it.strategyId)?.name || it.strategyId;
    const open = !!expanded[it.id];

    return (
      <div key={it.id} className="rounded-2xl border p-4 hover:shadow-sm bg-white">
        <div className="flex items-start justify-between gap-4">
          <div>
            <div className="text-sm text-gray-500">
              实例ID：{it.id} · 创建于 {new Date(it.createdAt).toLocaleString()}
            </div>
            <div className="mt-1 text-lg font-semibold">
              {platform} / {account} / {strategy}
            </div>
            <div className="mt-1">
              <span
                className={cls(
                  "inline-flex items-center px-2 py-0.5 rounded text-xs",
                  it.status === "运行中" && "bg-green-100 text-green-700",
                  it.status === "已停止" && "bg-gray-100 text-gray-700",
                  it.status === "异常" && "bg-red-100 text-red-700"
                )}
              >
                {it.status}
              </span>
            </div>
          </div>
          <div className="w-[220px] text-gray-500">
            <Sparkline data={waves[it.id] || [100]} />
            <div className="text-xs text-right -mt-2">波动</div>
          </div>
        </div>
        <div className="mt-3 flex items-center gap-2">
          <button
            className="px-3 py-1.5 rounded-lg border hover:bg-gray-50"
            onClick={() =>
              setInstances(s => s.map(x => (x.id === it.id ? { ...x, status: "运行中" } : x)))
            }
          >
            启动
          </button>
          <button
            className="px-3 py-1.5 rounded-lg border hover:bg-gray-50"
            onClick={() =>
              setInstances(s => s.map(x => (x.id === it.id ? { ...x, status: "已停止" } : x)))
            }
          >
            停止
          </button>
          <button
            className="px-3 py-1.5 rounded-lg border hover:bg-gray-50"
            onClick={() => setExpanded(e => ({ ...e, [it.id]: !open }))}
          >
            {open ? "收起" : "展开"}
          </button>
        </div>
        {open && (
          <div className="mt-4 rounded-xl bg-gray-50 p-3 text-sm">
            <div className="font-medium mb-2">最近日志</div>
            <ul className="max-h-40 overflow-auto leading-6">
              {logs
                .filter(l => l.scope === it.id)
                .slice(-6)
                .map((l, i) => (
                  <li key={i} className="text-gray-700">
                    <span className="text-gray-500 mr-2">{new Date(l.ts).toLocaleTimeString()}</span>
                    <span
                      className={cls(
                        "mr-2",
                        l.level === "INFO" && "text-gray-600",
                        l.level === "WARN" && "text-amber-600",
                        l.level === "ERROR" && "text-red-600"
                      )}
                    >
                      {l.level}
                    </span>
                    {l.message}
                  </li>
                ))}
              {logs.filter(l => l.scope === it.id).length === 0 && (
                <li className="text-gray-400">暂无日志</li>
              )}
            </ul>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="space-y-4">
      <div className="grid md:grid-cols-2 gap-4">
        {instances.map(it => card(it))}
        {card(undefined)}
      </div>
    </div>
  );
}
