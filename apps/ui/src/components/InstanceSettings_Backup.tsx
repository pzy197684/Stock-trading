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

// 安全的默认值配置 - 不依赖外部导入，防止白屏
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
    emergency_stop_loss: 0.1,
    max_total_qty: 0.5,
    tp_slippage: 0.002,
    max_slippage: 0.001,
    retry_attempts: 3,
    order_timeout: 30,
    enable_order_confirmation: true,
    enable_logging: true,
    enable_alerts: true,
    log_level: 'INFO',
    require_manual_start: true,
    auto_stop_on_error: true,
    max_consecutive_losses: 5,
    circuit_breaker_enabled: true,
    circuit_breaker_max_drawdown: 0.08
  }
};

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

export interface InstanceParameters {
  // 多头参数
  long: {
    first_qty: number;
    add_ratio: number;
    add_interval: number;
    max_add_times: number;
    tp_first_order: number;
    tp_before_full: number;
    tp_after_full: number;
  };
  // 空头参数
  short: {
    first_qty: number;
    add_ratio: number;
    add_interval: number;
    max_add_times: number;
    tp_first_order: number;
    tp_before_full: number;
    tp_after_full: number;
  };
  // 对冲参数
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
  // 高级配置参数
  advanced?: {
    symbol: string;
    leverage: number;
    mode: string;
    order_type: string;
    interval: number;
    max_daily_loss: number;
    emergency_stop_loss: number;
    max_total_qty: number;
    tp_slippage: number;
    max_slippage: number;
    retry_attempts: number;
    order_timeout: number;
    enable_order_confirmation: boolean;
    enable_logging: boolean;
    enable_alerts: boolean;
    log_level: string;
    require_manual_start: boolean;
    auto_stop_on_error: boolean;
    max_consecutive_losses: number;
    circuit_breaker_enabled: boolean;
    circuit_breaker_max_drawdown: number;
  };
  // 兼容性字段
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
  // 安全的参数初始化，确保自动交易默认关闭，防止白屏
  const [parameters, setParameters] = useState<InstanceParameters>(() => {
    try {
      // 安全检查当前参数，使用类型断言
      const currentParams = (currentParameters && typeof currentParameters === 'object' ? currentParameters : {}) as Partial<InstanceParameters>;
      
      // 使用安全的内置默认值，避免外部依赖导致白屏
      const configDefaults = {
        long: SAFE_DEFAULTS.parameters.long,
        short: SAFE_DEFAULTS.parameters.short,
        hedge: SAFE_DEFAULTS.parameters.hedge,
        advanced: SAFE_DEFAULTS.advanced
      };

      return {
        long: currentParams?.long || configDefaults.long,
        short: currentParams?.short || configDefaults.short,
        hedge: currentParams?.hedge || configDefaults.hedge,
        autoTrade: false, // 强制默认关闭自动交易
        notifications: currentParams?.notifications ?? true,
        advanced: {
          ...configDefaults.advanced,
          ...(currentParams?.advanced || {})
        }
      };
    } catch (error) {
      console.error('参数初始化失败:', error);
      // 最安全的退回方案
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

  // 内置安全模板，避免异步加载导致的问题
  const templates: Template[] = [
    {
      id: "conservative",
      name: "保守型",
      description: "低风险、稳健收益的参数配置",
      parameters: {
        long: {
          first_qty: 0.005,
          add_ratio: 1.5,
          add_interval: 0.03,
          max_add_times: 2,
          tp_first_order: 0.015,
          tp_before_full: 0.02,
          tp_after_full: 0.025
        },
        short: {
          first_qty: 0.005,
          add_ratio: 1.5,
          add_interval: 0.03,
          max_add_times: 2,
          tp_first_order: 0.015,
          tp_before_full: 0.02,
          tp_after_full: 0.025
        },
        hedge: {
          trigger_loss: 0.08,
          equal_eps: 0.015,
          min_wait_seconds: 120,
          release_tp_after_full: { long: 0.025, short: 0.025 },
          release_sl_loss_ratio: { long: 1.2, short: 1.2 }
        },
        autoTrade: false,
        notifications: true
      }
    },
    {
      id: "balanced",
      name: "平衡型", 
      description: "风险与收益平衡的参数配置",
      parameters: {
        long: {
          first_qty: 0.01,
          add_ratio: 2,
          add_interval: 0.02,
          max_add_times: 3,
          tp_first_order: 0.01,
          tp_before_full: 0.015,
          tp_after_full: 0.02
        },
        short: {
          first_qty: 0.01,
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
          release_tp_after_full: { long: 0.02, short: 0.02 },
          release_sl_loss_ratio: { long: 1, short: 1 }
        },
        autoTrade: false,
        notifications: true
      }
    },
    {
      id: "aggressive",
      name: "激进型",
      description: "高风险、高收益的参数配置",
      parameters: {
        long: {
          first_qty: 0.02,
          add_ratio: 2.5,
          add_interval: 0.015,
          max_add_times: 4,
          tp_first_order: 0.008,
          tp_before_full: 0.012,
          tp_after_full: 0.018
        },
        short: {
          first_qty: 0.02,
          add_ratio: 2.5,
          add_interval: 0.015,
          max_add_times: 4,
          tp_first_order: 0.008,
          tp_before_full: 0.012,
          tp_after_full: 0.018
        },
        hedge: {
          trigger_loss: 0.03,
          equal_eps: 0.008,
          min_wait_seconds: 30,
          release_tp_after_full: { long: 0.015, short: 0.015 },
          release_sl_loss_ratio: { long: 0.8, short: 0.8 }
        },
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
        autoTrade: false, // 模板应用后仍然关闭自动交易
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

  // 根据当前标签页刷新对应参数
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
            // 参数配置标签页：只刷新策略参数
            newParams.long = runningParams.long || parameters.long;
            newParams.short = runningParams.short || parameters.short;
            newParams.hedge = runningParams.hedge || parameters.hedge;
          } else if (activeTab === 'advanced') {
            // 高级配置标签页：刷新高级参数
            newParams.advanced = {
              ...prev.advanced,
              ...runningParams.risk_control,
              ...runningParams.execution,
              ...runningParams.monitoring,
              ...runningParams.safety,
              symbol: runningParams.symbol ?? prev.advanced?.symbol,
              leverage: runningParams.leverage ?? prev.advanced?.leverage,
              mode: runningParams.mode ?? prev.advanced?.mode,
              order_type: runningParams.order_type ?? prev.advanced?.order_type,
              interval: runningParams.interval ?? prev.advanced?.interval
            };
          }
          
          // 通知设置统一刷新，但保持自动交易关闭
          newParams.notifications = runningParams.monitoring?.enable_alerts ?? prev.notifications;
          // 不刷新 autoTrade，保持用户当前设置
          
          return newParams;
        });
      }
    } catch (error) {
      console.error('Failed to refresh parameters:', error);
    } finally {
      setLoadingCurrentParams(false);
    }
  };

