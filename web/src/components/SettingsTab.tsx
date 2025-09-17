import { useState } from "react";

export default function SettingsTab() {
  const [settings, setSettings] = useState<{
    autoRestart: boolean;
    notifyOnError: boolean;
    theme: "light" | "dark";
    lang: "zh-CN" | "en-US";
    csvPrecision: number;
  }>({
    autoRestart: true,
    notifyOnError: true,
    theme: "light",
    lang: "zh-CN",
    csvPrecision: 4,
  });

  return (
    <div className="grid md:grid-cols-2 gap-4">
      {/* 运行与通知 */}
      <div className="rounded-2xl border p-4">
        <div className="text-lg font-semibold mb-3">运行与通知</div>
        <div className="space-y-3 text-sm">
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={settings.autoRestart}
              onChange={e =>
                setSettings(x => ({ ...x, autoRestart: e.target.checked }))
              }
            />
            <span>策略异常自动重启</span>
          </label>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={settings.notifyOnError}
              onChange={e =>
                setSettings(x => ({ ...x, notifyOnError: e.target.checked }))
              }
            />
            <span>错误时发送通知</span>
          </label>
        </div>
      </div>

      {/* 显示与格式 */}
      <div className="rounded-2xl border p-4">
        <div className="text-lg font-semibold mb-3">显示与格式</div>
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div>
            <label className="block text-gray-600 mb-1">主题</label>
            <select
              className="w-full border rounded-lg px-3 py-2"
              value={settings.theme}
              onChange={(e: React.ChangeEvent<HTMLSelectElement>) =>
                setSettings(x => ({ ...x, theme: e.target.value as "light" | "dark" }))
              }
            >
              <option value="light">明亮</option>
              <option value="dark">深色</option>
            </select>
          </div>
          <div>
            <label className="block text-gray-600 mb-1">语言</label>
            <select
              className="w-full border rounded-lg px-3 py-2"
              value={settings.lang}
              onChange={(e: React.ChangeEvent<HTMLSelectElement>) =>
                setSettings(x => ({ ...x, theme: e.target.value as "light" | "dark" }))
              }
            >
              <option value="zh-CN">简体中文</option>
              <option value="en-US">English</option>
            </select>
          </div>
          <div>
            <label className="block text-gray-600 mb-1">CSV 数字精度</label>
            <input
              type="number"
              className="w-full border rounded-lg px-3 py-2"
              value={settings.csvPrecision}
              onChange={e =>
                setSettings(x => ({
                  ...x,
                  csvPrecision: Number(e.target.value),
                }))
              }
            />
          </div>
        </div>
      </div>
    </div>
  );
}
