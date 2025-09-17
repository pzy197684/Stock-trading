import type { Strategy } from "../utils";

interface StrategyTabProps {
  strategies: Strategy[];
}

export default function StrategyTab({ strategies }: StrategyTabProps) {
  return (
    <div className="grid md:grid-cols-2 gap-4">
      {strategies.map(s => (
        <div key={s.id} className="rounded-2xl border p-4 bg-white">
          <div className="text-sm text-gray-500">ID：{s.id}</div>
          <div className="mt-1 text-lg font-semibold">{s.name}</div>
          <p className="mt-2 text-gray-700 leading-6">{s.description}</p>
        </div>
      ))}
    </div>
  );
}
