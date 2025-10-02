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
  // 安全的参数初始化，防止白屏
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

  // 刷新当前参数
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
            newParams.long = runningParams.long || parameters.long;
            newParams.short = runningParams.short || parameters.short;
            newParams.hedge = runningParams.hedge || parameters.hedge;
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

  // 重置参数
  const resetCurrentTab = () => {
    setParameters(prev => {
      const newParams = { ...prev };
      
      if (activeTab === 'parameters') {
        newParams.long = SAFE_DEFAULTS.parameters.long;
        newParams.short = SAFE_DEFAULTS.parameters.short;
        newParams.hedge = SAFE_DEFAULTS.parameters.hedge;
        newParams.autoTrade = false;
      }
      
      return newParams;
    });
  };

  // 保存功能
  const saveCurrentTab = () => {
    const finalParams = {
      ...parameters,
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
        <DialogHeader>
          <DialogTitle>参数设置 - {instanceName || '未知实例'}</DialogTitle>
          <DialogDescription>
            配置交易策略参数和高级设置 ({platform || '未知平台'})
          </DialogDescription>
        </DialogHeader>

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
      </DialogContent>
    </Dialog>
  );
}