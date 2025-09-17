// ===== 类型定义 =====
export type Strategy = { id: string; name: string; description: string };

export type Platform = { id: string; name: string };

export type Account = {
  id: string;
  name: string;
  platformId: string;
  params: {
    leverage?: number;
    marginMode?: "isolated" | "cross";
    hedgeMode?: boolean;
    riskLimit?: number;
  };
};

export type Instance = {
  id: string;
  platformId: string;
  accountId: string;
  strategyId: string;
  status: "运行中" | "已停止" | "异常";
  createdAt: number;
};

export type LogEntry = {
  ts: number;
  level: "INFO" | "WARN" | "ERROR";
  scope: string;
  message: string;
};

export interface LogItem {
  id: string;
  source: string;
  level: "INFO" | "WARN" | "ERROR";
  msg: string;
  time: string;
}


// ===== 工具函数 =====
export const NOW = () => new Date().toLocaleString();

export function makeLog(scope: string, level: LogEntry["level"], message: string): LogEntry {
  return { ts: Date.now(), level, scope, message };
}

export function cls(...xs: Array<string | boolean | undefined>) {
  return xs.filter(Boolean).join(" ");
}

export function downloadText(filename: string, text: string) {
  const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}