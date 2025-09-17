import { useState } from "react";
import type { LogEntry } from "../utils";
import { cls, downloadText } from "../utils";
interface LogsTabProps {
    logs: LogEntry[];
}

export default function LogsTab({ logs }: LogsTabProps) {
    const [q, setQ] = useState("");
    const [lvl, setLvl] = useState<"ALL" | LogEntry["level"]>("ALL");

    const view = logs.filter(
        l =>
            (lvl === "ALL" || l.level === lvl) &&
            (q === "" || l.message.includes(q) || l.scope.includes(q))
    );

    const exportCSV = () => {
        const hdr = "ts,level,scope,message\n";
        const body = view
            .map(
                l =>
                    `${new Date(l.ts).toISOString()},${l.level},${l.scope},"${l.message.replace(/"/g, '""')}"`
            )
            .join("\n");
        downloadText(`logs_${Date.now()}.csv`, hdr + body + "\n");
    };

    const exportTXT = () => {
        const body = view
            .map(
                l =>
                    `${new Date(l.ts).toLocaleString()} [${l.level}] ${l.scope} - ${l.message}`
            )
            .join("\n");
        downloadText(`logs_${Date.now()}.txt`, body);
    };

    return (
        <div>
            <div className="flex flex-col md:flex-row md:items-center gap-3 mb-3">
                <input
                    className="flex-1 border rounded-lg px-3 py-2"
                    placeholder="关键词..."
                    value={q}
                    onChange={e => setQ(e.target.value)}
                />
                <select
                    className="border rounded-lg px-3 py-2"
                    value={lvl}
                    onChange={(e: React.ChangeEvent<HTMLSelectElement>) =>
                        setLvl(e.target.value as "INFO" | "WARN" | "ERROR")
                    }
                >
                    <option value="ALL">全部级别</option>
                    <option value="INFO">INFO</option>
                    <option value="WARN">WARN</option>
                    <option value="ERROR">ERROR</option>
                </select>
                <div className="flex gap-2">
                    <button className="px-3 py-2 rounded-lg border" onClick={exportCSV}>
                        导出 CSV
                    </button>
                    <button className="px-3 py-2 rounded-lg border" onClick={exportTXT}>
                        导出 TXT
                    </button>
                </div>
            </div>
            <div className="rounded-2xl border overflow-hidden">
                <table className="w-full text-sm">
                    <thead className="bg-gray-50">
                        <tr>
                            <th className="text-left px-3 py-2 w-48">时间</th>
                            <th className="text-left px-3 py-2 w-20">级别</th>
                            <th className="text-left px-3 py-2 w-24">范围</th>
                            <th className="text-left px-3 py-2">内容</th>
                        </tr>
                    </thead>
                    <tbody>
                        {view.slice(-500).map((l, i) => (
                            <tr key={i} className="border-t">
                                <td className="px-3 py-2 text-gray-600">
                                    {new Date(l.ts).toLocaleString()}
                                </td>
                                <td className="px-3 py-2">
                                    <span
                                        className={cls(
                                            "px-2 py-0.5 rounded text-xs",
                                            l.level === "INFO" && "bg-gray-100 text-gray-700",
                                            l.level === "WARN" && "bg-amber-100 text-amber-700",
                                            l.level === "ERROR" && "bg-red-100 text-red-700"
                                        )}
                                    >
                                        {l.level}
                                    </span>
                                </td>
                                <td className="px-3 py-2 text-gray-600">{l.scope}</td>
                                <td className="px-3 py-2">{l.message}</td>
                            </tr>
                        ))}
                        {view.length === 0 && (
                            <tr>
                                <td
                                    className="px-3 py-6 text-center text-gray-400"
                                    colSpan={4}
                                >
                                    暂无数据
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
