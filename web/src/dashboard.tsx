import { useState, useMemo } from "react";
import Nav from "./components/Nav";
import RunningTab from "./components/RunningTab";
import ConsoleTab from "./components/ConsoleTab";
import LogsTab from "./components/LogsTab";
import StrategyTab from "./components/StrategyTab";
import AccountsTab from "./components/AccountsTab";
import PlatformsTab from "./components/PlatformsTab";
import SettingsTab from "./components/SettingsTab";
import CreateInstanceModal from "./components/CreateInstanceModal";

import type {Platform, Strategy, Account, Instance, LogEntry} from "./utils"
import {NOW, makeLog} from "./utils"


// ===== Mock 数据 =====
const INIT_PLATFORMS: Platform[] = [
  { id: "binance", name: "Binance" },
  { id: "okx", name: "OKX" },
  { id: "coinw", name: "CoinW" },
];
const INIT_STRATEGIES: Strategy[] = [
  { id: "martin-hedge", name: "马丁对冲策略", description: "双向马丁 + 锁仓解锁 + 风控熔断" },
  { id: "range-maker", name: "横盘挂单策略", description: "SMA5/20 辅助定向，TTL 重挂 + PostOnly" },
  { id: "trend-break", name: "趋势突破", description: "EMA 交叉 + ATR 追踪止损" },
];
const INIT_ACCOUNTS: Account[] = [
  { id: "BN8891", name: "BN8891", platformId: "binance", params: { leverage: 30, marginMode: "isolated", hedgeMode: true, riskLimit: 1 } },
  { id: "BN1602", name: "BN1602", platformId: "binance", params: { leverage: 20, marginMode: "cross", hedgeMode: true, riskLimit: 2 } },
  { id: "OK201", name: "OK201", platformId: "okx", params: { leverage: 10, marginMode: "isolated", hedgeMode: false, riskLimit: 1 } },
  { id: "CW1602", name: "CW1602", platformId: "coinw", params: { leverage: 5, marginMode: "isolated", hedgeMode: false, riskLimit: 1 } },
];
const INIT_INSTANCES: Instance[] = [
  { id: "i-001", platformId: "binance", accountId: "BN8891", strategyId: "martin-hedge", status: "运行中", createdAt: Date.now() - 3600_000 },
  { id: "i-002", platformId: "coinw", accountId: "CW1602", strategyId: "range-maker", status: "已停止", createdAt: Date.now() - 7200_000 },
];

export default function TradingOpsDashboard() {
  const [tab, setTab] = useState("当前运行");
  const tabs = ["当前运行", "控制台", "日志", "策略", "账号", "平台配置", "全局设置"];

  const [platforms] = useState(INIT_PLATFORMS);
  const [strategies] = useState(INIT_STRATEGIES);
  const [accounts, setAccounts] = useState(INIT_ACCOUNTS);
  const [instances, setInstances] = useState(INIT_INSTANCES);
  const [logs, setLogs] = useState<LogEntry[]>([
    makeLog("system", "INFO", `系统启动：${NOW()}`),
    makeLog("i-001", "INFO", `实例 i-001 已启动（BN8891 / 马丁对冲策略）`),
    makeLog("i-002", "WARN", `实例 i-002 已停止（CW1602 / 横盘挂单策略）`),
  ]);

  const [consoleLines, setConsoleLines] = useState(["$ 欢迎使用控制台。示例：help / status / tail logs"]);
  const [consoleInput, setConsoleInput] = useState("");

  const [modalOpen, setModalOpen] = useState(false);
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});

  // 假数据: Sparkline
  const waves: Record<string, number[]> = useMemo(
    () => Object.fromEntries(instances.map(it => [it.id, Array.from({ length: 24 }, () => 90 + Math.random() * 20)])),
    [instances]
  );

  return (
    <div className="min-h-screen bg-white text-gray-900">
      <Nav tab={tab} setTab={setTab} tabs={tabs} />

      <div className="mx-auto max-w-[1200px] px-4 py-6">
        {tab === "当前运行" && (
          <RunningTab
            instances={instances}
            platforms={platforms}
            accounts={accounts}
            strategies={strategies}
            expanded={expanded}
            setExpanded={setExpanded}
            setInstances={setInstances}
            logs={logs}
            waves={waves}
            setModalOpen={setModalOpen}
          />
        )}
        {tab === "控制台" && (
          <ConsoleTab
            instances={instances}
            logs={logs}
            consoleLines={consoleLines}
            setConsoleLines={setConsoleLines}
            consoleInput={consoleInput}
            setConsoleInput={setConsoleInput}
          />
        )}
        {tab === "日志" && <LogsTab logs={logs} />}
        {tab === "策略" && <StrategyTab strategies={strategies} />}
        {tab === "账号" && <AccountsTab accounts={accounts} platforms={platforms} setAccounts={setAccounts} setLogs={setLogs} />}
        {tab === "平台配置" && <PlatformsTab accounts={accounts} platforms={platforms} setLogs={setLogs} />}
        {tab === "全局设置" && <SettingsTab />}
      </div>

      <CreateInstanceModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        platforms={platforms}
        accounts={accounts}
        strategies={strategies}
        onCreate={(platformId, accountId, strategyId) => {
          const id = `i-${Math.random().toString(36).slice(2, 6)}`;
          const it: Instance = { id, platformId, accountId, strategyId, status: "运行中", createdAt: Date.now() };
          setInstances(s => [it, ...s]);
          setLogs(s => [...s, makeLog(id, "INFO", `实例 ${id} 已创建并启动：${platformId}/${accountId}/${strategyId}`)]);
        }}
      />

      <footer className="py-8 text-center text-sm text-gray-500">
        © {new Date().getFullYear()} 交易面板 · 演示 UI
      </footer>
    </div>
  );
}
