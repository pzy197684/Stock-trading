import { useState } from 'react';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "./ui/dialog";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import { Switch } from "./ui/switch";
import { Separator } from "./ui/separator";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from "./ui/alert-dialog";
import { Save, RotateCcw, RefreshCw, Trash2, LayoutTemplate } from "lucide-react";
import apiService from "../services/apiService";

// 处理浮点数精度问题
const roundToDecimals = (num: number, decimals: number = 10): number => {
  return Math.round(num * Math.pow(10, decimals)) / Math.pow(10, decimals);
};

const percentToDecimal = (percentValue: number): number => {
  return roundToDecimals(percentValue / 100, 10);
};

const decimalToPercent = (decimalValue: number): number => {
  return roundToDecimals(decimalValue * 100, 8);
};

// 安全的默认值配置 - 防止白屏
const SAFE_DEFAULTS = {
  parameters: {
    long: {
      first_qty: 0.01,
      add_ratio: 2.0,
      add_interval: 0.02,
      max_add_times: 3,
      tp_first_order: 0.01,
      tp_before_full: 0.015,
      tp_after_full: 0.02
    },
    short: {
      first_qty: 0.01,
      add_ratio: 2.0,
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
      release_tp_after_full: { long: 0.02, short: 0.02 },
      release_sl_loss_ratio: { long: 1.0, short: 1.0 }
    }
  },
  advanced: {
    symbol: 'OPUSDT',
    leverage: 5,
    mode: 'dual',
    order_type: 'MARKET',
    interval: 5,
    max_daily_loss: 100.0,
    emergency_stop_loss: 0.1
  }
};

export interface InstanceParameters {
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
  advanced?: {
    symbol: string;
    leverage: number;
    mode: string;
    order_type: string;
    interval: number;
    max_daily_loss: number;
    emergency_stop_loss: number;
    enable_logging?: boolean;
    enable_performance_monitoring?: boolean;
    enable_webhooks?: boolean;
  };
  autoTrade?: boolean;
  notifications?: boolean;
}

interface Template {
  id: string;
  name: string;
  description: string;
  parameters: InstanceParameters;
}

interface InstanceSettingsProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  instanceId: string;
  instanceName: string;
  platform: string;
  currentParameters: InstanceParameters;
  onParametersChange: (parameters: InstanceParameters) => void;
  onDeleteInstance: () => void;
}

