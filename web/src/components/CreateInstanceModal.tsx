import { useState, useEffect, useMemo } from "react";
import type { Account, Platform, Strategy } from "../utils";
import { cls } from "../utils";

interface CreateInstanceModalProps {
  open: boolean;
  onClose: () => void;
  platforms: Platform[];
  accounts: Account[];
  strategies: Strategy[];
  onCreate: (pId: string, aId: string, sId: string) => void;
}

export default function CreateInstanceModal({
  open,
  onClose,
  platforms,
  accounts,
  strategies,
  onCreate,
}: CreateInstanceModalProps) {
  const [p, setP] = useState("");
  const [a, setA] = useState("");
  const [s, setS] = useState("");

  useEffect(() => {
    if (!open) {
      setP("");
      setA("");
      setS("");
    }
  }, [open]);

  const filteredAccounts = useMemo(
    () => accounts.filter(x => !p || x.platformId === p),
    [accounts, p]
  );

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="w-[560px] rounded-2xl bg-white p-6 shadow-xl">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xl font-semibold">新建运行实例</h3>
          <button
            className="px-2 py-1 rounded hover:bg-gray-100"
            onClick={onClose}
          >
            ✕
          </button>
        </div>

        <div className="space-y-4">
          {/* 平台选择 */}
          <div>
            <label className="block text-sm text-gray-600 mb-1">平台</label>
            <select
              className="w-full border rounded-lg px-3 py-2"
              value={p}
              onChange={e => setP(e.target.value)}
            >
              <option value="">选择平台</option>
              {platforms.map(pl => (
                <option key={pl.id} value={pl.id}>
                  {pl.name}
                </option>
              ))}
            </select>
          </div>

          {/* 账号选择 */}
          <div>
            <label className="block text-sm text-gray-600 mb-1">账号</label>
            <select
              className="w-full border rounded-lg px-3 py-2"
              value={a}
              onChange={e => setA(e.target.value)}
            >
              <option value="">选择账号</option>
              {filteredAccounts.map(ac => (
                <option key={ac.id} value={ac.id}>
                  {ac.name}
                </option>
              ))}
            </select>
          </div>

          {/* 策略选择 */}
          <div>
            <label className="block text-sm text-gray-600 mb-1">策略</label>
            <select
              className="w-full border rounded-lg px-3 py-2"
              value={s}
              onChange={e => setS(e.target.value)}
            >
              <option value="">选择策略</option>
              {strategies.map(st => (
                <option key={st.id} value={st.id}>
                  {st.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* 按钮 */}
        <div className="mt-6 flex items-center justify-end gap-3">
          <button className="px-4 py-2 rounded-lg border" onClick={onClose}>
            取消
          </button>
          <button
            className={cls(
              "px-4 py-2 rounded-lg text-white",
              p && a && s ? "bg-black" : "bg-gray-400 cursor-not-allowed"
            )}
            disabled={!p || !a || !s}
            onClick={() => {
              onCreate(p, a, s);
              onClose();
            }}
          >
            创建
          </button>
        </div>
      </div>
    </div>
  );
}
