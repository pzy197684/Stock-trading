import React, { useState, useMemo } from "react";
import { motion } from "framer-motion";

// Single-file React component for the trading UI framework
// Default export a React component named TradingUI
// TailwindCSS required in the hosting project. This file uses Tailwind classes.

// Mock data templates (replace with real backend / websockets later)
const PLATFORMS = [
  { id: "platA", name: "平台A" },
  { id: "platB", name: "平台B" },
];

const STRATEGIES = [
  { id: "strat_a", name: "策略A", desc: "均线突破策略，买多/买空都支持" },
  { id: "strat_b", name: "策略B", desc: "做市型策略，适合高频撮合" },
];

const SAMPLE_ACCOUNTS = [
  { id: "acc1", platform: "platA", owner: "爸爸", name: "A-001", paramsTemplate: "默认" },
  { id: "acc2", platform: "platB", owner: "妈妈", name: "B-002", paramsTemplate: "保守" },
];

// helpers
function downloadFile(filename, content, mime = "text/plain") {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

function exportLogsCSV(logs) {
  const header = ["time", "instanceId", "level", "message"].join(",");
  const rows = logs
    .map((l) => [l.time, l.instanceId, l.level, `"${l.message.replace(/"/g, '""')}"`].join(","));
  return [header, ...rows].join("\n");
}

// Main component
export default function TradingUI() {
  const [tab, setTab] = useState("running");
  const [platforms] = useState(PLATFORMS);
  const [strategies] = useState(STRATEGIES);
  const [accounts, setAccounts] = useState(SAMPLE_ACCOUNTS);

  // Instances: each running strategy instance tied to a platform account
  const [instances, setInstances] = useState([
    {
      id: "inst-1",
      platform: "platA",
      accountId: "acc1",
      accountName: "A-001",
      strategyId: "strat_a",
      strategyName: "策略A",
      status: "running",
      owner: "爸爸",
      logs: [
        { time: new Date().toLocaleString(), level: "info", message: "启动策略", instanceId: "inst-1" },
      ],
      pnl: 12.34,
      expanded: false,
    },
  ]);

  const [owners] = useState(["全部", "爸爸", "妈妈"]);
  const [ownerFilter, setOwnerFilter] = useState("全部");

  // Console state
  const [consoleText, setConsoleText] = useState("");
  const [consoleLines, setConsoleLines] = useState(["欢迎使用控制台。输入help以查看命令。"]);
  const [showCalc, setShowCalc] = useState(false);

  // Logs global (flattened)
  const allLogs = useMemo(() => instances.flatMap((i) => i.logs || []), [instances]);
  const [logLevelFilter, setLogLevelFilter] = useState("all");

  // Create instance modal state
  const [creating, setCreating] = useState(false);
  const [newPlatform, setNewPlatform] = useState(platforms[0]?.id || "");
  const [newAccount, setNewAccount] = useState("");
  const [newStrategy, setNewStrategy] = useState(strategies[0]?.id || "");

  // Platform & account management state
  const [activePlatform, setActivePlatform] = useState(platforms[0]?.id || "");

  // Handlers
  function addInstance({ platformId, accountId, strategyId }) {
    const platform = platforms.find((p) => p.id === platformId)?.name || platformId;
    const account = accounts.find((a) => a.id === accountId);
    const strategy = strategies.find((s) => s.id === strategyId);
    const id = "inst-" + Date.now();
    const instance = {
      id,
      platform: platformId,
      accountId,
      accountName: account?.name || accountId,
      strategyId,
      strategyName: strategy?.name || strategyId,
      status: "running",
      owner: account?.owner || "未指定",
      logs: [{ time: new Date().toLocaleString(), level: "info", message: "实例创建并运行", instanceId: id }],
      pnl: 0,
      expanded: false,
    };
    setInstances((s) => [instance, ...s]);
    setCreating(false);
  }

  function toggleInstanceExpand(id) {
    setInstances((s) => s.map((i) => (i.id === id ? { ...i, expanded: !i.expanded } : i)));
  }

  function stopInstance(id) {
    // second-step confirmation handled by modal in UI
    setInstances((s) => s.map((i) => (i.id === id ? { ...i, status: "stopped", logs: [...(i.logs || []), { time: new Date().toLocaleString(), level: "warn", message: "已停止策略", instanceId: id }], } : i)));
  }

  function closePositionAndStop(id) {
    setInstances((s) => s.map((i) => (i.id === id ? { ...i, status: "closed", logs: [...(i.logs || []), { time: new Date().toLocaleString(), level: "warn", message: "一键平仓并停止策略", instanceId: id }], } : i)));
  }

  function addConsoleLine(line) {
    setConsoleLines((l) => [...l, `[${new Date().toLocaleTimeString()}] ${line}`]);
  }

  function handleConsoleSubmit(e) {
    e.preventDefault();
    const cmd = consoleText.trim();
    if (!cmd) return;
    addConsoleLine(`> ${cmd}`);
    // simple fake commands
    if (cmd === "help") {
      addConsoleLine("支持命令：list, instances, help, clear");
    } else if (cmd === "list" || cmd === "instances") {
      addConsoleLine(`当前实例数: ${instances.length}`);
      instances.forEach((ins) => addConsoleLine(`${ins.id} - ${ins.strategyName} - ${ins.status}`));
    } else if (cmd === "clear") {
      setConsoleLines([]);
    } else {
      addConsoleLine("未知命令: " + cmd);
    }
    setConsoleText("");
  }

  function exportLogsTxt() {
    downloadFile("logs.txt", allLogs.map((l) => `[${l.time}] [${l.level}] ${l.instanceId} - ${l.message}`).join("\n\n"));
  }

  function exportLogsAsCSV() {
    const csv = exportLogsCSV(allLogs);
    downloadFile("logs.csv", csv, "text/csv");
  }

  function removeInstance(id) {
    setInstances((s) => s.filter((i) => i.id !== id));
  }

  // UI Components inside the file
  const TabButton = ({ id, children }) => (
    <button
      className={`px-4 py-2 rounded-md ${tab === id ? "bg-slate-800 text-white" : "bg-slate-100"}`}
      onClick={() => setTab(id)}
    >
      {children}
    </button>
  );

  // Small confirmation modal component
  const ConfirmModal = ({ open, title, message, onConfirm, onCancel }) => {
    if (!open) return null;
    return (
      <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6 w-96 shadow-lg">
          <h3 className="font-bold text-lg">{title}</h3>
          <p className="mt-2 text-sm">{message}</p>
          <div className="mt-4 flex justify-end gap-2">
            <button onClick={onCancel} className="px-3 py-1 rounded bg-slate-200">取消</button>
            <button onClick={onConfirm} className="px-3 py-1 rounded bg-red-500 text-white">确认</button>
          </div>
        </div>
      </div>
    );
  };

  // Per-instance confirm states
  const [confirmState, setConfirmState] = useState({ open: false, action: null, id: null });

  return (
    <div className="min-h-screen bg-slate-50 p-6">
      <div className="max-w-6xl mx-auto">
        <header className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold">炒股软件 控制面板（UI 原型）</h1>
          <nav className="flex gap-2">
            <TabButton id="running">当前运行</TabButton>
            <TabButton id="console">控制台工具</TabButton>
            <TabButton id="logs">日志</TabButton>
            <TabButton id="strategies">策略</TabButton>
            <TabButton id="accounts">账号</TabButton>
            <TabButton id="platforms">平台配置</TabButton>
            <TabButton id="global">全局设置</TabButton>
          </nav>
        </header>

        <main className="bg-white rounded-lg shadow p-4">
          {tab === "running" && (
            <section>
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <label className="text-sm">拥有者筛选：</label>
                  <select value={ownerFilter} onChange={(e) => setOwnerFilter(e.target.value)} className="border px-2 py-1 rounded">
                    {owners.map((o) => <option key={o} value={o}>{o}</option>)}
                  </select>
                </div>
                <div className="text-sm text-slate-500">实例数: {instances.length}</div>
              </div>

              <div className="space-y-3">
                {instances.filter(i => ownerFilter === "全部" || i.owner === ownerFilter).map((ins) => (
                  <motion.div layout key={ins.id} className="border rounded p-3 bg-white">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-4">
                        <div className="text-sm text-slate-500">{platforms.find(p=>p.id===ins.platform)?.name || ins.platform}</div>
                        <div className="font-medium">{ins.accountName}</div>
                        <div className="text-sm text-slate-400">{ins.strategyName}</div>
                        <div className={`px-2 py-0.5 rounded text-xs ${ins.status === 'running' ? 'bg-green-100 text-green-800' : ins.status === 'stopped' ? 'bg-yellow-100 text-yellow-800' : 'bg-slate-100 text-slate-800'}`}>{ins.status}</div>
                        <div className="text-sm text-slate-600">PNL: {ins.pnl}</div>
                      </div>

                      <div className="flex items-center gap-2">
                        <button onClick={() => { setConfirmState({ open: true, action: 'stop', id: ins.id }); }} className="px-3 py-1 rounded bg-yellow-400 text-white">停止策略</button>
                        <button onClick={() => { setConfirmState({ open: true, action: 'close', id: ins.id }); }} className="px-3 py-1 rounded bg-red-500 text-white">一键平仓并停止</button>
                        <button onClick={() => toggleInstanceExpand(ins.id)} className="px-2 py-1 rounded bg-slate-100">{ins.expanded ? '收起' : '展开'}</button>
                      </div>
                    </div>

                    {ins.expanded && (
                      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mt-3 border-t pt-3">
                        <div className="text-xs text-slate-500">更多信息</div>
                        <div className="mt-2 grid grid-cols-3 gap-3">
                          <div className="p-2 border rounded">详细状态：{ins.status}</div>
                          <div className="p-2 border rounded">最近日志：{ins.logs.slice(-1)[0]?.message}</div>
                          <div className="p-2 border rounded">持仓详情（模拟）</div>
                        </div>

                        <div className="mt-3">
                          <div className="text-sm font-medium">运行日志</div>
                          <div className="max-h-32 overflow-auto mt-2 text-xs bg-slate-50 p-2 rounded">{ins.logs.map((l, idx) => <div key={idx}>[{l.time}] {l.level} — {l.message}</div>)}</div>
                        </div>
                      </motion.div>
                    )}
                  </motion.div>
                ))}

                {/* Add new instance card */}
                <div className="border rounded p-4 flex items-center justify-center text-slate-400 hover:bg-slate-50 cursor-pointer" onClick={() => setCreating(true)}>
                  + 添加实例
                </div>
              </div>

              {/* create modal */}
              {creating && (
                <div className="fixed inset-0 bg-black/40 z-40 flex items-center justify-center">
                  <div className="bg-white rounded-lg p-6 w-96">
                    <h3 className="font-bold">创建新实例</h3>
                    <div className="mt-3">
                      <label className="text-sm">平台</label>
                      <select value={newPlatform} onChange={(e) => setNewPlatform(e.target.value)} className="w-full border px-2 py-1 rounded mt-1">
                        {platforms.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
                      </select>
                    </div>
                    <div className="mt-3">
                      <label className="text-sm">账号</label>
                      <select value={newAccount} onChange={(e) => setNewAccount(e.target.value)} className="w-full border px-2 py-1 rounded mt-1">
                        <option value="">-- 选择一个账号 --</option>
                        {accounts.filter(a=>a.platform===newPlatform).map(a => <option key={a.id} value={a.id}>{a.name} ({a.owner})</option>)}
                      </select>
                    </div>
                    <div className="mt-3">
                      <label className="text-sm">策略</label>
                      <select value={newStrategy} onChange={(e) => setNewStrategy(e.target.value)} className="w-full border px-2 py-1 rounded mt-1">
                        {strategies.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
                      </select>
                    </div>
                    <div className="mt-4 flex justify-end gap-2">
                      <button onClick={() => setCreating(false)} className="px-3 py-1 rounded bg-slate-200">取消</button>
                      <button onClick={() => addInstance({ platformId: newPlatform, accountId: newAccount, strategyId: newStrategy })} className="px-3 py-1 rounded bg-blue-600 text-white">创建并启动</button>
                    </div>
                  </div>
                </div>
              )}

              <ConfirmModal
                open={confirmState.open}
                title={confirmState.action === 'stop' ? '确认停止策略？' : '确认一键平仓并停止？'}
                message={confirmState.action === 'stop' ? '此操作会停止策略，但不会尝试平仓。是否继续？' : '此操作会尝试平掉所有持仓并停止策略。是否继续？'}
                onCancel={() => setConfirmState({ open: false, action: null, id: null })}
                onConfirm={() => {
                  if (confirmState.action === 'stop') stopInstance(confirmState.id);
                  else if (confirmState.action === 'close') closePositionAndStop(confirmState.id);
                  setConfirmState({ open: false, action: null, id: null });
                }}
              />
            </section>
          )}

          {tab === "console" && (
            <section>
              <div className="grid grid-cols-3 gap-4">
                <div className="col-span-2">
                  <div className="border rounded p-2 h-64 overflow-auto bg-black text-green-200 font-mono text-sm">
                    {consoleLines.map((l, idx) => <div key={idx}>{l}</div>)}
                  </div>
                  <form onSubmit={handleConsoleSubmit} className="mt-2 flex gap-2">
                    <input value={consoleText} onChange={(e)=>setConsoleText(e.target.value)} className="flex-1 border rounded px-2 py-1" placeholder="输入命令..." />
                    <button type="submit" className="px-3 py-1 rounded bg-blue-600 text-white">执行</button>
                  </form>
                </div>

                <div className="col-span-1">
                  <div className="grid grid-cols-2 gap-2">
                    <button onClick={() => setShowCalc(true)} className="p-3 rounded border">计算器</button>
                    <button onClick={()=>{ addConsoleLine('预设工具: 下载示例报告'); downloadFile('example-report.txt','示例报告内容'); }} className="p-3 rounded border">报告导出</button>
                    <button onClick={()=>addConsoleLine('预设工具: 刷新账户列表') } className="p-3 rounded border">刷新账户</button>
                    <button onClick={()=>addConsoleLine('预设工具: 模拟行情快照')} className="p-3 rounded border">行情快照</button>
                  </div>

                  {showCalc && (
                    <div className="mt-3 p-3 border rounded bg-white">
                      <div className="flex justify-between items-center mb-2">
                        <div className="font-medium">简易计算器</div>
                        <button onClick={()=>setShowCalc(false)} className="text-sm text-slate-500">关闭</button>
                      </div>
                      <Calculator onResult={(r)=>{ addConsoleLine('计算结果: ' + r); }} />
                    </div>
                  )}
                </div>
              </div>
            </section>
          )}

          {tab === "logs" && (
            <section>
              <div className="flex items-center justify-between mb-3">
                <div>
                  <label className="mr-2">级别筛选</label>
                  <select value={logLevelFilter} onChange={(e)=>setLogLevelFilter(e.target.value)} className="border px-2 py-1 rounded">
                    <option value="all">全部</option>
                    <option value="info">info</option>
                    <option value="warn">warn</option>
                    <option value="error">error</option>
                  </select>
                </div>
                <div className="flex gap-2">
                  <button onClick={exportLogsTxt} className="px-3 py-1 rounded bg-slate-200">导出 TXT</button>
                  <button onClick={exportLogsAsCSV} className="px-3 py-1 rounded bg-slate-200">导出 CSV</button>
                </div>
              </div>

              <div className="max-h-96 overflow-auto border rounded p-2 bg-slate-50">
                {allLogs.filter(l => logLevelFilter === 'all' || l.level === logLevelFilter).map((l, idx) => (
                  <div key={idx} className="border-b py-1 text-xs">[{l.time}] [{l.level}] {l.instanceId} — {l.message}</div>
                ))}
              </div>

              <div className="mt-4">
                <div className="text-sm font-medium">盈亏统计（示例）</div>
                <div className="mt-2 grid grid-cols-3 gap-3">
                  <div className="p-2 border rounded">总盈亏: {instances.reduce((s,i)=>s+(i.pnl||0),0).toFixed(2)}</div>
                  <div className="p-2 border rounded">盈利账户数: {instances.filter(i=>i.pnl>0).length}</div>
                  <div className="p-2 border rounded">亏损账户数: {instances.filter(i=>i.pnl<0).length}</div>
                </div>
              </div>
            </section>
          )}

          {tab === "strategies" && (
            <section>
              <div className="grid grid-cols-1 gap-3">
                {strategies.map(s => (
                  <div key={s.id} className="border rounded p-3">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="font-medium">{s.name}</div>
                        <div className="text-sm text-slate-500">{s.desc}</div>
                      </div>
                      <div className="text-xs text-slate-400">只读展示</div>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          )}

          {tab === "accounts" && (
            <section>
              <div className="flex gap-4">
                <aside className="w-64 border rounded p-2">
                  <div className="text-sm font-medium mb-2">平台</div>
                  <div className="space-y-1">
                    {platforms.map(p => <div key={p.id} className={`p-2 rounded cursor-pointer ${activePlatform===p.id ? 'bg-slate-100' : ''}`} onClick={()=>setActivePlatform(p.id)}>{p.name}</div>)}
                  </div>
                </aside>

                <div className="flex-1">
                  <div className="text-sm font-medium mb-2">账号（属于 {platforms.find(p=>p.id===activePlatform)?.name}）</div>
                  <div className="grid grid-cols-2 gap-3">
                    {accounts.filter(a=>a.platform===activePlatform).map(a => (
                      <div key={a.id} className="border rounded p-3">
                        <div className="flex items-center justify-between">
                          <div>
                            <div className="font-medium">{a.name}</div>
                            <div className="text-xs text-slate-500">拥有者: {a.owner}</div>
                          </div>
                          <div className="text-xs">模板: {a.paramsTemplate}</div>
                        </div>
                        <div className="mt-2 text-sm">账号参数（示例，可在这里编辑）：</div>
                        <div className="mt-2 grid grid-cols-2 gap-2">
                          <label className="text-xs">最大下单量</label>
                          <input className="border px-2 py-1 text-sm" defaultValue={100} />
                          <label className="text-xs">风险模板</label>
                          <select defaultValue={a.paramsTemplate} className="border px-2 py-1 text-sm"><option>默认</option><option>保守</option><option>激进</option></select>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </section>
          )}

          {tab === "platforms" && (
            <section>
              <div className="grid grid-cols-2 gap-3">
                {platforms.map(p => (
                  <div key={p.id} className="border rounded p-3">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="font-medium">{p.name}</div>
                        <div className="text-xs text-slate-500">接口频率、超时、API Key 管理等</div>
                      </div>
                      <div className="text-xs text-slate-400">可配置</div>
                    </div>

                    <div className="mt-3 grid grid-cols-2 gap-2 text-sm">
                      <div>请求频率(ms)</div>
                      <input defaultValue={500} className="border px-2 py-1" />
                      <div>超时(s)</div>
                      <input defaultValue={30} className="border px-2 py-1" />
                      <div>最大重试</div>
                      <input defaultValue={3} className="border px-2 py-1" />
                    </div>

                    <div className="mt-3 text-sm font-medium">该平台账户</div>
                    <div className="mt-2 space-y-1">
                      {accounts.filter(a=>a.platform===p.id).map(a=> (
                        <div key={a.id} className="flex items-center justify-between p-2 border rounded">
                          <div>{a.name} ({a.owner})</div>
                          <div className="text-xs">编辑</div>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </section>
          )}

          {tab === "global" && (
            <section>
              <div className="grid grid-cols-2 gap-3">
                <div className="border rounded p-3">
                  <div className="font-medium">通知设置</div>
                  <div className="mt-2 space-y-2 text-sm">
                    <label className="flex items-center gap-2"><input type="checkbox" /> 实例状态变更通知</label>
                    <label className="flex items-center gap-2"><input type="checkbox" /> 盈亏阈值提醒</label>
                    <label className="flex items-center gap-2"><input type="checkbox" /> 风险事件报警</label>
                  </div>
                </div>

                <div className="border rounded p-3">
                  <div className="font-medium">显示 / UX</div>
                  <div className="mt-2 space-y-2 text-sm">
                    <label className="flex items-center gap-2"><input type="checkbox" /> 深色模式</label>
                    <label className="flex items-center gap-2"><input type="checkbox" /> 启用动画效果</label>
                  </div>
                </div>
              </div>
            </section>
          )}

        </main>
      </div>
    </div>
  );
}

// Small calculator component used by Console tools
function Calculator({ onResult }) {
  const [expr, setExpr] = React.useState("");
  const [result, setResult] = React.useState(null);

  function calc() {
    try {
      // eslint-disable-next-line no-eval
      const res = eval(expr);
      setResult(res);
      onResult && onResult(res);
    } catch (e) {
      setResult("错误");
    }
  }

  return (
    <div>
      <input value={expr} onChange={(e)=>setExpr(e.target.value)} placeholder="输入算式，例如 1+2*3" className="w-full border px-2 py-1 mb-2" />
      <div className="flex gap-2">
        <button onClick={calc} className="px-3 py-1 rounded bg-blue-600 text-white">计算</button>
        <button onClick={()=>{ setExpr(""); setResult(null); }} className="px-3 py-1 rounded bg-slate-200">清除</button>
      </div>
      <div className="mt-2">结果: <span className="font-mono">{String(result)}</span></div>
    </div>
  );
}
