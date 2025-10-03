import { useState, useEffect } from 'react';
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import { Separator } from "./ui/separator";
import { useToast } from "./ui/toast";
import { Save, RotateCcw } from "lucide-react";

export interface InstanceParameters {
  symbol: string;
  leverage: number;
  mode: string;
  order_type: string;
  interval: number;
  long: {
    first_qty: number;
    add_ratio: number;
    add_interval: number;
    max_add_times: number;
    tp_first_order: number;
    tp_before_full: number;
    tp_after_full: number;
  };
  short: {
    first_qty: number;
    add_ratio: number;
    add_interval: number;
    max_add_times: number;
    tp_first_order: number;
    tp_before_full: number;
    tp_after_full: number;
  };
  hedge: {
    trigger_loss: number;
    equal_eps: number;
    min_wait_seconds: number;
    release_tp_after_full: {
      long: number;
      short: number;
    };
    release_sl_loss_ratio: {
      long: number;
      short: number;
    };
  };
  risk_control: {
    max_daily_loss: number;
    emergency_stop_loss: number;
    max_total_qty: number;
    tp_slippage: number;
  };
}

interface InstanceSettingsProps {
  instance: any;
  onSave: (parameters: InstanceParameters) => void;
  onCancel: () => void;
}

const DEFAULT_PARAMETERS: InstanceParameters = {
  symbol: "OPUSDT",
  leverage: 5,
  mode: "dual",
  order_type: "MARKET",
  interval: 5,
  long: {
    first_qty: 1,
    add_ratio: 2,
    add_interval: 0.02,
    max_add_times: 3,
    tp_first_order: 0.01,
    tp_before_full: 0.015,
    tp_after_full: 0.02
  },
  short: {
    first_qty: 1,
    add_ratio: 2,
    add_interval: 0.02,
    max_add_times: 3,
    tp_first_order: 0.01,
    tp_before_full: 0.015,
    tp_after_full: 0.02
  },
  hedge: {
    trigger_loss: 0.05,
    equal_eps: 0.01,
    min_wait_seconds: 60,
    release_tp_after_full: {
      long: 0.02,
      short: 0.02
    },
    release_sl_loss_ratio: {
      long: 1,
      short: 1
    }
  },
  risk_control: {
    max_daily_loss: 100,
    emergency_stop_loss: 0.1,
    max_total_qty: 0.5,
    tp_slippage: 0.002
  }
};

