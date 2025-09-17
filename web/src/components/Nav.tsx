import { cls } from "../utils";

interface NavProps {
  tab: string;
  setTab: (t: string) => void;
  tabs: string[];
}

export default function Nav({ tab, setTab, tabs }: NavProps) {
  return (
    <div className="sticky top-0 z-40 bg-white/80 backdrop-blur border-b">
      <div className="mx-auto max-w-[1200px] px-4">
        <div className="flex items-center justify-between h-14">
          <div className="font-semibold">多平台多策略交易面板</div>
          <div className="flex gap-1 overflow-x-auto">
            {tabs.map(t => (
              <button
                key={t}
                onClick={() => setTab(t)}
                className={cls(
                  "px-3 py-1.5 rounded-full text-sm whitespace-nowrap",
                  tab === t ? "bg-black text-white" : "hover:bg-gray-100"
                )}
              >
                {t}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
