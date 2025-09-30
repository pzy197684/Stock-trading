import { useState, useEffect } from 'react';
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
  // API数据状态
  const [apiStrategies, setApiStrategies] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);

  // 从API获取策略列表
  const fetchStrategies = async () => {
    try {
      setIsLoading(true);
      setApiError(null);
      const response = await fetch('http://localhost:8001/api/strategies/available');
      if (!response.ok) {
        throw new Error(`API错误: ${response.status}`);
      }
      const data = await response.json();
      setApiStrategies(data.strategies || []);
    } catch (error) {
      console.error('获取策略列表失败:', error);
      setApiError('无法连接到API服务器');
    } finally {
      setIsLoading(false);
    }
  };

  // 初始化数据
  useEffect(() => {
    fetchStrategies();
  }, []);

  // 直接使用API数据
  const displayStrategies = apiStrategies.map((apiStrategy: any) => ({
    id: apiStrategy.id,
    name: apiStrategy.name,
    description: apiStrategy.description || "暂无描述",
    category: mapCategory(apiStrategy.category),
    riskLevel: apiStrategy.risk_level as 'low' | 'medium' | 'high',
    profitability: calculateProfitability(apiStrategy.performance_metrics),
    complexity: calculateComplexity(apiStrategy.param_schema),
    marketCondition: extractMarketConditions(apiStrategy.performance_metrics),
    features: extractFeatures(apiStrategy.capabilities, apiStrategy.default_params),
    performance: {
      winRate: parseFloat(apiStrategy.performance_metrics?.win_rate?.replace('%', '') || '0'),
      avgProfit: parseFloat(apiStrategy.performance_metrics?.expected_return?.replace('%', '') || '0'),
      maxDrawdown: parseFloat(apiStrategy.performance_metrics?.expected_drawdown?.split('-')[1]?.replace('%', '') || '0')
    }
  }));

  // Helper functions to transform API data
  function mapCategory(category: string): string {
    const categoryMap: { [key: string]: string } = {
      'grid_trading': '网格策略',
      'arbitrage': '套利策略', 
      'trend_following': '趋势策略',
      'scalping': '高频策略',
      'martingale': '资金管理',
      'mean_reversion': '统计策略'
    };
    return categoryMap[category] || '其他策略';
  }

  function calculateProfitability(metrics: any): number {
    if (!metrics) return 50;
    // Base calculation on capital requirement and market suitability
    const capitalReq = metrics.capital_requirement;
    if (capitalReq === 'low') return 85;
    if (capitalReq === 'medium') return 70;
    if (capitalReq === 'high') return 60;
    return 50;
  }

  function calculateComplexity(schema: any): number {
    if (!schema?.properties) return 50;
    const paramCount = Object.keys(schema.properties).length;
    return Math.min(95, 30 + paramCount * 8); // More params = more complex
  }

  function extractMarketConditions(metrics: any): string[] {
    if (!metrics) return ['通用市场'];
    const conditions = [];
    if (metrics.suitable_market) {
      conditions.push(metrics.suitable_market);
    }
    return conditions.length > 0 ? conditions : ['通用市场'];
  }

  function extractFeatures(capabilities: any, params: any): string[] {
    const features = [];
    if (params?.hedge_enabled) features.push('对冲交易');
    if (params?.auto_restart) features.push('自动重启');
    if (params?.stop_loss_ratio) features.push('止损保护');
    if (params?.take_profit_ratio) features.push('自动止盈');
    if (params?.grid_gap) features.push('网格交易');
    if (params?.max_position_size) features.push('仓位控制');
    return features.length > 0 ? features : ['基础交易'];
  }
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
      {/* 加载状态和错误显示 */}
      {isLoading && (
        <div className="text-center text-muted-foreground py-4">
          正在加载策略列表...
        </div>
      )}
      {apiError && (
        <div className="text-sm text-amber-600 bg-amber-50 p-3 rounded border">
          ⚠️ {apiError}
        </div>
      )}
      
      <div className="text-sm text-muted-foreground">
        当前系统共有 {displayStrategies.length} 个策略可用，涵盖多种市场条件和风险偏好。
        {apiStrategies.length > 0 && (
          <div className="mt-2 space-y-1">
            <div>API策略: {apiStrategies.map((s: any) => s.name || s.id).join(', ')}</div>
            <div>支持的平台: {[...new Set(apiStrategies.flatMap((s: any) => s.supported_platforms || []))].join(', ')}</div>
          </div>
        )}
      </div>

      <div className="grid gap-6">
        {displayStrategies.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-muted-foreground">
              {isLoading ? "正在加载策略..." : "暂无可用策略"}
            </div>
          </div>
        ) : (
          displayStrategies.map((strategy) => (
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
        )))}
      </div>
    </div>
  );
}