export function InstanceSettings({ instance, onSave, onCancel }: InstanceSettingsProps) {
  const [parameters, setParameters] = useState<InstanceParameters>(DEFAULT_PARAMETERS);
  const [isLoading, setIsLoading] = useState(false);
  const { toast } = useToast();

  // 初始化参数
  useEffect(() => {
    if (instance && instance.parameters) {
      // 合并实例参数和默认参数
      const merged = {
        ...DEFAULT_PARAMETERS,
        ...instance.parameters,
        long: {
          ...DEFAULT_PARAMETERS.long,
          ...(instance.parameters.long || {})
        },
        short: {
          ...DEFAULT_PARAMETERS.short,
          ...(instance.parameters.short || {})
        },
        hedge: {
          ...DEFAULT_PARAMETERS.hedge,
          ...(instance.parameters.hedge || {}),
          release_tp_after_full: {
            ...DEFAULT_PARAMETERS.hedge.release_tp_after_full,
            ...(instance.parameters.hedge?.release_tp_after_full || {})
          },
          release_sl_loss_ratio: {
            ...DEFAULT_PARAMETERS.hedge.release_sl_loss_ratio,
            ...(instance.parameters.hedge?.release_sl_loss_ratio || {})
          }
        },
        risk_control: {
          ...DEFAULT_PARAMETERS.risk_control,
          ...(instance.parameters.risk_control || {})
        }
      };
      setParameters(merged);
    }
  }, [instance]);

  // 验证参数
  const validateParameters = (): string[] => {
    const errors: string[] = [];

    // 基础参数验证
    if (!parameters.leverage || parameters.leverage <= 0) {
      errors.push("杠杆倍数必须大于0");
    }

    // 多头参数验证
    if (!parameters.long.first_qty || parameters.long.first_qty <= 0) {
      errors.push("多头首次数量必须大于0");
    }
    if (!parameters.long.add_ratio || parameters.long.add_ratio <= 0) {
      errors.push("多头加仓比例必须大于0");
    }
    if (!parameters.long.add_interval || parameters.long.add_interval <= 0) {
      errors.push("多头加仓间隔必须大于0");
    }

    // 空头参数验证
    if (!parameters.short.first_qty || parameters.short.first_qty <= 0) {
      errors.push("空头首次数量必须大于0");
    }
    if (!parameters.short.add_ratio || parameters.short.add_ratio <= 0) {
      errors.push("空头加仓比例必须大于0");
    }
    if (!parameters.short.add_interval || parameters.short.add_interval <= 0) {
      errors.push("空头加仓间隔必须大于0");
    }

    // 对冲参数验证
    if (!parameters.hedge.trigger_loss || parameters.hedge.trigger_loss <= 0) {
      errors.push("对冲触发亏损必须大于0");
    }
    if (!parameters.hedge.min_wait_seconds || parameters.hedge.min_wait_seconds <= 0) {
      errors.push("最小等待时间必须大于0");
    }

    // 风控参数验证
    if (!parameters.risk_control.max_daily_loss || parameters.risk_control.max_daily_loss <= 0) {
      errors.push("每日最大亏损必须大于0");
    }

    return errors;
  };

  // 处理保存
  const handleSave = () => {
    const errors = validateParameters();
    if (errors.length > 0) {
      toast({
        type: "error",
        title: "参数验证失败",
        description: errors.join("; ")
      });
      return;
    }

    onSave(parameters);
  };

  // 重置参数
  const handleReset = () => {
    setParameters(DEFAULT_PARAMETERS);
    toast({
      type: "info",
      title: "参数已重置",
      description: "已恢复为默认参数"
    });
  };

  // 更新参数的辅助函数
  const updateParameter = (path: string, value: number | string) => {
    setParameters(prev => {
      const newParams = { ...prev };
      const keys = path.split('.');
      let current: any = newParams;
      
      for (let i = 0; i < keys.length - 1; i++) {
        current = current[keys[i]];
      }
      
      current[keys[keys.length - 1]] = typeof value === 'string' ? parseFloat(value) || 0 : value;
      return newParams;
    });
  };

  return (
    <div className="space-y-6">
      <Tabs defaultValue="basic" className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="basic">基础设置</TabsTrigger>
          <TabsTrigger value="long">多头配置</TabsTrigger>
          <TabsTrigger value="short">空头配置</TabsTrigger>
          <TabsTrigger value="hedge">对冲&风控</TabsTrigger>
        </TabsList>

        <TabsContent value="basic" className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="symbol">交易对</Label>
              <Input
                id="symbol"
                value={parameters.symbol}
                onChange={(e) => updateParameter('symbol', e.target.value)}
                placeholder="OPUSDT"
              />
            </div>
            <div>
              <Label htmlFor="leverage">杠杆倍数</Label>
              <Input
                id="leverage"
                type="number"
                value={parameters.leverage}
                onChange={(e) => updateParameter('leverage', e.target.value)}
                min="1"
                max="125"
              />
            </div>
            <div>
              <Label htmlFor="interval">执行间隔(秒)</Label>
              <Input
                id="interval"
                type="number"
                value={parameters.interval}
                onChange={(e) => updateParameter('interval', e.target.value)}
                min="1"
              />
            </div>
            <div>
              <Label htmlFor="order_type">订单类型</Label>
              <Input
                id="order_type"
                value={parameters.order_type}
                onChange={(e) => updateParameter('order_type', e.target.value)}
                placeholder="MARKET"
              />
            </div>
          </div>
        </TabsContent>

        <TabsContent value="long" className="space-y-4">
          <h3 className="text-lg font-semibold">多头策略配置</h3>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="long_first_qty">首次数量</Label>
              <Input
                id="long_first_qty"
                type="number"
                value={parameters.long.first_qty}
                onChange={(e) => updateParameter('long.first_qty', e.target.value)}
                min="0"
                step="0.001"
              />
            </div>
            <div>
              <Label htmlFor="long_add_ratio">加仓比例</Label>
              <Input
                id="long_add_ratio"
                type="number"
                value={parameters.long.add_ratio}
                onChange={(e) => updateParameter('long.add_ratio', e.target.value)}
                min="1"
                step="0.1"
              />
            </div>
            <div>
              <Label htmlFor="long_add_interval">加仓间隔</Label>
              <Input
                id="long_add_interval"
                type="number"
                value={parameters.long.add_interval}
                onChange={(e) => updateParameter('long.add_interval', e.target.value)}
                min="0"
                step="0.001"
              />
            </div>
            <div>
              <Label htmlFor="long_max_add_times">最大加仓次数</Label>
              <Input
                id="long_max_add_times"
                type="number"
                value={parameters.long.max_add_times}
                onChange={(e) => updateParameter('long.max_add_times', e.target.value)}
                min="0"
              />
            </div>
            <div>
              <Label htmlFor="long_tp_first_order">首单止盈</Label>
              <Input
                id="long_tp_first_order"
                type="number"
                value={parameters.long.tp_first_order}
                onChange={(e) => updateParameter('long.tp_first_order', e.target.value)}
                min="0"
                step="0.001"
              />
            </div>
            <div>
              <Label htmlFor="long_tp_before_full">满仓前止盈</Label>
              <Input
                id="long_tp_before_full"
                type="number"
                value={parameters.long.tp_before_full}
                onChange={(e) => updateParameter('long.tp_before_full', e.target.value)}
                min="0"
                step="0.001"
              />
            </div>
            <div>
              <Label htmlFor="long_tp_after_full">满仓后止盈</Label>
              <Input
                id="long_tp_after_full"
                type="number"
                value={parameters.long.tp_after_full}
                onChange={(e) => updateParameter('long.tp_after_full', e.target.value)}
                min="0"
                step="0.001"
              />
            </div>
          </div>
        </TabsContent>

        <TabsContent value="short" className="space-y-4">
          <h3 className="text-lg font-semibold">空头策略配置</h3>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="short_first_qty">首次数量</Label>
              <Input
                id="short_first_qty"
                type="number"
                value={parameters.short.first_qty}
                onChange={(e) => updateParameter('short.first_qty', e.target.value)}
                min="0"
                step="0.001"
              />
            </div>
            <div>
              <Label htmlFor="short_add_ratio">加仓比例</Label>
              <Input
                id="short_add_ratio"
                type="number"
                value={parameters.short.add_ratio}
                onChange={(e) => updateParameter('short.add_ratio', e.target.value)}
                min="1"
                step="0.1"
              />
            </div>
            <div>
              <Label htmlFor="short_add_interval">加仓间隔</Label>
              <Input
                id="short_add_interval"
                type="number"
                value={parameters.short.add_interval}
                onChange={(e) => updateParameter('short.add_interval', e.target.value)}
                min="0"
                step="0.001"
              />
            </div>
            <div>
              <Label htmlFor="short_max_add_times">最大加仓次数</Label>
              <Input
                id="short_max_add_times"
                type="number"
                value={parameters.short.max_add_times}
                onChange={(e) => updateParameter('short.max_add_times', e.target.value)}
                min="0"
              />
            </div>
            <div>
              <Label htmlFor="short_tp_first_order">首单止盈</Label>
              <Input
                id="short_tp_first_order"
                type="number"
                value={parameters.short.tp_first_order}
                onChange={(e) => updateParameter('short.tp_first_order', e.target.value)}
                min="0"
                step="0.001"
              />
            </div>
            <div>
              <Label htmlFor="short_tp_before_full">满仓前止盈</Label>
              <Input
                id="short_tp_before_full"
                type="number"
                value={parameters.short.tp_before_full}
                onChange={(e) => updateParameter('short.tp_before_full', e.target.value)}
                min="0"
                step="0.001"
              />
            </div>
            <div>
              <Label htmlFor="short_tp_after_full">满仓后止盈</Label>
              <Input
                id="short_tp_after_full"
                type="number"
                value={parameters.short.tp_after_full}
                onChange={(e) => updateParameter('short.tp_after_full', e.target.value)}
                min="0"
                step="0.001"
              />
            </div>
          </div>
        </TabsContent>

        <TabsContent value="hedge" className="space-y-4">
          <h3 className="text-lg font-semibold">对冲与风控配置</h3>
          <Separator />
          
          <div className="space-y-4">
            <h4 className="text-md font-medium">对冲设置</h4>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="trigger_loss">触发亏损比例</Label>
                <Input
                  id="trigger_loss"
                  type="number"
                  value={parameters.hedge.trigger_loss}
                  onChange={(e) => updateParameter('hedge.trigger_loss', e.target.value)}
                  min="0"
                  step="0.001"
                />
              </div>
              <div>
                <Label htmlFor="equal_eps">平衡误差</Label>
                <Input
                  id="equal_eps"
                  type="number"
                  value={parameters.hedge.equal_eps}
                  onChange={(e) => updateParameter('hedge.equal_eps', e.target.value)}
                  min="0"
                  step="0.001"
                />
              </div>
              <div>
                <Label htmlFor="min_wait_seconds">最小等待时间(秒)</Label>
                <Input
                  id="min_wait_seconds"
                  type="number"
                  value={parameters.hedge.min_wait_seconds}
                  onChange={(e) => updateParameter('hedge.min_wait_seconds', e.target.value)}
                  min="0"
                />
              </div>
            </div>
          </div>

          <Separator />
          
          <div className="space-y-4">
            <h4 className="text-md font-medium">风控设置</h4>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="max_daily_loss">每日最大亏损</Label>
                <Input
                  id="max_daily_loss"
                  type="number"
                  value={parameters.risk_control.max_daily_loss}
                  onChange={(e) => updateParameter('risk_control.max_daily_loss', e.target.value)}
                  min="0"
                />
              </div>
              <div>
                <Label htmlFor="emergency_stop_loss">紧急止损比例</Label>
                <Input
                  id="emergency_stop_loss"
                  type="number"
                  value={parameters.risk_control.emergency_stop_loss}
                  onChange={(e) => updateParameter('risk_control.emergency_stop_loss', e.target.value)}
                  min="0"
                  step="0.001"
                />
              </div>
              <div>
                <Label htmlFor="max_total_qty">最大总数量</Label>
                <Input
                  id="max_total_qty"
                  type="number"
                  value={parameters.risk_control.max_total_qty}
                  onChange={(e) => updateParameter('risk_control.max_total_qty', e.target.value)}
                  min="0"
                  step="0.001"
                />
              </div>
              <div>
                <Label htmlFor="tp_slippage">止盈滑点</Label>
                <Input
                  id="tp_slippage"
                  type="number"
                  value={parameters.risk_control.tp_slippage}
                  onChange={(e) => updateParameter('risk_control.tp_slippage', e.target.value)}
                  min="0"
                  step="0.0001"
                />
              </div>
            </div>
          </div>
        </TabsContent>
      </Tabs>

      <div className="flex justify-between pt-4 border-t">
        <div className="flex gap-2">
          <Button variant="outline" onClick={handleReset}>
            <RotateCcw className="w-4 h-4 mr-2" />
            重置
          </Button>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={onCancel}>
            取消
          </Button>
          <Button onClick={handleSave} disabled={isLoading}>
            <Save className="w-4 h-4 mr-2" />
            {isLoading ? "保存中..." : "保存设置"}
          </Button>
        </div>
      </div>
    </div>
  );
}