  // 根据当前标签页重置对应参数
  const resetCurrentTab = () => {
    setParameters(prev => {
      const newParams = { ...prev };
      
      if (activeTab === 'parameters') {
        // 参数配置标签页：重置策略参数为默认值
        newParams.long = SAFE_DEFAULTS.parameters.long;
        newParams.short = SAFE_DEFAULTS.parameters.short;
        newParams.hedge = SAFE_DEFAULTS.parameters.hedge;
        newParams.autoTrade = false;
      }
      
      return newParams;
    });
  };

  // 统一的保存功能
  const saveCurrentTab = () => {
    // 统一处理notifications和enable_alerts的同步
    const finalParams = {
      long: parameters.long,
      short: parameters.short,
      hedge: parameters.hedge,
      autoTrade: parameters.autoTrade,
      notifications: parameters.notifications,
      ...parameters.advanced,
      // 确保notifications和enable_alerts保持同步
      enable_alerts: parameters.notifications
    };
    
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
      }
      
      return newParams;
    });
  };

  // 根据不同标签页返回不同的按钮组合
  const renderActionButtons = () => {
    const deleteButton = (
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
    );

    const refreshButton = (
      <Button 
        variant="outline" 
        onClick={refreshCurrentTab}
        disabled={!instanceName || !platform || loadingCurrentParams}
      >
        <RefreshCw className={`w-4 h-4 mr-2 ${loadingCurrentParams ? 'animate-spin' : ''}`} />
        {loadingCurrentParams ? '刷新中...' : '刷新'}
      </Button>
    );

    const saveButton = (
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
    );

    if (activeTab === 'parameters') {
      // 参数配置：删除实例、刷新、重置、保存设置
      return (
        <div className="flex items-center justify-between pt-4 border-t">
          {deleteButton}
          <div className="flex gap-2">
            {refreshButton}
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
            {saveButton}
          </div>
        </div>
      );
    } else if (activeTab === 'templates') {
      // 配置模板：删除实例、刷新、保存设置（不需要重置）
      return (
        <div className="flex items-center justify-between pt-4 border-t">
          {deleteButton}
          <div className="flex gap-2">
            {refreshButton}
            {saveButton}
          </div>
        </div>
      );
    } else {
      // 高级设置：删除实例、刷新、保存设置（不需要重置）
      return (
        <div className="flex items-center justify-between pt-4 border-t">
          {deleteButton}
          <div className="flex gap-2">
            {refreshButton}
            {saveButton}
          </div>
        </div>
      );
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle>参数设置 - {instanceName || '未知实例'}</DialogTitle>
          <DialogDescription>
            配置交易策略参数和高级设置 ({platform || '未知平台'})
          </DialogDescription>
        </DialogHeader>

        {/* 额外的安全检查，确保参数已正确初始化 */}
        {!parameters?.long || !parameters?.short || !parameters?.hedge ? (
          <div className="flex items-center justify-center py-8">
            <div className="text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-2"></div>
              <p className="text-sm text-muted-foreground">正在初始化参数...</p>
            </div>
          </div>
        ) : (
        <div className="flex-1 overflow-hidden">
          <Tabs value={activeTab} onValueChange={setActiveTab} className="h-full flex flex-col">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="parameters">参数配置</TabsTrigger>
              <TabsTrigger value="templates">配置模板</TabsTrigger>
              <TabsTrigger value="advanced">高级配置</TabsTrigger>
            </TabsList>

            <div className="flex-1 overflow-hidden mt-6">
              <TabsContent value="parameters" className="h-full m-0">
                <div className="h-full overflow-y-auto pr-2 space-y-6">
                  {/* 多头参数 */}
                  <div className="space-y-4">
                    <h3 className="text-lg font-semibold">多头参数</h3>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label>首次开仓数量</Label>
                        <Input
                          type="number"
                          value={parameters.long.first_qty}
                          onChange={(e) => updateParameter('long.first_qty', parseFloat(e.target.value))}
                          step="0.01"
                          min="0"
                        />
                      </div>
                      <div>
                        <Label>加仓倍数</Label>
                        <Input
                          type="number"
                          value={parameters.long.add_ratio}
                          onChange={(e) => updateParameter('long.add_ratio', parseFloat(e.target.value))}
                          step="0.1"
                          min="1"
                        />
                      </div>
                      <div>
                        <Label>加仓间隔 (%)</Label>
                        <Input
                          type="number"
                          value={decimalToPercent(parameters.long.add_interval)}
                          onChange={(e) => updateParameter('long.add_interval', percentToDecimal(parseFloat(e.target.value)))}
                          step="0.1"
                          min="0.1"
                        />
                      </div>
                      <div>
                        <Label>最大加仓次数</Label>
                        <Input
                          type="number"
                          value={parameters.long.max_add_times}
                          onChange={(e) => updateParameter('long.max_add_times', parseInt(e.target.value))}
                          min="0"
                        />
                      </div>
                      <div>
                        <Label>首仓止盈 (%)</Label>
                        <Input
                          type="number"
                          value={decimalToPercent(parameters.long.tp_first_order)}
                          onChange={(e) => updateParameter('long.tp_first_order', percentToDecimal(parseFloat(e.target.value)))}
                          step="0.1"
                          min="0.1"
                        />
                      </div>
                      <div>
                        <Label>满仓前止盈 (%)</Label>
                        <Input
                          type="number"
                          value={decimalToPercent(parameters.long.tp_before_full)}
                          onChange={(e) => updateParameter('long.tp_before_full', percentToDecimal(parseFloat(e.target.value)))}
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
                          value={parameters.short.first_qty}
                          onChange={(e) => updateParameter('short.first_qty', parseFloat(e.target.value))}
                          step="0.01"
                          min="0"
                        />
                      </div>
                      <div>
                        <Label>加仓倍数</Label>
                        <Input
                          type="number"
                          value={parameters.short.add_ratio}
                          onChange={(e) => updateParameter('short.add_ratio', parseFloat(e.target.value))}
                          step="0.1"
                          min="1"
                        />
                      </div>
                      <div>
                        <Label>加仓间隔 (%)</Label>
                        <Input
                          type="number"
                          value={decimalToPercent(parameters.short.add_interval)}
                          onChange={(e) => updateParameter('short.add_interval', percentToDecimal(parseFloat(e.target.value)))}
                          step="0.1"
                          min="0.1"
                        />
                      </div>
                      <div>
                        <Label>最大加仓次数</Label>
                        <Input
                          type="number"
                          value={parameters.short.max_add_times}
                          onChange={(e) => updateParameter('short.max_add_times', parseInt(e.target.value))}
                          min="0"
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
                          value={decimalToPercent(parameters.hedge.trigger_loss)}
                          onChange={(e) => updateParameter('hedge.trigger_loss', percentToDecimal(parseFloat(e.target.value)))}
                          step="0.1"
                          min="0.1"
                        />
                      </div>
                      <div>
                        <Label>平衡精度</Label>
                        <Input
                          type="number"
                          value={parameters.hedge.equal_eps}
                          onChange={(e) => updateParameter('hedge.equal_eps', parseFloat(e.target.value))}
                          step="0.01"
                          min="0.01"
                        />
                      </div>
                      <div>
                        <Label>最小等待时间 (秒)</Label>
                        <Input
                          type="number"
                          value={parameters.hedge.min_wait_seconds}
                          onChange={(e) => updateParameter('hedge.min_wait_seconds', parseInt(e.target.value))}
                          min="0"
                        />
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
                        checked={parameters.notifications}
                        onCheckedChange={(checked: boolean) => updateParameter('notifications', checked)}
                      />
                    </div>

                    <div className="flex items-center justify-between p-4 border rounded-lg bg-amber-50 border-amber-200">
                      <div>
                        <Label className="text-amber-800">自动交易模式</Label>
                        <p className="text-sm text-amber-600">启用后系统将自动执行交易（请谨慎开启）</p>
                      </div>
                      <Switch
                        checked={parameters.autoTrade}
                        onCheckedChange={(checked: boolean) => updateParameter('autoTrade', checked)}
                      />
                    </div>
                  </div>
                </div>
              </TabsContent>

              <TabsContent value="templates" className="h-full m-0">
                <div className="h-full overflow-y-auto pr-2">
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
                            className="transition-all duration-200"
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

              <TabsContent value="advanced" className="h-full m-0">
                <div className="h-full overflow-y-auto pr-2 space-y-6">
                  {/* 交易配置 */}
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
                          onChange={(e) => updateParameter('advanced.leverage', parseInt(e.target.value))}
                          min="1"
                          max="100"
                        />
                      </div>
                    </div>
                  </div>

                  <Separator />

                  {/* 风险控制 */}
                  <div className="space-y-4">
                    <h3 className="text-lg font-semibold">风险控制</h3>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label>最大日亏损 (USDT)</Label>
                        <Input
                          type="number"
                          value={parameters.advanced?.max_daily_loss || 0}
                          onChange={(e) => updateParameter('advanced.max_daily_loss', parseFloat(e.target.value))}
                          min="0"
                        />
                      </div>
                      <div>
                        <Label>紧急止损比例 (%)</Label>
                        <Input
                          type="number"
                          value={decimalToPercent(parameters.advanced?.emergency_stop_loss || 0)}
                          onChange={(e) => updateParameter('advanced.emergency_stop_loss', percentToDecimal(parseFloat(e.target.value)))}
                          step="0.1"
                          min="0"
                        />
                      </div>
                    </div>
                  </div>

                  <Separator />

                  {/* 安全设置 */}
                  <div className="space-y-4">
                    <h3 className="text-lg font-semibold">安全设置</h3>
                    <div className="space-y-3">
                      <div className="flex items-center justify-between p-4 border rounded-lg">
                        <div>
                          <Label>需要手动启动</Label>
                          <p className="text-sm text-muted-foreground">禁用后系统可自动启动交易</p>
                        </div>
                        <Switch
                          checked={parameters.advanced?.require_manual_start ?? true}
                          onCheckedChange={(checked: boolean) => updateParameter('advanced.require_manual_start', checked)}
                        />
                      </div>
                      <div className="flex items-center justify-between p-4 border rounded-lg">
                        <div>
                          <Label>错误时自动停止</Label>
                          <p className="text-sm text-muted-foreground">发生错误时自动停止交易</p>
                        </div>
                        <Switch
                          checked={parameters.advanced?.auto_stop_on_error ?? true}
                          onCheckedChange={(checked: boolean) => updateParameter('advanced.auto_stop_on_error', checked)}
                        />
                      </div>
                    </div>
                  </div>
                </div>
              </TabsContent>
            </div>
          </Tabs>
            </div>
          </Tabs>
        </div>

        {/* 根据标签页动态显示按钮 */}
        {renderActionButtons()}
        )}

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
        )}

      </DialogContent>
    </Dialog>
  );
}