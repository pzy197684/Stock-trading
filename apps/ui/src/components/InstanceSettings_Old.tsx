import { useState, useCallback } from 'react';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "./ui/dialog";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import { Switch } from "./ui/switch";
import { Separator } from "./ui/separator";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from "./ui/alert-dialog";
import { Save, RotateCcw, RefreshCw, Trash2 } from "lucide-react";
import apiService from "../services/apiService";
import { DEFAULT_CONFIG } from "../config/defaults";

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
  instanceId,
  instanceName,
  platform,
  currentParameters,
  onParametersChange,
  onDeleteInstance
}: InstanceSettingsProps) {
  const [parameters, setParameters] = useState<InstanceParameters>(currentParameters);
  const [activeTab, setActiveTab] = useState("parameters");

  // Mock templates specific to platform
  const templates: Template[] = [
    {
      id: "conservative",
      name: "保守型",
      description: "低风险、稳健收益的参数配置",
      parameters: {
        maxPosition: 30,
        riskLevel: 20,
        stopLoss: 5,
        takeProfit: 10,
        autoTrade: true,
        notifications: true,
        gridSpacing: 1,
        maxGrids: 10
      }
    },
    {
      id: "balanced",
      name: "平衡型",
      description: "风险与收益平衡的参数配置",
      parameters: {
        maxPosition: 50,
        riskLevel: 50,
        stopLoss: 8,
        takeProfit: 15,
        autoTrade: true,
        notifications: true,
        gridSpacing: 0.5,
        maxGrids: 20
      }
    },
    {
      id: "aggressive",
      name: "激进型",
      description: "高风险、高收益的参数配置",
      parameters: {
        maxPosition: 80,
        riskLevel: 80,
        stopLoss: 12,
        takeProfit: 25,
        autoTrade: true,
        notifications: false,
        gridSpacing: 0.3,
        maxGrids: 30
      }
    }
  ];

  const updateParameter = (key: keyof InstanceParameters, value: any) => {
    setParameters(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const applyTemplate = (templateId: string) => {
    const template = templates.find(t => t.id === templateId);
    if (template) {
      setParameters(template.parameters);
    }
  };

  const handleSave = () => {
    onParametersChange(parameters);
    onOpenChange(false);
  };

  const handleReset = () => {
    setParameters(currentParameters);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-hidden flex flex-col animate-in fade-in-0 zoom-in-95 duration-300">
        {/* Fixed Header */}
        <div className="flex-shrink-0 border-b pb-4 mb-4 bg-background/95 backdrop-blur-sm">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Settings className="w-5 h-5" />
              实例设置 - {instanceName}
            </DialogTitle>
            <DialogDescription>
              配置 {platform} 平台上 {instanceName} 实例的交易参数
            </DialogDescription>
          </DialogHeader>
        </div>

        {/* Scrollable Content */}
        <div className="flex-1 min-h-0">
          <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full h-full flex flex-col">
            <TabsList className="grid w-full grid-cols-2 flex-shrink-0 mb-4">
              <TabsTrigger value="parameters" className="transition-all duration-300">参数配置</TabsTrigger>
              <TabsTrigger value="templates" className="transition-all duration-300">参数模板</TabsTrigger>
            </TabsList>

            <div className="flex-1 overflow-hidden">
              <TabsContent value="parameters" className="h-full mt-0 data-[state=active]:animate-in data-[state=active]:fade-in-0 data-[state=active]:slide-in-from-bottom-2 duration-300">
                <div className="h-full overflow-y-auto overflow-x-hidden scrollbar-none" style={{scrollbarWidth: 'none', msOverflowStyle: 'none'}}>
                  <div className="px-1">
                    <div className="space-y-6 pb-20 md:pb-4">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="space-y-2">
                          <Label>最大仓位 (%)</Label>
                          <div className="px-3">
                            <Slider
                              value={[parameters.maxPosition]}
                              onValueChange={(value) => updateParameter('maxPosition', value[0])}
                              max={100}
                              step={5}
                              className="w-full"
                            />
                            <div className="flex justify-between text-xs text-muted-foreground mt-1">
                              <span>0%</span>
                              <span>{parameters.maxPosition}%</span>
                              <span>100%</span>
                            </div>
                          </div>
                        </div>

                        <div className="space-y-2">
                          <Label>风险等级</Label>
                          <div className="px-3">
                            <Slider
                              value={[parameters.riskLevel]}
                              onValueChange={(value) => updateParameter('riskLevel', value[0])}
                              max={100}
                              step={10}
                              className="w-full"
                            />
                            <div className="flex justify-between text-xs text-muted-foreground mt-1">
                              <span>保守</span>
                              <span>{parameters.riskLevel}%</span>
                              <span>激进</span>
                            </div>
                          </div>
                        </div>

                        <div className="space-y-2">
                          <Label>止损比例 (%)</Label>
                          <Input
                            type="number"
                            value={parameters.stopLoss}
                            onChange={(e) => updateParameter('stopLoss', parseFloat(e.target.value))}
                            min="0"
                            max="50"
                            step="0.5"
                          />
                        </div>

                        <div className="space-y-2">
                          <Label>止盈比例 (%)</Label>
                          <Input
                            type="number"
                            value={parameters.takeProfit}
                            onChange={(e) => updateParameter('takeProfit', parseFloat(e.target.value))}
                            min="0"
                            max="100"
                            step="0.5"
                          />
                        </div>

                        <div className="space-y-2">
                          <Label>网格间距 (%)</Label>
                          <Input
                            type="number"
                            value={parameters.gridSpacing}
                            onChange={(e) => updateParameter('gridSpacing', parseFloat(e.target.value))}
                            min="0.1"
                            max="10"
                            step="0.1"
                          />
                        </div>

                        <div className="space-y-2">
                          <Label>最大网格数</Label>
                          <Input
                            type="number"
                            value={parameters.maxGrids}
                            onChange={(e) => updateParameter('maxGrids', parseInt(e.target.value))}
                            min="5"
                            max="100"
                          />
                        </div>
                      </div>

                      <Separator />

                      <div className="space-y-4">
                        <div className="flex items-center justify-between">
                          <div>
                            <Label>自动交易</Label>
                            <p className="text-sm text-muted-foreground">启用后系统将自动执行交易</p>
                          </div>
                          <Switch
                            checked={parameters.autoTrade}
                            onCheckedChange={(checked) => updateParameter('autoTrade', checked)}
                          />
                        </div>

                        <div className="flex items-center justify-between">
                          <div>
                            <Label>消息通知</Label>
                            <p className="text-sm text-muted-foreground">接收交易和系统通知</p>
                          </div>
                          <Switch
                            checked={parameters.notifications}
                            onCheckedChange={(checked) => updateParameter('notifications', checked)}
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </TabsContent>

              <TabsContent value="templates" className="h-full mt-0 data-[state=active]:animate-in data-[state=active]:fade-in-0 data-[state=active]:slide-in-from-bottom-2 duration-300">
                <div className="h-full overflow-y-auto overflow-x-hidden scrollbar-none" style={{scrollbarWidth: 'none', msOverflowStyle: 'none'}}>
                  <div className="px-1">
                    <div className="space-y-4 pb-4">
                      {templates.map((template) => (
                        <div
                          key={template.id}
                          className="border rounded-lg p-4 hover:bg-muted/50 cursor-pointer transition-all duration-200"
                          onClick={() => applyTemplate(template.id)}
                        >
                          <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center gap-2">
                              <LayoutTemplate className="w-4 h-4" />
                              <span className="font-medium">{template.name}</span>
                            </div>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={(e) => {
                                e.stopPropagation();
                                applyTemplate(template.id);
                              }}
                              className="transition-all duration-200"
                            >
                              应用
                            </Button>
                          </div>
                          <p className="text-sm text-muted-foreground mb-3">{template.description}</p>
                          <div className="grid grid-cols-2 gap-2 text-xs">
                            <div>最大仓位: {template.parameters.maxPosition}%</div>
                            <div>风险等级: {template.parameters.riskLevel}%</div>
                            <div>止损: {template.parameters.stopLoss}%</div>
                            <div>止盈: {template.parameters.takeProfit}%</div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </TabsContent>
            </div>
          </Tabs>
        </div>

        {/* Fixed Footer */}
        <div className="flex-shrink-0 border-t pt-4 mt-4 bg-background/95 backdrop-blur-sm">
          <div className="flex justify-between">
            <AlertDialog>
              <AlertDialogTrigger asChild>
                <Button variant="destructive" size="sm" className="transition-all duration-200">
                  <Trash2 className="w-4 h-4 mr-2" />
                  删除实例
                </Button>
              </AlertDialogTrigger>
              <AlertDialogContent className="animate-in fade-in-0 zoom-in-95 duration-200">
                <AlertDialogHeader>
                  <AlertDialogTitle>确认删除实例</AlertDialogTitle>
                  <AlertDialogDescription>
                    您确定要删除实例 "{instanceName}" 吗？此操作不可撤销。
                  </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                  <AlertDialogCancel>取消</AlertDialogCancel>
                  <AlertDialogAction
                    className="bg-destructive text-destructive-foreground"
                    onClick={() => {
                      onDeleteInstance();
                      onOpenChange(false);
                    }}
                  >
                    确认删除
                  </AlertDialogAction>
                </AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>

            <div className="flex gap-2">
              <Button variant="outline" onClick={handleReset} className="transition-all duration-200">
                <RotateCcw className="w-4 h-4 mr-2" />
                重置
              </Button>
              <Button onClick={handleSave} className="transition-all duration-200">
                <Save className="w-4 h-4 mr-2" />
                保存设置
              </Button>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}