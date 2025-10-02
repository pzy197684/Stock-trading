// 策略名称映射
export const strategyNameMap: Record<string, string> = {
  'martingale_hedge': '马丁对冲策略',
  'recovery': '回撤恢复策略',
  // 可以在这里添加更多策略的中文名称映射
};

// 获取策略的显示名称
export function getStrategyDisplayName(strategyId: string): string {
  return strategyNameMap[strategyId] || strategyId;
}

// 统一处理带版本号的策略名称
export function normalizeStrategyName(name: string): string {
  // 处理 v3, v3.0 等版本标注，统一显示为基础名称
  return name
    .replace(/\s*v?\d+(\.\d+)?\s*$/i, '') // 移除版本号 v3, v3.0, 3.0 等
    .replace(/\s*\(.*?\)\s*/g, '') // 移除括号内容
    .trim();
}