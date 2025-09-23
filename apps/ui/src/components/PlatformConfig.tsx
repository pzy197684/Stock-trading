import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import { Badge } from "./ui/badge";
import { Switch } from "./ui/switch";
import { Slider } from "./ui/slider";
import { Separator } from "./ui/separator";
import { ScrollArea } from "./ui/scroll-area";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "./ui/accordion";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "./ui/dialog";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from "./ui/alert-dialog";
import { Settings2, Wifi, Clock, Shield, AlertTriangle, CheckCircle, LayoutTemplate, Plus, Edit, Trash2, Save, DollarSign } from "lucide-react";

interface ParameterTemplate {
  id: string;
  name: string;
  description: string;
  parameters: {
    maxPosition: number;
    riskLevel: number;
    stopLoss: number;
    takeProfit: number;
    autoTrade: boolean;
    notifications: boolean;
    gridSpacing: number;
    maxGrids: number;
  };
  createdAt: string;
  isDefault: boolean;
}

interface PlatformConfig {
  id: string;
  name: string;
  icon: string;
  status: 'connected' | 'disconnected' | 'error';
  accounts: number;
  settings: {
    requestFrequency: number;
    timeout: number;
    retryAttempts: number;
    enableProxy: boolean;
    proxyUrl: string;
    enableRateLimit: boolean;
    maxOrdersPerSecond: number;
    enableFailover: boolean;
    primaryEndpoint: string;
    backupEndpoint: string;
  };
  limits: {
    maxDailyOrders: number;
    maxPositionSize: number;
    minOrderValue: number;
  };
  templates: ParameterTemplate[];
  fees: {
    makerFee: number;
    takerFee: number;
    withdrawalFee: number;
  };
}

