

interface SparklineProps {
  data: number[];
}

export default function Sparkline({ data }: SparklineProps) {
  const w = 200,
    h = 48,
    pad = 4;
  const min = Math.min(...data),
    max = Math.max(...data);
  const scaleX = (i: number) =>
    pad + (i * (w - 2 * pad)) / Math.max(1, data.length - 1);
  const scaleY = (v: number) =>
    pad + (h - 2 * pad) * (1 - (v - min) / Math.max(1e-9, max - min));
  const d = data
    .map((v, i) => `${i === 0 ? "M" : "L"}${scaleX(i)},${scaleY(v)}`)
    .join(" ");

  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="w-full h-12">
      <path d={d} fill="none" strokeWidth={2} stroke="currentColor" />
    </svg>
  );
}
