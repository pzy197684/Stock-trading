import React, { useState } from "react";
import type { Account, Platform, LogEntry } from "../utils";
import { cls, makeLog, NOW } from "../utils";

interface PlatformsTabProps {
  accounts: Account[];
  platforms: Platform[];
  setLogs: React.Dispatch<React.SetStateAction<LogEntry[]>>;
}

interface PlatParams {
  rateLimitMs: number;
  slipTolerance: number;
  postOnlyDefault: boolean;
}


export default function PlatformsTab({
  accounts,
  platforms,
  setLogs,
}: PlatformsTabProps) {
  const [plat, setPlat] = useState<string>(platforms[0]?.id || "");
  const platAccounts = accounts.filter(a => a.platformId === plat);

  // 平台层参数（示意）
  const [platParams, setPlatParams] = useState<Record<string, PlatParams>>({
    binance: { rateLimitMs: 100, slipTolerance: 0.001, postOnlyDefault: false },
    okx: { rateLimitMs: 200, slipTolerance: 0.0015, postOnlyDefault: true },
    coinw: { rateLimitMs: 200, slipTolerance: 0.002, postOnlyDefault: false },
  });

  const savePlat = () => {
    setLogs(s => [
      ...s,
      makeLog("system", "INFO", `平台 ${plat} 配置已保存 @ ${NOW()}`),
    ]);
  };

  return (
    <div className="space-y-4">
      {/* 平台切换按钮 */}
      <div className="mb-1 flex gap-2 overflow-x-auto">
        {platforms.map(p => (
          <button
            key={p.id}
            onClick={() => setPlat(p.id)}
            className={cls(
              "px-3 py-1.5 rounded-full text-sm",
              plat === p.id ? "bg-black text-white" : "hover:bg-gray-100"
            )}
          >
            {p.name}
          </button>
        ))}
      </div>

      {/* 平台级设置 */}
      <div className="rounded-2xl border p-4">
        <div className="text-lg font-semibold mb-3">
          平台参数（{platforms.find(x => x.id === plat)?.name}）
        </div>
        <div className="grid md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm text-gray-600 mb-1">
              Rate Limit（ms）
            </label>
            <input
              type="number"
              className="w-full border rounded-lg px-3 py-2"
              value={platParams[plat]?.rateLimitMs || 0}
              onChange={e =>
                setPlatParams(x => ({
                  ...x,
                  [plat]: { ...x[plat], rateLimitMs: Number(e.target.value) },
                }))
              }
            />
          </div>
          <div>
            <label className="block text-sm text-gray-600 mb-1">
              滑点容忍（小数）
            </label>
            <input
              type="number"
              step="0.0001"
              className="w-full border rounded-lg px-3 py-2"
              value={platParams[plat]?.slipTolerance || 0}
              onChange={e =>
                setPlatParams(x => ({
                  ...x,
                  [plat]: { ...x[plat], slipTolerance: Number(e.target.value) },
                }))
              }
            />
          </div>
          <div className="flex items-end">
            <label className="inline-flex items-center gap-2">
              <input
                type="checkbox"
                checked={!!platParams[plat]?.postOnlyDefault}
                onChange={e =>
                  setPlatParams(x => ({
                    ...x,
                    [plat]: { ...x[plat], postOnlyDefault: e.target.checked },
                  }))
                }
              />
              <span>默认 PostOnly</span>
            </label>
          </div>
        </div>
        <div className="mt-3">
          <button
            className="px-3 py-1.5 rounded-lg border hover:bg-gray-50"
            onClick={savePlat}
          >
            保存平台配置
          </button>
        </div>
      </div>

      {/* 平台下账号视图 */}
      <div className="rounded-2xl border overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50">
            <tr>
              <th className="text-left px-3 py-2 w-40">账号</th>
              <th className="text-left px-3 py-2 w-28">杠杆</th>
              <th className="text-left px-3 py-2 w-32">保证金模式</th>
              <th className="text-left px-3 py-2 w-28">对冲模式</th>
              <th className="text-left px-3 py-2 w-28">风险限额</th>
            </tr>
          </thead>
          <tbody>
            {platAccounts.map(a => (
              <tr key={a.id} className="border-t">
                <td className="px-3 py-2 font-medium">{a.name}</td>
                <td className="px-3 py-2">{a.params.leverage}</td>
                <td className="px-3 py-2">
                  {a.params.marginMode === "cross" ? "全仓" : "逐仓"}
                </td>
                <td className="px-3 py-2">{a.params.hedgeMode ? "是" : "否"}</td>
                <td className="px-3 py-2">{a.params.riskLimit}</td>
              </tr>
            ))}
            {platAccounts.length === 0 && (
              <tr>
                <td
                  className="px-3 py-6 text-center text-gray-400"
                  colSpan={5}
                >
                  暂无账号
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