export function InstanceSettings({
  open,
  onOpenChange,
  instanceName,
  platform,
  currentParameters,
  onParametersChange,
  onDeleteInstance
}: InstanceSettingsProps) {
  const [parameters, setParameters] = useState<InstanceParameters>(() => {
    try {
      const currentParams = (currentParameters && typeof currentParameters === 'object' ? currentParameters : {}) as Partial<InstanceParameters>;
      
      return {
        long: currentParams?.long || SAFE_DEFAULTS.parameters.long,
        short: currentParams?.short || SAFE_DEFAULTS.parameters.short,
        hedge: currentParams?.hedge || SAFE_DEFAULTS.parameters.hedge,
        autoTrade: false, // 强制默认关闭自动交易
        notifications: currentParams?.notifications ?? true,
        advanced: {
          ...SAFE_DEFAULTS.advanced,
          ...(currentParams?.advanced || {})
        }
      };
    } catch (error) {
      console.error('参数初始化失败:', error);
      return {
        long: SAFE_DEFAULTS.parameters.long,
        short: SAFE_DEFAULTS.parameters.short,
        hedge: SAFE_DEFAULTS.parameters.hedge,
        autoTrade: false,
        notifications: true,
        advanced: SAFE_DEFAULTS.advanced
      };
    }
  });

  const [activeTab, setActiveTab] = useState("parameters");
  const [loadingCurrentParams, setLoadingCurrentParams] = useState(false);
  const [templateToApply, setTemplateToApply] = useState<Template | null>(null);
  const [showTemplateConfirm, setShowTemplateConfirm] = useState(false);
  const [showAutoTradeConfirm, setShowAutoTradeConfirm] = useState(false);

  // 内置安全模板
  const templates: Template[] = [
    {
      id: "conservative",
      name: "保守型",
      description: "低风险、稳健收益的参数配置",
      parameters: {
        long: { first_qty: 0.005, add_ratio: 1.5, add_interval: 0.03, max_add_times: 2, tp_first_order: 0.015, tp_before_full: 0.02, tp_after_full: 0.025 },
        short: { first_qty: 0.005, add_ratio: 1.5, add_interval: 0.03, max_add_times: 2, tp_first_order: 0.015, tp_before_full: 0.02, tp_after_full: 0.025 },
        hedge: { trigger_loss: 0.08, equal_eps: 0.015, min_wait_seconds: 120, release_tp_after_full: { long: 0.025, short: 0.025 }, release_sl_loss_ratio: { long: 1.2, short: 1.2 } },
        autoTrade: false,
        notifications: true
      }
    },
    {
      id: "balanced",
      name: "平衡型", 
      description: "风险与收益平衡的参数配置",
      parameters: {
        long: SAFE_DEFAULTS.parameters.long,
        short: SAFE_DEFAULTS.parameters.short,
        hedge: SAFE_DEFAULTS.parameters.hedge,
        autoTrade: false,
        notifications: true
      }
    },
    {
      id: "aggressive",
      name: "激进型",
      description: "高风险、高收益的参数配置",
      parameters: {
        long: { first_qty: 0.02, add_ratio: 2.5, add_interval: 0.015, max_add_times: 4, tp_first_order: 0.008, tp_before_full: 0.012, tp_after_full: 0.018 },
        short: { first_qty: 0.02, add_ratio: 2.5, add_interval: 0.015, max_add_times: 4, tp_first_order: 0.008, tp_before_full: 0.012, tp_after_full: 0.018 },
        hedge: { trigger_loss: 0.03, equal_eps: 0.008, min_wait_seconds: 30, release_tp_after_full: { long: 0.015, short: 0.015 }, release_sl_loss_ratio: { long: 0.8, short: 0.8 } },
        autoTrade: false,
        notifications: true
      }
    }
  ];

  // 模板应用功能
  const applyTemplate = (templateId: string) => {
    const template = templates.find(t => t.id === templateId);
    if (template) {
      setTemplateToApply(template);
      setShowTemplateConfirm(true);
    }
  };

  const confirmApplyTemplate = () => {
    if (templateToApply) {
      setParameters(prev => ({
        ...prev,
        long: templateToApply.parameters.long,
        short: templateToApply.parameters.short,
        hedge: templateToApply.parameters.hedge,
        autoTrade: false,
        notifications: templateToApply.parameters.notifications ?? true
      }));
      setShowTemplateConfirm(false);
      setTemplateToApply(null);
    }
  };

  const cancelApplyTemplate = () => {
    setShowTemplateConfirm(false);
    setTemplateToApply(null);
  };

  // 简化的配置检查函数
  const checkBasicConfig = async (params: InstanceParameters): Promise<boolean> => {
    try {
      // 基本非空检查
      const hasSymbol = !!(params.advanced?.symbol);
      const hasLeverage = !!(params.advanced?.leverage && params.advanced.leverage > 0);
      const hasLong = !!(params.long && params.long.first_qty > 0);
      const hasShort = !!(params.short && params.short.first_qty > 0);
      const hasHedge = !!(params.hedge && params.hedge.trigger_loss > 0);
      
      return hasSymbol && hasLeverage && hasLong && hasShort && hasHedge;
    } catch (error) {
      console.error('配置检查失败:', error);
      return false;
    }
  };

  // 处理自动交易开关切换
  const handleAutoTradeToggle = async (checked: boolean) => {
    if (checked) {
      // 开启自动交易时进行基础检查
      const configValid = await checkBasicConfig(parameters);
      if (configValid) {
        setShowAutoTradeConfirm(true);
      } else {
        alert('配置不完整，请检查 交易对、杠杆倍数、多头参数、空头参数、对冲参数 是否设置正确！');
      }
    } else {
      // 直接关闭自动交易
      updateParameter('autoTrade', false);
    }
  };

  // 确认开启自动交易
  const confirmEnableAutoTrade = () => {
    updateParameter('autoTrade', true);
    setShowAutoTradeConfirm(false);
  };

  // 取消开启自动交易
  const cancelEnableAutoTrade = () => {
    setShowAutoTradeConfirm(false);
  };

  // 刷新当前参数 - 确保从账户特定配置获取完整参数
  const refreshCurrentTab = async () => {
    if (!instanceName || !platform) return;
    
    setLoadingCurrentParams(true);
    try {
      const result = await apiService.getInstanceParameters(instanceName);
      if (result.success && result.data?.raw_parameters) {
        const runningParams = result.data.raw_parameters;
        
        setParameters(prev => {
          const newParams = { ...prev };
          
          if (activeTab === 'parameters') {
            // 参数配置：从运行时获取策略参数
            newParams.long = runningParams.long || prev.long;
            newParams.short = runningParams.short || prev.short;
            newParams.hedge = runningParams.hedge || prev.hedge;
          } else if (activeTab === 'advanced') {
            // 高级配置：从运行时获取基础配置，确保正确映射
            const advancedFields = {
              symbol: runningParams.symbol || prev.advanced?.symbol || SAFE_DEFAULTS.advanced.symbol,
              leverage: runningParams.leverage || prev.advanced?.leverage || SAFE_DEFAULTS.advanced.leverage,
              mode: runningParams.mode || prev.advanced?.mode || SAFE_DEFAULTS.advanced.mode,
              order_type: runningParams.order_type || prev.advanced?.order_type || SAFE_DEFAULTS.advanced.order_type,
              interval: runningParams.interval || prev.advanced?.interval || SAFE_DEFAULTS.advanced.interval,
              max_daily_loss: runningParams.max_daily_loss || runningParams.risk_control?.max_daily_loss || prev.advanced?.max_daily_loss || SAFE_DEFAULTS.advanced.max_daily_loss,
              emergency_stop_loss: runningParams.emergency_stop_loss || runningParams.risk_control?.emergency_stop_loss || prev.advanced?.emergency_stop_loss || SAFE_DEFAULTS.advanced.emergency_stop_loss
            };
            
            newParams.advanced = {
              ...SAFE_DEFAULTS.advanced,
              ...prev.advanced,
              ...advancedFields
            };
          }
          
          newParams.notifications = runningParams.monitoring?.enable_alerts ?? prev.notifications;
          return newParams;
        });
      }
    } catch (error) {
      console.error('Failed to refresh parameters:', error);
    } finally {
      setLoadingCurrentParams(false);
    }
  };

  // 重置参数 - 重置到账户特定配置，而不是前端硬编码默认值
  const resetCurrentTab = async () => {
    if (activeTab === 'parameters') {
      // 重置参数配置：重新从后端获取账户特定的默认参数
      await refreshCurrentTab();
    } else if (activeTab === 'advanced') {
      // 重置高级配置：使用当前账户配置，而不是前端硬编码
      setParameters(prev => ({
        ...prev,
        advanced: {
          ...SAFE_DEFAULTS.advanced,
          // 保持账户特定的核心配置
          symbol: prev.advanced?.symbol || SAFE_DEFAULTS.advanced.symbol,
          leverage: prev.advanced?.leverage || SAFE_DEFAULTS.advanced.leverage
        }
      }));
    }
  };

  // 保存功能 - 正确处理高级配置的展平
  const saveCurrentTab = () => {
    const finalParams = {
      ...parameters,
      // 展平高级配置到顶层，保持与后端配置文件结构一致
      ...(parameters.advanced || {}),
      enable_alerts: parameters.notifications
    };
    
    // 移除嵌套的 advanced 对象，避免重复
    delete finalParams.advanced;
    
    onParametersChange(finalParams);
    onOpenChange(false);
  };

  // 参数更新辅助函数
  const updateParameter = (path: string, value: any) => {
    setParameters(prev => {
      const newParams = { ...prev };
      const keys = path.split('.');
      
      if (keys.length === 1) {
        (newParams as any)[keys[0]] = value;
      } else if (keys.length === 2) {
        if (keys[0] === 'advanced') {
          newParams.advanced = { 
            ...newParams.advanced, 
            [keys[1]]: value 
          } as typeof newParams.advanced;
        } else {
          (newParams as any)[keys[0]] = { ...(newParams as any)[keys[0]], [keys[1]]: value };
        }
      } else if (keys.length === 3) {
        // 处理嵌套对象，如 hedge.release_tp_after_full.long
        const [section, subsection, field] = keys;
        (newParams as any)[section] = {
          ...(newParams as any)[section],
          [subsection]: {
            ...((newParams as any)[section][subsection] || {}),
            [field]: value
          }
        };
      }
      
      return newParams;
    });
  };

  // 检查参数是否已初始化
  if (!parameters || !parameters.long || !parameters.short || !parameters.hedge) {
    return (
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent>
          <div className="flex items-center justify-center py-8">
            <div className="text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-2"></div>
              <p className="text-sm text-muted-foreground">正在初始化参数...</p>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    );
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
        <DialogHeader className="flex-shrink-0">
          <DialogTitle>参数设置 - {instanceName || '未知实例'}</DialogTitle>
          <DialogDescription>
            配置交易策略参数和高级设置 ({platform || '未知平台'})
          </DialogDescription>
        </DialogHeader>

        <div className="flex-1 overflow-hidden min-h-0">
          <Tabs value={activeTab} onValueChange={setActiveTab} className="h-full flex flex-col">
            <TabsList className="grid w-full grid-cols-3 flex-shrink-0">
              <TabsTrigger value="parameters">参数配置</TabsTrigger>
              <TabsTrigger value="templates">配置模板</TabsTrigger>
              <TabsTrigger value="advanced">高级配置</TabsTrigger>
            </TabsList>

            <div className="flex-1 overflow-hidden mt-6 min-h-0">
              <TabsContent value="parameters" className="h-full m-0 overflow-hidden">
                <div className="h-full overflow-y-auto pr-2 space-y-6" style={{maxHeight: 'calc(90vh - 200px)'}}>
                  {/* 多头参数 */}
                  <div className="space-y-4">
                    <h3 className="text-lg font-semibold">多头参数</h3>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label>首次开仓数量</Label>
                        <Input
                          type="number"
                          value={parameters.long.first_qty || 0}
                          onChange={(e) => updateParameter('long.first_qty', parseFloat(e.target.value) || 0)}
                          step="0.01"
                          min="0"
                        />
                      </div>
                      <div>
                        <Label>加仓倍数</Label>
                        <Input
                          type="number"
                          value={parameters.long.add_ratio || 1}
                          onChange={(e) => updateParameter('long.add_ratio', parseFloat(e.target.value) || 1)}
                          step="0.1"
                          min="1"
                        />
                      </div>
                      <div>
                        <Label>加仓间隔 (%)</Label>
                        <Input
                          type="number"
                          value={decimalToPercent(parameters.long.add_interval || 0)}
                          onChange={(e) => updateParameter('long.add_interval', percentToDecimal(parseFloat(e.target.value) || 0))}
                          step="0.1"
                          min="0.1"
                        />
                      </div>
                      <div>
                        <Label>最大加仓次数</Label>
                        <Input
                          type="number"
                          value={parameters.long.max_add_times || 0}
                          onChange={(e) => updateParameter('long.max_add_times', parseInt(e.target.value) || 0)}
                          min="0"
                        />
                      </div>
                      <div>
                        <Label>首单止盈 (%)</Label>
                        <Input
                          type="number"
                          value={decimalToPercent(parameters.long.tp_first_order || 0)}
                          onChange={(e) => updateParameter('long.tp_first_order', percentToDecimal(parseFloat(e.target.value) || 0))}
                          step="0.1"
                          min="0.1"
                        />
                      </div>
                      <div>
                        <Label>补仓前止盈 (%)</Label>
                        <Input
                          type="number"
                          value={decimalToPercent(parameters.long.tp_before_full || 0)}
                          onChange={(e) => updateParameter('long.tp_before_full', percentToDecimal(parseFloat(e.target.value) || 0))}
                          step="0.1"
                          min="0.1"
                        />
                      </div>
                      <div>
                        <Label>补仓后止盈 (%)</Label>
                        <Input
                          type="number"
                          value={decimalToPercent(parameters.long.tp_after_full || 0)}
                          onChange={(e) => updateParameter('long.tp_after_full', percentToDecimal(parseFloat(e.target.value) || 0))}
                          step="0.1"
                          min="0.1"
                        />
                      </div>
                    </div>
                  </div>

                  <Separator />

                  {/* 空头参数 */}
                  <div className="space-y-4">
                    <h3 className="text-lg font-semibold">空头参数</h3>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label>首次开仓数量</Label>
                        <Input
                          type="number"
                          value={parameters.short.first_qty || 0}
                          onChange={(e) => updateParameter('short.first_qty', parseFloat(e.target.value) || 0)}
                          step="0.01"
                          min="0"
                        />
                      </div>
                      <div>
                        <Label>加仓倍数</Label>
                        <Input
                          type="number"
                          value={parameters.short.add_ratio || 1}
                          onChange={(e) => updateParameter('short.add_ratio', parseFloat(e.target.value) || 1)}
                          step="0.1"
                          min="1"
                        />
                      </div>
                      <div>
                        <Label>加仓间隔 (%)</Label>
                        <Input
                          type="number"
                          value={decimalToPercent(parameters.short.add_interval || 0)}
                          onChange={(e) => updateParameter('short.add_interval', percentToDecimal(parseFloat(e.target.value) || 0))}
                          step="0.1"
                          min="0.1"
                        />
                      </div>
                      <div>
                        <Label>最大加仓次数</Label>
                        <Input
                          type="number"
                          value={parameters.short.max_add_times || 0}
                          onChange={(e) => updateParameter('short.max_add_times', parseInt(e.target.value) || 0)}
                          min="0"
                        />
                      </div>
                      <div>
                        <Label>首单止盈 (%)</Label>
                        <Input
                          type="number"
                          value={decimalToPercent(parameters.short.tp_first_order || 0)}
                          onChange={(e) => updateParameter('short.tp_first_order', percentToDecimal(parseFloat(e.target.value) || 0))}
                          step="0.1"
                          min="0.1"
                        />
                      </div>
                      <div>
                        <Label>补仓前止盈 (%)</Label>
                        <Input
                          type="number"
                          value={decimalToPercent(parameters.short.tp_before_full || 0)}
                          onChange={(e) => updateParameter('short.tp_before_full', percentToDecimal(parseFloat(e.target.value) || 0))}
                          step="0.1"
                          min="0.1"
                        />
                      </div>
                      <div>
                        <Label>补仓后止盈 (%)</Label>
                        <Input
                          type="number"
                          value={decimalToPercent(parameters.short.tp_after_full || 0)}
                          onChange={(e) => updateParameter('short.tp_after_full', percentToDecimal(parseFloat(e.target.value) || 0))}
                          step="0.1"
                          min="0.1"
                        />
                      </div>
                    </div>
                  </div>

                  <Separator />

                  {/* 对冲参数 */}
                  <div className="space-y-4">
                    <h3 className="text-lg font-semibold">对冲参数</h3>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label>触发对冲亏损比例 (%)</Label>
                        <Input
                          type="number"
                          value={decimalToPercent(parameters.hedge.trigger_loss || 0)}
                          onChange={(e) => updateParameter('hedge.trigger_loss', percentToDecimal(parseFloat(e.target.value) || 0))}
                          step="0.1"
                          min="0.1"
                        />
                      </div>
                      <div>
                        <Label>平衡精度</Label>
                        <Input
                          type="number"
                          value={parameters.hedge.equal_eps || 0}
                          onChange={(e) => updateParameter('hedge.equal_eps', parseFloat(e.target.value) || 0)}
                          step="0.01"
                          min="0.01"
                        />
                      </div>
                      <div>
                        <Label>最小等待时间 (秒)</Label>
                        <Input
                          type="number"
                          value={parameters.hedge.min_wait_seconds || 0}
                          onChange={(e) => updateParameter('hedge.min_wait_seconds', parseInt(e.target.value) || 0)}
                          step="1"
                          min="1"
                        />
                      </div>
                      <div className="col-span-2">
                        <h4 className="text-md font-medium mb-3">对冲释放止盈</h4>
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <Label>多头释放止盈 (%)</Label>
                            <Input
                              type="number"
                              value={decimalToPercent(parameters.hedge.release_tp_after_full?.long || 0)}
                              onChange={(e) => updateParameter('hedge.release_tp_after_full.long', percentToDecimal(parseFloat(e.target.value) || 0))}
                              step="0.1"
                              min="0.1"
                            />
                          </div>
                          <div>
                            <Label>空头释放止盈 (%)</Label>
                            <Input
                              type="number"
                              value={decimalToPercent(parameters.hedge.release_tp_after_full?.short || 0)}
                              onChange={(e) => updateParameter('hedge.release_tp_after_full.short', percentToDecimal(parseFloat(e.target.value) || 0))}
                              step="0.1"
                              min="0.1"
                            />
                          </div>
                        </div>
                      </div>
                      <div className="col-span-2">
                        <h4 className="text-md font-medium mb-3">释放止损比例</h4>
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <Label>多头止损比例</Label>
                            <Input
                              type="number"
                              value={parameters.hedge.release_sl_loss_ratio?.long || 0}
                              onChange={(e) => updateParameter('hedge.release_sl_loss_ratio.long', parseFloat(e.target.value) || 0)}
                              step="0.1"
                              min="0.1"
                            />
                          </div>
                          <div>
                            <Label>空头止损比例</Label>
                            <Input
                              type="number"
                              value={parameters.hedge.release_sl_loss_ratio?.short || 0}
                              onChange={(e) => updateParameter('hedge.release_sl_loss_ratio.short', parseFloat(e.target.value) || 0)}
                              step="0.1"
                              min="0.1"
                            />
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  <Separator />

                  {/* 消息通知和自动交易 */}
                  <div className="space-y-4">
                    <div className="flex items-center justify-between p-4 border rounded-lg">
                      <div>
                        <Label>消息通知</Label>
                        <p className="text-sm text-muted-foreground">接收交易和系统通知</p>
                      </div>
                      <Switch
                        checked={parameters.notifications || false}
                        onCheckedChange={(checked: boolean) => updateParameter('notifications', checked)}
                      />
                    </div>

                    <div className="flex items-center justify-between p-4 border rounded-lg bg-amber-50 border-amber-200">
                      <div>
                        <Label className="text-amber-800">自动交易模式</Label>
                        <p className="text-sm text-amber-600">启用后系统将自动执行交易（请谨慎开启）</p>
                      </div>
                      <Switch
                        checked={parameters.autoTrade || false}
                        onCheckedChange={handleAutoTradeToggle}
                      />
                    </div>
                  </div>
                </div>
              </TabsContent>

              <TabsContent value="templates" className="h-full m-0 overflow-hidden">
                <div className="h-full overflow-y-auto pr-2" style={{maxHeight: 'calc(90vh - 200px)'}}>
                  <div className="space-y-4">
                    {templates.map((template) => (
                      <div
                        key={template.id}
                        className="border rounded-lg p-4 hover:bg-muted/50 transition-all duration-200"
                      >
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <LayoutTemplate className="w-4 h-4" />
                            <span className="font-medium">{template.name}</span>
                          </div>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => applyTemplate(template.id)}
                          >
                            应用
                          </Button>
                        </div>
                        <p className="text-sm text-muted-foreground mb-3">{template.description}</p>
                        <div className="grid grid-cols-2 gap-2 text-xs">
                          <div>首次开仓: {template.parameters.long.first_qty}</div>
                          <div>加仓倍数: {template.parameters.long.add_ratio}x</div>
                          <div>触发对冲: {(template.parameters.hedge.trigger_loss * 100).toFixed(1)}%</div>
                          <div>加仓间隔: {(template.parameters.long.add_interval * 100).toFixed(1)}%</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </TabsContent>

              <TabsContent value="advanced" className="h-full m-0 overflow-hidden">
                <div className="h-full overflow-y-auto pr-2 space-y-6" style={{maxHeight: 'calc(90vh - 200px)'}}>
                  <div className="space-y-4">
                    <h3 className="text-lg font-semibold">交易配置</h3>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label>交易对</Label>
                        <Input
                          value={parameters.advanced?.symbol || ''}
                          onChange={(e) => updateParameter('advanced.symbol', e.target.value)}
                          placeholder="如: BTCUSDT"
                        />
                      </div>
                      <div>
                        <Label>杠杆倍数</Label>
                        <Input
                          type="number"
                          value={parameters.advanced?.leverage || 1}
                          onChange={(e) => updateParameter('advanced.leverage', parseInt(e.target.value) || 1)}
                          min="1"
                          max="100"
                        />
                      </div>
                      <div>
                        <Label>交易模式</Label>
                        <select
                          className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                          value={parameters.advanced?.mode || 'dual'}
                          onChange={(e) => updateParameter('advanced.mode', e.target.value)}
                        >
                          <option value="dual">双向持仓</option>
                          <option value="net">单向持仓</option>
                        </select>
                      </div>
                      <div>
                        <Label>订单类型</Label>
                        <select
                          className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                          value={parameters.advanced?.order_type || 'MARKET'}
                          onChange={(e) => updateParameter('advanced.order_type', e.target.value)}
                        >
                          <option value="MARKET">市价订单</option>
                          <option value="LIMIT">限价订单</option>
                        </select>
                      </div>
                      <div>
                        <Label>检查间隔 (秒)</Label>
                        <Input
                          type="number"
                          value={parameters.advanced?.interval || 5}
                          onChange={(e) => updateParameter('advanced.interval', parseInt(e.target.value) || 5)}
                          min="1"
                          max="300"
                        />
                      </div>
                    </div>
                  </div>

                  <Separator />

                  <div className="space-y-4">
                    <h3 className="text-lg font-semibold">风险控制</h3>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label>每日最大亏损 (USDT)</Label>
                        <Input
                          type="number"
                          value={parameters.advanced?.max_daily_loss || 0}
                          onChange={(e) => updateParameter('advanced.max_daily_loss', parseFloat(e.target.value) || 0)}
                          step="10"
                          min="0"
                        />
                      </div>
                      <div>
                        <Label>紧急止损比例 (%)</Label>
                        <Input
                          type="number"
                          value={decimalToPercent(parameters.advanced?.emergency_stop_loss || 0)}
                          onChange={(e) => updateParameter('advanced.emergency_stop_loss', percentToDecimal(parseFloat(e.target.value) || 0))}
                          step="1"
                          min="1"
                          max="50"
                        />
                      </div>
                    </div>
                  </div>

                  <Separator />

                  <div className="space-y-4">
                    <h3 className="text-lg font-semibold">监控设置</h3>
                    <div className="space-y-4">
                      <div className="flex items-center justify-between p-4 border rounded-lg">
                        <div>
                          <Label>启用日志记录</Label>
                          <p className="text-sm text-muted-foreground">记录详细的交易日志</p>
                        </div>
                        <Switch
                          checked={parameters.advanced?.enable_logging ?? true}
                          onCheckedChange={(checked: boolean) => updateParameter('advanced.enable_logging', checked)}
                        />
                      </div>
                      
                      <div className="flex items-center justify-between p-4 border rounded-lg">
                        <div>
                          <Label>启用性能监控</Label>
                          <p className="text-sm text-muted-foreground">监控系统性能指标</p>
                        </div>
                        <Switch
                          checked={parameters.advanced?.enable_performance_monitoring ?? true}
                          onCheckedChange={(checked: boolean) => updateParameter('advanced.enable_performance_monitoring', checked)}
                        />
                      </div>
                      
                      <div className="flex items-center justify-between p-4 border rounded-lg">
                        <div>
                          <Label>启用 Webhook 通知</Label>
                          <p className="text-sm text-muted-foreground">向外部系统发送交易通知</p>
                        </div>
                        <Switch
                          checked={parameters.advanced?.enable_webhooks ?? false}
                          onCheckedChange={(checked: boolean) => updateParameter('advanced.enable_webhooks', checked)}
                        />
                      </div>
                    </div>
                  </div>
                </div>
              </TabsContent>
            </div>
          </Tabs>
        </div>

        {/* 按钮区域 */}
        <div className="flex items-center justify-between pt-4 border-t">
          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button variant="destructive" size="sm">
                <Trash2 className="w-4 h-4 mr-2" />
                删除实例
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>确认删除实例</AlertDialogTitle>
                <AlertDialogDescription>
                  您确定要删除实例 "{instanceName}" 吗？此操作不可撤销。
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>取消</AlertDialogCancel>
                <AlertDialogAction onClick={onDeleteInstance}>
                  确认删除
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>

          <div className="flex gap-2">
            <Button 
              variant="outline" 
              onClick={refreshCurrentTab}
              disabled={!instanceName || !platform || loadingCurrentParams}
            >
              <RefreshCw className={`w-4 h-4 mr-2 ${loadingCurrentParams ? 'animate-spin' : ''}`} />
              {loadingCurrentParams ? '刷新中...' : '刷新'}
            </Button>
            
            {activeTab === 'parameters' && (
              <AlertDialog>
                <AlertDialogTrigger asChild>
                  <Button variant="outline">
                    <RotateCcw className="w-4 h-4 mr-2" />
                    重置
                  </Button>
                </AlertDialogTrigger>
                <AlertDialogContent>
                  <AlertDialogHeader>
                    <AlertDialogTitle>确认重置策略参数</AlertDialogTitle>
                    <AlertDialogDescription>
                      您确定要将策略参数重置为默认值吗？
                    </AlertDialogDescription>
                  </AlertDialogHeader>
                  <AlertDialogFooter>
                    <AlertDialogCancel>取消</AlertDialogCancel>
                    <AlertDialogAction onClick={resetCurrentTab}>
                      确认重置
                    </AlertDialogAction>
                  </AlertDialogFooter>
                </AlertDialogContent>
              </AlertDialog>
            )}

            <AlertDialog>
              <AlertDialogTrigger asChild>
                <Button>
                  <Save className="w-4 h-4 mr-2" />
                  保存设置
                </Button>
              </AlertDialogTrigger>
              <AlertDialogContent>
                <AlertDialogHeader>
                  <AlertDialogTitle>确认保存设置</AlertDialogTitle>
                  <AlertDialogDescription>
                    您确定要保存当前的参数配置吗？这将更新实例的运行参数。
                  </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                  <AlertDialogCancel>取消</AlertDialogCancel>
                  <AlertDialogAction onClick={saveCurrentTab}>
                    确认保存
                  </AlertDialogAction>
                </AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>
          </div>
        </div>

        {/* 模板应用确认对话框 */}
        <AlertDialog open={showTemplateConfirm} onOpenChange={setShowTemplateConfirm}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>确认应用模板</AlertDialogTitle>
              <AlertDialogDescription>
                您确定要应用模板 "{templateToApply?.name}" 吗？
                <br /><br />
                <span className="text-sm text-muted-foreground">
                  {templateToApply?.description}
                </span>
                <br /><br />
                <span className="text-sm font-medium text-amber-600">
                  ⚠️ 这将覆盖当前的多头、空头和对冲参数设置，自动交易模式将保持关闭
                </span>
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel onClick={cancelApplyTemplate}>取消</AlertDialogCancel>
              <AlertDialogAction onClick={confirmApplyTemplate}>
                确认应用
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>

        {/* 自动交易确认对话框 */}
        <AlertDialog open={showAutoTradeConfirm} onOpenChange={setShowAutoTradeConfirm}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle className="flex items-center gap-2 text-amber-700">
                <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
                启用自动交易确认
              </AlertDialogTitle>
              <AlertDialogDescription>
                您确定要启用自动交易模式吗？
                <br /><br />
                <span className="text-sm text-amber-600 bg-amber-50 p-3 rounded block">
                  ⚠️ 启用自动交易后，系统将根据当前策略参数自动执行交易操作。请确保已仔细检查所有参数设置，并承担相应的交易风险。
                </span>
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel onClick={cancelEnableAutoTrade}>
                取消
              </AlertDialogCancel>
              <AlertDialogAction onClick={confirmEnableAutoTrade}>
                确认启用自动交易
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </DialogContent>
    </Dialog>
  );
}