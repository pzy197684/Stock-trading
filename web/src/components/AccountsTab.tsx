import React, { useState } from "react";
import type { Account, Platform, LogEntry } from "../utils";
import { cls, makeLog, NOW } from "../utils";

interface AccountsTabProps {
    accounts: Account[];
    platforms: Platform[];
    setAccounts: React.Dispatch<React.SetStateAction<Account[]>>;
    setLogs: React.Dispatch<React.SetStateAction<LogEntry[]>>;
}

export default function AccountsTab({
    accounts,
    platforms,
    setAccounts,
    setLogs,
}: AccountsTabProps) {
    const [plat, setPlat] = useState<string>(platforms[0]?.id || "");
    const view = accounts.filter(a => a.platformId === plat);

    const updateAccount = (id: string, patch: Partial<Account["params"]>) => {
        setAccounts(xs =>
            xs.map(acc =>
                acc.id === id ? { ...acc, params: { ...acc.params, ...patch } } : acc
            )
        );
        setLogs(s => [
            ...s,
            makeLog("system", "INFO", `账号 ${id} 参数已更新 @ ${NOW()}`),
        ]);
    };

    return (
        <div>
            <div className="mb-3 flex gap-2 overflow-x-auto">
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
            <div className="rounded-2xl border overflow-hidden">
                <table className="w-full text-sm">
                    <thead className="bg-gray-50">
                        <tr>
                            <th className="text-left px-3 py-2 w-32">账号</th>
                            <th className="text-left px-3 py-2 w-28">杠杆</th>
                            <th className="text-left px-3 py-2 w-36">保证金模式</th>
                            <th className="text-left px-3 py-2 w-28">对冲模式</th>
                            <th className="text-left px-3 py-2 w-28">风险限额</th>
                            <th className="text-left px-3 py-2">操作</th>
                        </tr>
                    </thead>
                    <tbody>
                        {view.map(a => (
                            <tr key={a.id} className="border-t">
                                <td className="px-3 py-2 font-medium">{a.name}</td>
                                <td className="px-3 py-2">
                                    <input
                                        type="number"
                                        className="w-24 border rounded-lg px-2 py-1"
                                        value={a.params.leverage || 0}
                                        onChange={e =>
                                            updateAccount(a.id, { leverage: Number(e.target.value) })
                                        }
                                    />
                                </td>
                                <td className="px-3 py-2">
                                    <select
                                        className="w-32 border rounded-lg px-2 py-1"
                                        value={a.params.marginMode || "isolated"}
                                        onChange={e =>
                                            updateAccount(a.id, {
                                                marginMode: e.target.value as "isolated" | "cross",
                                            })
                                        }
                                    >
                                        <option value="isolated">逐仓</option>
                                        <option value="cross">全仓</option>
                                    </select>
                                </td>
                                <td className="px-3 py-2">
                                    <label className="inline-flex items-center gap-2">
                                        <input
                                            type="checkbox"
                                            checked={!!a.params.hedgeMode}
                                            onChange={e =>
                                                updateAccount(a.id, { hedgeMode: e.target.checked })
                                            }
                                        />
                                        <span>开启</span>
                                    </label>
                                </td>
                                <td className="px-3 py-2">
                                    <input
                                        type="number"
                                        className="w-24 border rounded-lg px-2 py-1"
                                        value={a.params.riskLimit || 0}
                                        onChange={e =>
                                            updateAccount(a.id, { riskLimit: Number(e.target.value) })
                                        }
                                    />
                                </td>
                                <td className="px-3 py-2">
                                    <button
                                        className="px-3 py-1.5 rounded-lg border hover:bg-gray-50"
                                        onClick={() =>
                                            setLogs(s => [
                                                ...s,
                                                makeLog(
                                                    "system",
                                                    "INFO",
                                                    `[预留] 已保存账号 ${a.name}`
                                                ),
                                            ])
                                        }
                                    >
                                        保存
                                    </button>
                                </td>
                            </tr>
                        ))}
                        {view.length === 0 && (
                            <tr>
                                <td
                                    className="px-3 py-6 text-center text-gray-400"
                                    colSpan={6}
                                >
                                    当前平台暂无账号
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
