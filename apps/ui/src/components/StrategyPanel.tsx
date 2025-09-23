import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";
import { Progress } from "./ui/progress";
import { Zap, TrendingUp, BarChart3, Shuffle, Target, Shield } from "lucide-react";

interface Strategy {
  id: string;
  name: string;
  description: string;
  category: string;
  riskLevel: 'low' | 'medium' | 'high';
  profitability: number;
  complexity: number;
  marketCondition: string[];
  features: string[];
  performance: {
    winRate: number;
    avgProfit: number;
    maxDrawdown: number;
  };
}

export function StrategyPanel() {
  const strategies: Strategy[] = [
    {
      id: "grid",
      name: "网格策略",
      description: "在预设价格区间内设置买卖网格，适用于横盘震荡市场。通过低买高卖获得价差收益，同时支持多空双向网格交易。",
      category: "震荡策略",
      riskLevel: "low",
      profitability: 75,
      complexity: 60,
      marketCondition: ["横盘震荡", "低波动率"],
      features: ["双向交易", "自动止盈", "风险控制", "资金管理"],
      performance: {
        winRate: 78.5,
        avgProfit: 2.3,
        maxDrawdown: 8.2
      }
    },
    {
      id: "arbitrage",
      name: "套利策略",
      description: "利用不同交易所或交易对之间的价格差异进行套利交易。实时监控多个市场，发现套利机会时自动执行交易。",
      category: "套利策略",
      riskLevel: "medium",
      profitability: 85,
      complexity: 80,
      marketCondition: ["价格差异", "高流动性"],
      features: ["跨平台交易", "实时监控", "自动执行", "风险对冲"],
      performance: {
        winRate: 92.1,
        avgProfit: 1.8,
        maxDrawdown: 3.5
      }
    },
    {
      id: "trend",
      name: "趋势跟踪策略",
      description: "基于技术分析指标识别市场趋势，在趋势确立后进入市场，在趋势反转时退出。适用于单边行情市场。",
      category: "趋势策略",
      riskLevel: "high",
      profitability: 90,
      complexity: 70,
      marketCondition: ["单边趋势", "高波动率"],
      features: ["趋势识别", "动态止损", "仓位管理", "信号过滤"],
      performance: {
        winRate: 65.3,
        avgProfit: 4.7,
        maxDrawdown: 15.6
      }
    },
    {
      id: "scalping",
      name: "高频scalp策略",
      description: "通过大量小额快速交易获利，利用市场微小价格波动进行超短线交易。要求极低延迟和高频率执行。",
      category: "高频策略",
      riskLevel: "medium",
      profitability: 70,
      complexity: 95,
      marketCondition: ["高流动性", "微小波动"],
      features: ["高频交易", "低延迟", "快速执行", "风险分散"],
      performance: {
        winRate: 89.7,
        avgProfit: 0.8,
        maxDrawdown: 5.1
      }
    },
    {
      id: "martingale",
      name: "马丁格尔策略",
      description: "在亏损时加倍投注的策略，适用于有强势反弹预期的市场。需要充足资金和严格的风险控制措施。",
      category: "资金管理",
      riskLevel: "high",
      profitability: 60,
      complexity: 50,
      marketCondition: ["强支撑位", "反弹预期"],
      features: ["加倍投注", "风险放大", "高资金要求", "快速回本"],
      performance: {
        winRate: 45.2,
        avgProfit: 8.9,
        maxDrawdown: 35.7
      }
    },
    {
      id: "mean_reversion",
      name: "均值回归策略",
      description: "基于价格会回归其历史均值的理论，在价格偏离均值时进行反向交易。适用于波动性较大但总体稳定的市场。",
      category: "统计策略",
      riskLevel: "medium",
      profitability: 80,
      complexity: 75,
      marketCondition: ["均值回归", "稳定波动"],
      features: ["统计分析", "均值计算", "偏差检测", "回归交易"],
      performance: {
        winRate: 71.8,
        avgProfit: 3.2,
        maxDrawdown: 12.4
      }
    }
  ];

  const getRiskBadge = (risk: string) => {
    switch (risk) {
      case 'low':
        return <Badge className="bg-green-100 text-green-800 border-green-200">低风险</Badge>;
      case 'medium':
        return <Badge className="bg-yellow-100 text-yellow-800 border-yellow-200">中风险</Badge>;
      case 'high':
        return <Badge className="bg-red-100 text-red-800 border-red-200">高风险</Badge>;
      default:
        return <Badge>未知</Badge>;
    }
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case '震荡策略':
        return <BarChart3 className="w-5 h-5" />;
      case '套利策略':
        return <Shuffle className="w-5 h-5" />;
      case '趋势策略':
        return <TrendingUp className="w-5 h-5" />;
      case '高频策略':
        return <Zap className="w-5 h-5" />;
      case '资金管理':
        return <Target className="w-5 h-5" />;
      case '统计策略':
        return <Shield className="w-5 h-5" />;
      default:
        return <Zap className="w-5 h-5" />;
    }
  };

  return (
    <div className="space-y-6">
      <div className="text-sm text-muted-foreground">
        当前系统共有 {strategies.length} 个策略可用，涵盖多种市场条件和风险偏好。
      </div>

      <div className="grid gap-6">
        {strategies.map((strategy) => (
          <Card key={strategy.id} className="w-full">
            <CardHeader>
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  {getCategoryIcon(strategy.category)}
                  <div>
                    <CardTitle className="text-xl">{strategy.name}</CardTitle>
                    <p className="text-sm text-muted-foreground mt-1">{strategy.category}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {getRiskBadge(strategy.riskLevel)}
                </div>
              </div>
            </CardHeader>
            
            <CardContent className="space-y-6">
              {/* Description */}
              <div>
                <h4 className="font-medium mb-2">策略描述</h4>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  {strategy.description}
                </p>
              </div>

              {/* Performance Metrics */}
              <div className="grid grid-cols-3 gap-4">
                <div className="text-center p-3 bg-muted/50 rounded-lg">
                  <div className="text-2xl font-bold text-green-600">{strategy.performance.winRate}%</div>
                  <div className="text-xs text-muted-foreground">胜率</div>
                </div>
                <div className="text-center p-3 bg-muted/50 rounded-lg">
                  <div className="text-2xl font-bold text-blue-600">{strategy.performance.avgProfit}%</div>
                  <div className="text-xs text-muted-foreground">平均收益</div>
                </div>
                <div className="text-center p-3 bg-muted/50 rounded-lg">
                  <div className="text-2xl font-bold text-red-600">{strategy.performance.maxDrawdown}%</div>
                  <div className="text-xs text-muted-foreground">最大回撤</div>
                </div>
              </div>

              {/* Strategy Metrics */}
              <div className="grid grid-cols-2 gap-6">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium">盈利能力</span>
                    <span className="text-sm text-muted-foreground">{strategy.profitability}%</span>
                  </div>
                  <Progress value={strategy.profitability} className="h-2" />
                </div>
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium">策略复杂度</span>
                    <span className="text-sm text-muted-foreground">{strategy.complexity}%</span>
                  </div>
                  <Progress value={strategy.complexity} className="h-2" />
                </div>
              </div>

              {/* Market Conditions and Features */}
              <div className="grid grid-cols-2 gap-6">
                <div>
                  <h4 className="font-medium mb-2">适用市场条件</h4>
                  <div className="flex flex-wrap gap-2">
                    {strategy.marketCondition.map((condition, index) => (
                      <Badge key={index} variant="outline" className="text-xs">
                        {condition}
                      </Badge>
                    ))}
                  </div>
                </div>
                <div>
                  <h4 className="font-medium mb-2">核心功能</h4>
                  <div className="flex flex-wrap gap-2">
                    {strategy.features.map((feature, index) => (
                      <Badge key={index} variant="secondary" className="text-xs">
                        {feature}
                      </Badge>
                    ))}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}