import React from "react";
import type { Instance, LogEntry } from "../utils";

interface ConsoleTabProps {
  instances: Instance[];
  logs: LogEntry[];
  consoleLines: string[];
  setConsoleLines: React.Dispatch<React.SetStateAction<string[]>>;
  consoleInput: string;
  setConsoleInput: React.Dispatch<React.SetStateAction<string>>;
}

export default function ConsoleTab({
  instances,
  logs,
  consoleLines,
  setConsoleLines,
  consoleInput,
  setConsoleInput,
}: ConsoleTabProps) {
  const runCmd = (cmd: string) => {
    const trimmed = cmd.trim();
    if (!trimmed) return;
    setConsoleLines(s => [...s, `$ ${trimmed}`]);

    setTimeout(() => {
      if (trimmed === "help") {
        setConsoleLines(s => [...s, "可用命令：help / status / tail logs / clear"]);
      } else if (trimmed === "status") {
        setConsoleLines(s => [
          ...s,
          `实例数：${instances.length}；运行中：${instances.filter(x => x.status === "运行中").length}`,
        ]);
      } else if (trimmed.startsWith("tail")) {
        const last = logs
          .slice(-3)
          .map(l => `${new Date(l.ts).toLocaleTimeString()} ${l.level} ${l.scope}: ${l.message}`);
        setConsoleLines(s => [...s, ...last]);
      } else if (trimmed === "clear") {
        setConsoleLines(["$ 控制台已清屏"]);
      } else {
        setConsoleLines(s => [...s, `未知命令：${trimmed}`]);
      }
    }, 200);
  };

  return (
    <div className="rounded-2xl border bg-black text-gray-100 p-3">
      <div className="h-72 overflow-auto font-mono text-sm whitespace-pre-wrap" id="console-box">
        {consoleLines.join("\n")}
      </div>
      <div className="mt-3 flex gap-2">
        <input
          className="flex-1 px-3 py-2 rounded bg-gray-900 border border-gray-700 outline-none"
          placeholder="输入命令，例如：help"
          value={consoleInput}
          onChange={e => setConsoleInput(e.target.value)}
          onKeyDown={e => {
            if (e.key === "Enter") {
              runCmd(consoleInput);
              setConsoleInput("");
            }
          }}
        />
        <button
          className="px-3 py-2 rounded bg-white text-black"
          onClick={() => {
            runCmd(consoleInput);
            setConsoleInput("");
          }}
        >
          执行
        </button>
      </div>
    </div>
  );
}
