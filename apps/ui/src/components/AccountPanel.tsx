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
import { Settings, Eye, EyeOff, Save, RotateCcw } from "lucide-react";

interface Account {
  id: string;
  name: string;
  platform: string;
  status: 'connected' | 'disconnected' | 'error';
  balance: number;
  apiKey: string;
  secretKey: string;
  template: string;
  parameters: {
    maxPosition: number;
    riskLevel: number;
    stopLoss: number;
    takeProfit: number;
    autoTrade: boolean;
    notifications: boolean;
  };
}

interface Template {
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
  };
}

export function AccountPanel() {
  const [selectedPlatform, setSelectedPlatform] = useState("binance");
  const [showApiKey, setShowApiKey] = useState(false);
  const [showSecretKey, setShowSecretKey] = useState(false);

  const platforms = [
    { id: "binance", name: "币安", icon: "🟡" },
    { id: "huobi", name: "火币", icon: "🔵" },
    { id: "okex", name: "OKEx", icon: "⚫" }
  ];

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
        notifications: true
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
        notifications: true
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
        notifications: false
      }
    }
  ];

  // 账户将从 API 获取，移除 Mock 数据
  const [accounts, setAccounts] = useState<Record<string, Account[]>>({});
  const [selectedAccountId, setSelectedAccountId] = useState<string | null>(null);

  const currentAccounts = accounts[selectedPlatform] || [];
  const selectedAccount = selectedAccountId 
    ? currentAccounts.find(acc => acc.id === selectedAccountId)
    : currentAccounts[0];

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'connected':
        return <Badge className="bg-green-100 text-green-800 border-green-200">已连接</Badge>;
      case 'disconnected':
        return <Badge className="bg-gray-100 text-gray-800 border-gray-200">未连接</Badge>;
      case 'error':
        return <Badge className="bg-red-100 text-red-800 border-red-200">错误</Badge>;
      default:
        return <Badge>未知</Badge>;
    }
  };

  const applyTemplate = (templateId: string) => {
    if (!selectedAccount) return;
    
    const template = templates.find(t => t.id === templateId);
    if (!template) return;

    const updatedAccounts = { ...accounts };
    const accountIndex = updatedAccounts[selectedPlatform].findIndex(acc => acc.id === selectedAccount.id);
    
    if (accountIndex >= 0) {
      updatedAccounts[selectedPlatform][accountIndex] = {
        ...selectedAccount,
        template: templateId,
        parameters: { ...template.parameters }
      };
      setAccounts(updatedAccounts);
    }
  };

  const updateParameter = (key: string, value: any) => {
    if (!selectedAccount) return;

    const updatedAccounts = { ...accounts };
    const accountIndex = updatedAccounts[selectedPlatform].findIndex(acc => acc.id === selectedAccount.id);
    
    if (accountIndex >= 0) {
      updatedAccounts[selectedPlatform][accountIndex] = {
        ...selectedAccount,
        parameters: {
          ...selectedAccount.parameters,
          [key]: value
        }
      };
      setAccounts(updatedAccounts);
    }
  };

  return (
    <div className="space-y-6">
      {/* Platform Selection */}
      <div className="flex gap-4">
        {platforms.map((platform) => (
          <Button
            key={platform.id}
            variant={selectedPlatform === platform.id ? "default" : "outline"}
            onClick={() => setSelectedPlatform(platform.id)}
            className="flex items-center gap-2"
          >
            <span>{platform.icon}</span>
            {platform.name}
            <Badge variant="secondary" className="ml-2">
              {accounts[platform.id]?.length || 0}
            </Badge>
          </Button>
        ))}
      </div>

      {currentAccounts.length === 0 ? (
        <Card>
          <CardContent className="flex items-center justify-center p-12">
            <div className="text-center">
              <p className="text-muted-foreground mb-4">该平台下暂无账户</p>
              <Button>添加账户</Button>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Account List */}
          <Card>
            <CardHeader>
              <CardTitle>账户列表</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {currentAccounts.map((account) => (
                <div
                  key={account.id}
                  className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                    selectedAccount?.id === account.id 
                      ? 'border-primary bg-primary/5' 
                      : 'border-border hover:bg-muted/50'
                  }`}
                  onClick={() => setSelectedAccountId(account.id)}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium">{account.name}</span>
                    {getStatusBadge(account.status)}
                  </div>
                  <div className="text-sm text-muted-foreground">
                    余额: {account.balance.toFixed(2)} USDT
                  </div>
                  <div className="text-xs text-muted-foreground mt-1">
                    模板: {templates.find(t => t.id === account.template)?.name || '自定义'}
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>

          {/* Account Details */}
          {selectedAccount && (
            <div className="lg:col-span-2">
              <Tabs defaultValue="settings" className="w-full">
                <TabsList className="grid w-full grid-cols-3">
                  <TabsTrigger value="settings">参数设置</TabsTrigger>
                  <TabsTrigger value="templates">参数模板</TabsTrigger>
                  <TabsTrigger value="api">API配置</TabsTrigger>
                </TabsList>

                <TabsContent value="settings" className="space-y-6">
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <Settings className="w-5 h-5" />
                        {selectedAccount.name} - 参数设置
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-6">
                      <div className="grid grid-cols-2 gap-6">
                        <div className="space-y-2">
                          <Label>最大仓位 (%)</Label>
                          <div className="px-3">
                            <Slider
                              value={[selectedAccount.parameters.maxPosition]}
                              onValueChange={(value: number[]) => updateParameter('maxPosition', value[0])}
                              max={100}
                              step={5}
                              className="w-full"
                            />
                            <div className="flex justify-between text-xs text-muted-foreground mt-1">
                              <span>0%</span>
                              <span>{selectedAccount.parameters.maxPosition}%</span>
                              <span>100%</span>
                            </div>
                          </div>
                        </div>

                        <div className="space-y-2">
                          <Label>风险等级</Label>
                          <div className="px-3">
                            <Slider
                              value={[selectedAccount.parameters.riskLevel]}
                              onValueChange={(value: number[]) => updateParameter('riskLevel', value[0])}
                              max={100}
                              step={10}
                              className="w-full"
                            />
                            <div className="flex justify-between text-xs text-muted-foreground mt-1">
                              <span>保守</span>
                              <span>{selectedAccount.parameters.riskLevel}%</span>
                              <span>激进</span>
                            </div>
                          </div>
                        </div>

                        <div className="space-y-2">
                          <Label>止损比例 (%)</Label>
                          <Input
                            type="number"
                            value={selectedAccount.parameters.stopLoss}
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
                            value={selectedAccount.parameters.takeProfit}
                            onChange={(e) => updateParameter('takeProfit', parseFloat(e.target.value))}
                            min="0"
                            max="100"
                            step="0.5"
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
                            checked={selectedAccount.parameters.autoTrade}
                            onCheckedChange={(checked: boolean) => updateParameter('autoTrade', checked)}
                          />
                        </div>

                        <div className="flex items-center justify-between">
                          <div>
                            <Label>消息通知</Label>
                            <p className="text-sm text-muted-foreground">接收交易和系统通知</p>
                          </div>
                          <Switch
                            checked={selectedAccount.parameters.notifications}
                            onCheckedChange={(checked: boolean) => updateParameter('notifications', checked)}
                          />
                        </div>
                      </div>

                      <div className="flex gap-2">
                        <Button className="flex-1">
                          <Save className="w-4 h-4 mr-2" />
                          保存设置
                        </Button>
                        <Button variant="outline">
                          <RotateCcw className="w-4 h-4 mr-2" />
                          重置
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                </TabsContent>

                <TabsContent value="templates" className="space-y-4">
                  {templates.map((template) => (
                    <Card key={template.id} className={selectedAccount.template === template.id ? 'ring-2 ring-primary' : ''}>
                      <CardHeader>
                        <div className="flex items-center justify-between">
                          <div>
                            <CardTitle className="text-lg">{template.name}</CardTitle>
                            <p className="text-sm text-muted-foreground">{template.description}</p>
                          </div>
                          <Button
                            variant={selectedAccount.template === template.id ? "default" : "outline"}
                            onClick={() => applyTemplate(template.id)}
                            disabled={selectedAccount.template === template.id}
                          >
                            {selectedAccount.template === template.id ? '当前模板' : '应用模板'}
                          </Button>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <div className="grid grid-cols-2 gap-4 text-sm">
                          <div>最大仓位: {template.parameters.maxPosition}%</div>
                          <div>风险等级: {template.parameters.riskLevel}%</div>
                          <div>止损: {template.parameters.stopLoss}%</div>
                          <div>止盈: {template.parameters.takeProfit}%</div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </TabsContent>

                <TabsContent value="api" className="space-y-4">
                  <Card>
                    <CardHeader>
                      <CardTitle>API配置</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="space-y-2">
                        <Label>API Key</Label>
                        <div className="flex gap-2">
                          <Input
                            type={showApiKey ? "text" : "password"}
                            value={selectedAccount.apiKey}
                            readOnly
                          />
                          <Button
                            variant="outline"
                            size="icon"
                            onClick={() => setShowApiKey(!showApiKey)}
                          >
                            {showApiKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                          </Button>
                        </div>
                      </div>

                      <div className="space-y-2">
                        <Label>Secret Key</Label>
                        <div className="flex gap-2">
                          <Input
                            type={showSecretKey ? "text" : "password"}
                            value={selectedAccount.secretKey}
                            readOnly
                          />
                          <Button
                            variant="outline"
                            size="icon"
                            onClick={() => setShowSecretKey(!showSecretKey)}
                          >
                            {showSecretKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                          </Button>
                        </div>
                      </div>

                      <div className="flex gap-2">
                        <Button>测试连接</Button>
                        <Button variant="outline">重新配置</Button>
                      </div>
                    </CardContent>
                  </Card>
                </TabsContent>
              </Tabs>
            </div>
          )}
        </div>
      )}
    </div>
  );
}