export function PlatformConfig() {
  const [selectedPlatform, setSelectedPlatform] = useState("binance");
  const [showTemplateDialog, setShowTemplateDialog] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState<ParameterTemplate | null>(null);
  const [templateFormData, setTemplateFormData] = useState<Partial<ParameterTemplate>>({
    name: '',
    description: '',
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
  });

  const [platformConfigs, setPlatformConfigs] = useState<Record<string, PlatformConfig>>({
    binance: {
      id: "binance",
      name: "币安",
      icon: "🟡",
      status: "connected",
      accounts: 2,
      settings: {
        requestFrequency: 100,
        timeout: 5000,
        retryAttempts: 3,
        enableProxy: false,
        proxyUrl: "",
        enableRateLimit: true,
        maxOrdersPerSecond: 10,
        enableFailover: true,
        primaryEndpoint: "https://api.binance.com",
        backupEndpoint: "https://api1.binance.com"
      },
      limits: {
        maxDailyOrders: 10000,
        maxPositionSize: 100000,
        minOrderValue: 10
      },
      templates: [
        {
          id: "binance_conservative",
          name: "保守型",
          description: "适合币安的低风险稳健收益配置",
          parameters: {
            maxPosition: 30,
            riskLevel: 20,
            stopLoss: 5,
            takeProfit: 10,
            autoTrade: true,
            notifications: true,
            gridSpacing: 1,
            maxGrids: 10
          },
          createdAt: "2024-09-19 10:00:00",
          isDefault: true
        },
        {
          id: "binance_balanced",
          name: "平衡型",
          description: "币安平台风险与收益平衡的参数配置",
          parameters: {
            maxPosition: 50,
            riskLevel: 50,
            stopLoss: 8,
            takeProfit: 15,
            autoTrade: true,
            notifications: true,
            gridSpacing: 0.5,
            maxGrids: 20
          },
          createdAt: "2024-09-19 10:00:00",
          isDefault: true
        }
      ],
      fees: {
        makerFee: 0.001,
        takerFee: 0.002,
        withdrawalFee: 0.005
      }
    },
    huobi: {
      id: "huobi",
      name: "火币",
      icon: "🔵",
      status: "connected",
      accounts: 1,
      settings: {
        requestFrequency: 200,
        timeout: 8000,
        retryAttempts: 5,
        enableProxy: true,
        proxyUrl: "http://proxy.example.com:8080",
        enableRateLimit: true,
        maxOrdersPerSecond: 5,
        enableFailover: false,
        primaryEndpoint: "https://api.huobi.pro",
        backupEndpoint: ""
      },
      limits: {
        maxDailyOrders: 5000,
        maxPositionSize: 50000,
        minOrderValue: 5
      },
      templates: [
        {
          id: "huobi_aggressive",
          name: "激进型",
          description: "火币平台高风险高收益配置",
          parameters: {
            maxPosition: 80,
            riskLevel: 80,
            stopLoss: 12,
            takeProfit: 25,
            autoTrade: true,
            notifications: false,
            gridSpacing: 0.3,
            maxGrids: 30
          },
          createdAt: "2024-09-19 10:00:00",
          isDefault: true
        }
      ],
      fees: {
        makerFee: 0.0015,
        takerFee: 0.0025,
        withdrawalFee: 0.005
      }
    },
    okex: {
      id: "okex",
      name: "OKEx",
      icon: "⚫",
      status: "error",
      accounts: 1,
      settings: {
        requestFrequency: 150,
        timeout: 6000,
        retryAttempts: 3,
        enableProxy: false,
        proxyUrl: "",
        enableRateLimit: true,
        maxOrdersPerSecond: 8,
        enableFailover: true,
        primaryEndpoint: "https://www.okex.com",
        backupEndpoint: "https://aws.okex.com"
      },
      limits: {
        maxDailyOrders: 8000,
        maxPositionSize: 80000,
        minOrderValue: 1
      },
      templates: [
        {
          id: "okex_conservative",
          name: "保守型",
          description: "OKEx平台保守型配置",
          parameters: {
            maxPosition: 25,
            riskLevel: 15,
            stopLoss: 4,
            takeProfit: 8,
            autoTrade: true,
            notifications: true,
            gridSpacing: 1.2,
            maxGrids: 8
          },
          createdAt: "2024-09-19 10:00:00",
          isDefault: true
        }
      ],
      fees: {
        makerFee: 0.001,
        takerFee: 0.002,
        withdrawalFee: 0.005
      }
    }
  });

  const currentConfig = platformConfigs[selectedPlatform];

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'connected':
        return (
          <Badge className="bg-green-100 text-green-800 border-green-200">
            <CheckCircle className="w-3 h-3 mr-1" />
            已连接
          </Badge>
        );
      case 'disconnected':
        return (
          <Badge className="bg-gray-100 text-gray-800 border-gray-200">
            <Wifi className="w-3 h-3 mr-1" />
            未连接
          </Badge>
        );
      case 'error':
        return (
          <Badge className="bg-red-100 text-red-800 border-red-200">
            <AlertTriangle className="w-3 h-3 mr-1" />
            错误
          </Badge>
        );
      default:
        return <Badge>未知</Badge>;
    }
  };

  const updateSetting = (key: string, value: any) => {
    setPlatformConfigs(prev => ({
      ...prev,
      [selectedPlatform]: {
        ...prev[selectedPlatform],
        settings: {
          ...prev[selectedPlatform].settings,
          [key]: value
        }
      }
    }));
  };

  const updateLimit = (key: string, value: any) => {
    setPlatformConfigs(prev => ({
      ...prev,
      [selectedPlatform]: {
        ...prev[selectedPlatform],
        limits: {
          ...prev[selectedPlatform].limits,
          [key]: value
        }
      }
    }));
  };

  const handleSaveTemplate = () => {
    if (!templateFormData.name || !templateFormData.parameters) return;

    const newTemplate: ParameterTemplate = {
      id: editingTemplate?.id || `${selectedPlatform}_${Date.now()}`,
      name: templateFormData.name,
      description: templateFormData.description || '',
      parameters: templateFormData.parameters,
      createdAt: editingTemplate?.createdAt || new Date().toLocaleString('zh-CN'),
      isDefault: editingTemplate?.isDefault || false
    };

    setPlatformConfigs(prev => ({
      ...prev,
      [selectedPlatform]: {
        ...prev[selectedPlatform],
        templates: editingTemplate
          ? prev[selectedPlatform].templates.map(t => t.id === editingTemplate.id ? newTemplate : t)
          : [...prev[selectedPlatform].templates, newTemplate]
      }
    }));

    setShowTemplateDialog(false);
    setEditingTemplate(null);
    setTemplateFormData({
      name: '',
      description: '',
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
    });
  };

  const handleEditTemplate = (template: ParameterTemplate) => {
    setEditingTemplate(template);
    setTemplateFormData(template);
    setShowTemplateDialog(true);
  };

  const handleDeleteTemplate = (templateId: string) => {
    setPlatformConfigs(prev => ({
      ...prev,
      [selectedPlatform]: {
        ...prev[selectedPlatform],
        templates: prev[selectedPlatform].templates.filter(t => t.id !== templateId)
      }
    }));
  };

  const updateTemplateParameter = (key: string, value: any) => {
    setTemplateFormData(prev => ({
      ...prev,
      parameters: {
        ...prev.parameters!,
        [key]: value
      }
    }));
  };

  return (
    <div className="space-y-4 md:space-y-6">
      {/* Platform Selection */}
      <div className="flex flex-wrap gap-2 md:gap-4">
        {Object.values(platformConfigs).map((platform) => (
          <Button
            key={platform.id}
            variant={selectedPlatform === platform.id ? "default" : "outline"}
            onClick={() => setSelectedPlatform(platform.id)}
            className="flex items-center gap-2 text-xs md:text-sm"
          >
            <span>{platform.icon}</span>
            {platform.name}
            <Badge variant="secondary" className="ml-2 text-xs">
              {platform.accounts}
            </Badge>
          </Button>
        ))}
      </div>

      {/* Platform Status Overview */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2 text-base md:text-lg">
              <span>{currentConfig.icon}</span>
              {currentConfig.name} 平台配置
            </CardTitle>
            {getStatusBadge(currentConfig.status)}
          </div>
        </CardHeader>
        <CardContent className="p-3 md:p-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2 md:gap-4 mb-4">
            <div className="text-center p-3 md:p-4 bg-muted/50 rounded-lg">
              <div className="text-lg md:text-2xl font-bold">{currentConfig.accounts}</div>
              <div className="text-xs md:text-sm text-muted-foreground">关联账户</div>
            </div>
            <div className="text-center p-3 md:p-4 bg-muted/50 rounded-lg">
              <div className="text-lg md:text-2xl font-bold">{currentConfig.settings.maxOrdersPerSecond}</div>
              <div className="text-xs md:text-sm text-muted-foreground">订单/秒</div>
            </div>
            <div className="text-center p-3 md:p-4 bg-muted/50 rounded-lg">
              <div className="text-lg md:text-2xl font-bold">{currentConfig.settings.requestFrequency}ms</div>
              <div className="text-xs md:text-sm text-muted-foreground">请求间隔</div>
            </div>
            <div className="text-center p-3 md:p-4 bg-muted/50 rounded-lg">
              <div className="text-lg md:text-2xl font-bold">{currentConfig.fees.makerFee}%</div>
              <div className="text-xs md:text-sm text-muted-foreground">Maker费率</div>
            </div>
          </div>
          
          {/* Platform Fee Details */}
          <div className="border rounded-lg p-3 md:p-4 bg-muted/20">
            <div className="flex items-center gap-2 mb-3">
              <DollarSign className="w-4 h-4" />
              <span className="text-sm font-medium">{currentConfig.name} 手续费详情</span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs md:text-sm">
              <div className="text-center p-2 bg-background rounded">
                <div className="font-medium mb-1">Maker 手续费</div>
                <div className="text-green-600 font-bold">{currentConfig.fees.makerFee}%</div>
              </div>
              <div className="text-center p-2 bg-background rounded">
                <div className="font-medium mb-1">Taker 手续费</div>
                <div className="text-blue-600 font-bold">{currentConfig.fees.takerFee}%</div>
              </div>
              <div className="text-center p-2 bg-background rounded">
                <div className="font-medium mb-1">提现手续费</div>
                <div className="text-orange-600 font-bold">{currentConfig.fees.withdrawalFee}%</div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Detailed Configuration */}
      <Tabs defaultValue="templates" className="w-full">
        <TabsList className="grid w-full grid-cols-2 h-auto">
          <TabsTrigger value="templates" className="text-xs md:text-sm p-2 transition-all duration-300">参数模板</TabsTrigger>
          <TabsTrigger value="accounts" className="text-xs md:text-sm p-2 transition-all duration-300">账户管理</TabsTrigger>
        </TabsList>

        <TabsContent value="templates" className="space-y-6 data-[state=active]:animate-in data-[state=active]:fade-in-0 data-[state=active]:slide-in-from-bottom-2 duration-300">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2">
                  <LayoutTemplate className="w-5 h-5" />
                  {currentConfig.name} 参数模板
                </CardTitle>
                <Button 
                  onClick={() => {
                    setEditingTemplate(null);
                    setTemplateFormData({
                      name: '',
                      description: '',
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
                    });
                    setShowTemplateDialog(true);
                  }}
                  className="transition-all duration-200"
                >
                  <Plus className="w-4 h-4 mr-2" />
                  新建模板
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {currentConfig.templates.map((template) => (
                  <div key={template.id} className="border rounded-lg p-4 transition-all duration-200 hover:bg-muted/30">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <h4 className="font-medium">{template.name}</h4>
                          {template.isDefault && (
                            <Badge variant="outline" className="text-xs">默认</Badge>
                          )}
                        </div>
                        <p className="text-sm text-muted-foreground mb-2">{template.description}</p>
                        <p className="text-xs text-muted-foreground">创建时间: {template.createdAt}</p>
                      </div>
                      <div className="flex gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleEditTemplate(template)}
                          className="transition-all duration-200"
                        >
                          <Edit className="w-3 h-3 mr-1" />
                          编辑
                        </Button>
                        {!template.isDefault && (
                          <AlertDialog>
                            <AlertDialogTrigger asChild>
                              <Button variant="outline" size="sm" className="transition-all duration-200">
                                <Trash2 className="w-3 h-3 mr-1" />
                                删除
                              </Button>
                            </AlertDialogTrigger>
                            <AlertDialogContent className="animate-in fade-in-0 zoom-in-95 duration-200">
                              <AlertDialogHeader>
                                <AlertDialogTitle>确认删除模板</AlertDialogTitle>
                                <AlertDialogDescription>
                                  您确定要删除模板 "{template.name}" 吗？此操作不可撤销。
                                </AlertDialogDescription>
                              </AlertDialogHeader>
                              <AlertDialogFooter>
                                <AlertDialogCancel>取消</AlertDialogCancel>
                                <AlertDialogAction
                                  className="bg-destructive text-destructive-foreground"
                                  onClick={() => handleDeleteTemplate(template.id)}
                                >
                                  确认删除
                                </AlertDialogAction>
                              </AlertDialogFooter>
                            </AlertDialogContent>
                          </AlertDialog>
                        )}
                      </div>
                    </div>
                    
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm bg-muted/30 p-3 rounded">
                      <div>
                        <span className="text-muted-foreground">最大仓位</span>
                        <p className="font-medium">{template.parameters.maxPosition}%</p>
                      </div>
                      <div>
                        <span className="text-muted-foreground">风险等级</span>
                        <p className="font-medium">{template.parameters.riskLevel}%</p>
                      </div>
                      <div>
                        <span className="text-muted-foreground">止损</span>
                        <p className="font-medium">{template.parameters.stopLoss}%</p>
                      </div>
                      <div>
                        <span className="text-muted-foreground">止盈</span>
                        <p className="font-medium">{template.parameters.takeProfit}%</p>
                      </div>
                    </div>
                  </div>
                ))}
                
                {currentConfig.templates.length === 0 && (
                  <div className="text-center py-8 text-muted-foreground">
                    <LayoutTemplate className="w-12 h-12 mx-auto mb-2 opacity-50" />
                    <p>该平台暂无参数模板</p>
                    <p className="text-sm">点击上方按钮创建第一个模板</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="accounts" className="space-y-6 data-[state=active]:animate-in data-[state=active]:fade-in-0 data-[state=active]:slide-in-from-bottom-2 duration-300">
          <Card>
            <CardHeader>
              <CardTitle>平台账户管理</CardTitle>
            </CardHeader>
            <CardContent>
              <Accordion type="single" collapsible className="w-full">
                <AccordionItem value="account-1">
                  <AccordionTrigger className="transition-all duration-200">主账户 - 余额: 12,500.50 USDT</AccordionTrigger>
                  <AccordionContent className="data-[state=open]:animate-accordion-down data-[state=closed]:animate-accordion-up">
                    <div className="space-y-4 pt-4">
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <Label>账户状态</Label>
                          <p className="text-sm">正常</p>
                        </div>
                        <div>
                          <Label>API权限</Label>
                          <p className="text-sm">交易、查询</p>
                        </div>
                        <div>
                          <Label>最后活跃</Label>
                          <p className="text-sm">2024-09-19 14:35</p>
                        </div>
                        <div>
                          <Label>今日交易次数</Label>
                          <p className="text-sm">47</p>
                        </div>
                      </div>
                      <div className="flex gap-2">
                        <Button size="sm" className="transition-all duration-200">编辑配置</Button>
                        <Button size="sm" variant="outline" className="transition-all duration-200">禁用账户</Button>
                      </div>
                    </div>
                  </AccordionContent>
                </AccordionItem>
                
                <AccordionItem value="account-2">
                  <AccordionTrigger className="transition-all duration-200">副账户 - 余额: 8,200.75 USDT</AccordionTrigger>
                  <AccordionContent className="data-[state=open]:animate-accordion-down data-[state=closed]:animate-accordion-up">
                    <div className="space-y-4 pt-4">
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <Label>账户状态</Label>
                          <p className="text-sm">正常</p>
                        </div>
                        <div>
                          <Label>API权限</Label>
                          <p className="text-sm">仅查询</p>
                        </div>
                        <div>
                          <Label>最后活跃</Label>
                          <p className="text-sm">2024-09-19 13:20</p>
                        </div>
                        <div>
                          <Label>今日交易次数</Label>
                          <p className="text-sm">23</p>
                        </div>
                      </div>
                      <div className="flex gap-2">
                        <Button size="sm" className="transition-all duration-200">编辑配置</Button>
                        <Button size="sm" variant="outline" className="transition-all duration-200">禁用账户</Button>
                      </div>
                    </div>
                  </AccordionContent>
                </AccordionItem>
              </Accordion>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Template Dialog */}
      <Dialog open={showTemplateDialog} onOpenChange={setShowTemplateDialog}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-hidden flex flex-col animate-in fade-in-0 zoom-in-95 duration-300">
          <DialogHeader className="flex-shrink-0 border-b pb-4 mb-4">
            <DialogTitle>
              {editingTemplate ? '编辑参数模板' : '新建参数模板'}
            </DialogTitle>
            <DialogDescription>
              为 {currentConfig.name} 平台{editingTemplate ? '编辑' : '创建'}参数模板
            </DialogDescription>
          </DialogHeader>

          <ScrollArea className="h-[60vh] md:h-auto">
            <div className="space-y-6 pb-4 pr-4">
              <div className="grid grid-cols-1 gap-4">
                <div className="space-y-2">
                  <Label>模板名称</Label>
                  <Input
                    value={templateFormData.name}
                    onChange={(e) => setTemplateFormData(prev => ({ ...prev, name: e.target.value }))}
                    placeholder="输入模板名称"
                  />
                </div>
                <div className="space-y-2">
                  <Label>模板描述</Label>
                  <Input
                    value={templateFormData.description}
                    onChange={(e) => setTemplateFormData(prev => ({ ...prev, description: e.target.value }))}
                    placeholder="输入模板描述"
                  />
                </div>
              </div>

              <Separator />

              <div className="space-y-4">
                <h4 className="font-medium">参数配置</h4>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>最大仓位 (%)</Label>
                    <div className="px-3">
                      <Slider
                        value={[templateFormData.parameters?.maxPosition || 50]}
                        onValueChange={(value) => updateTemplateParameter('maxPosition', value[0])}
                        max={100}
                        step={5}
                        className="w-full"
                      />
                      <div className="flex justify-between text-xs text-muted-foreground mt-1">
                        <span>0%</span>
                        <span>{templateFormData.parameters?.maxPosition || 50}%</span>
                        <span>100%</span>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label>风险等级</Label>
                    <div className="px-3">
                      <Slider
                        value={[templateFormData.parameters?.riskLevel || 50]}
                        onValueChange={(value) => updateTemplateParameter('riskLevel', value[0])}
                        max={100}
                        step={10}
                        className="w-full"
                      />
                      <div className="flex justify-between text-xs text-muted-foreground mt-1">
                        <span>保守</span>
                        <span>{templateFormData.parameters?.riskLevel || 50}%</span>
                        <span>激进</span>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label>止损比例 (%)</Label>
                    <Input
                      type="number"
                      value={templateFormData.parameters?.stopLoss || 8}
                      onChange={(e) => updateTemplateParameter('stopLoss', parseFloat(e.target.value))}
                      min="0"
                      max="50"
                      step="0.5"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label>止盈比例 (%)</Label>
                    <Input
                      type="number"
                      value={templateFormData.parameters?.takeProfit || 15}
                      onChange={(e) => updateTemplateParameter('takeProfit', parseFloat(e.target.value))}
                      min="0"
                      max="100"
                      step="0.5"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label>网格间距 (%)</Label>
                    <Input
                      type="number"
                      value={templateFormData.parameters?.gridSpacing || 0.5}
                      onChange={(e) => updateTemplateParameter('gridSpacing', parseFloat(e.target.value))}
                      min="0.1"
                      max="10"
                      step="0.1"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label>最大网格数</Label>
                    <Input
                      type="number"
                      value={templateFormData.parameters?.maxGrids || 20}
                      onChange={(e) => updateTemplateParameter('maxGrids', parseInt(e.target.value))}
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
                      checked={templateFormData.parameters?.autoTrade || false}
                      onCheckedChange={(checked) => updateTemplateParameter('autoTrade', checked)}
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <Label>消息通知</Label>
                      <p className="text-sm text-muted-foreground">接收交易和系统通知</p>
                    </div>
                    <Switch
                      checked={templateFormData.parameters?.notifications || false}
                      onCheckedChange={(checked) => updateTemplateParameter('notifications', checked)}
                    />
                  </div>
                </div>
              </div>
            </div>
          </ScrollArea>

          <DialogFooter className="flex-shrink-0 border-t pt-4 mt-4">
            <Button variant="outline" onClick={() => setShowTemplateDialog(false)} className="transition-all duration-200">
              取消
            </Button>
            <Button onClick={handleSaveTemplate} className="transition-all duration-200">
              <Save className="w-4 h-4 mr-2" />
              {editingTemplate ? '保存修改' : '创建模板'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}