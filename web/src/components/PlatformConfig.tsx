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
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "./ui/accordion";
import { Settings2, Wifi, Clock, Shield, AlertTriangle, CheckCircle } from "lucide-react";

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
  fees: {
    makerFee: number;
    takerFee: number;
    withdrawalFee: number;
  };
}

export function PlatformConfig() {
  const [selectedPlatform, setSelectedPlatform] = useState("binance");

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
      fees: {
        makerFee: 0.1,
        takerFee: 0.1,
        withdrawalFee: 0.0005
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
      fees: {
        makerFee: 0.2,
        takerFee: 0.2,
        withdrawalFee: 0.001
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
      fees: {
        makerFee: 0.15,
        takerFee: 0.15,
        withdrawalFee: 0.0008
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

  return (
    <div className="space-y-6">
      {/* Platform Selection */}
      <div className="flex gap-4">
        {Object.values(platformConfigs).map((platform) => (
          <Button
            key={platform.id}
            variant={selectedPlatform === platform.id ? "default" : "outline"}
            onClick={() => setSelectedPlatform(platform.id)}
            className="flex items-center gap-2"
          >
            <span>{platform.icon}</span>
            {platform.name}
            <Badge variant="secondary" className="ml-2">
              {platform.accounts}
            </Badge>
          </Button>
        ))}
      </div>

      {/* Platform Status Overview */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <span>{currentConfig.icon}</span>
              {currentConfig.name} 平台配置
            </CardTitle>
            {getStatusBadge(currentConfig.status)}
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center p-4 bg-muted/50 rounded-lg">
              <div className="text-2xl font-bold">{currentConfig.accounts}</div>
              <div className="text-sm text-muted-foreground">关联账户</div>
            </div>
            <div className="text-center p-4 bg-muted/50 rounded-lg">
              <div className="text-2xl font-bold">{currentConfig.settings.maxOrdersPerSecond}</div>
              <div className="text-sm text-muted-foreground">订单/秒</div>
            </div>
            <div className="text-center p-4 bg-muted/50 rounded-lg">
              <div className="text-2xl font-bold">{currentConfig.settings.requestFrequency}ms</div>
              <div className="text-sm text-muted-foreground">请求间隔</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Detailed Configuration */}
      <Tabs defaultValue="network" className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="network">网络设置</TabsTrigger>
          <TabsTrigger value="limits">交易限制</TabsTrigger>
          <TabsTrigger value="fees">手续费</TabsTrigger>
          <TabsTrigger value="accounts">账户管理</TabsTrigger>
        </TabsList>

        <TabsContent value="network" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Wifi className="w-5 h-5" />
                网络与连接设置
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-2 gap-6">
                <div className="space-y-2">
                  <Label>请求频率 (毫秒)</Label>
                  <div className="px-3">
                    <Slider
                      value={[currentConfig.settings.requestFrequency]}
                      onValueChange={(value) => updateSetting('requestFrequency', value[0])}
                      min={50}
                      max={1000}
                      step={50}
                      className="w-full"
                    />
                    <div className="flex justify-between text-xs text-muted-foreground mt-1">
                      <span>50ms</span>
                      <span>{currentConfig.settings.requestFrequency}ms</span>
                      <span>1000ms</span>
                    </div>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label>超时时间 (毫秒)</Label>
                  <Input
                    type="number"
                    value={currentConfig.settings.timeout}
                    onChange={(e) => updateSetting('timeout', parseInt(e.target.value))}
                    min="1000"
                    max="30000"
                    step="1000"
                  />
                </div>

                <div className="space-y-2">
                  <Label>重试次数</Label>
                  <Select
                    value={currentConfig.settings.retryAttempts.toString()}
                    onValueChange={(value) => updateSetting('retryAttempts', parseInt(value))}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="1">1次</SelectItem>
                      <SelectItem value="2">2次</SelectItem>
                      <SelectItem value="3">3次</SelectItem>
                      <SelectItem value="5">5次</SelectItem>
                      <SelectItem value="10">10次</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label>最大订单/秒</Label>
                  <Input
                    type="number"
                    value={currentConfig.settings.maxOrdersPerSecond}
                    onChange={(e) => updateSetting('maxOrdersPerSecond', parseInt(e.target.value))}
                    min="1"
                    max="50"
                  />
                </div>
              </div>

              <Separator />

              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <Label>启用代理</Label>
                    <p className="text-sm text-muted-foreground">通过代理服务器连接API</p>
                  </div>
                  <Switch
                    checked={currentConfig.settings.enableProxy}
                    onCheckedChange={(checked) => updateSetting('enableProxy', checked)}
                  />
                </div>

                {currentConfig.settings.enableProxy && (
                  <div className="space-y-2">
                    <Label>代理地址</Label>
                    <Input
                      value={currentConfig.settings.proxyUrl}
                      onChange={(e) => updateSetting('proxyUrl', e.target.value)}
                      placeholder="http://proxy.example.com:8080"
                    />
                  </div>
                )}

                <div className="flex items-center justify-between">
                  <div>
                    <Label>启用速率限制</Label>
                    <p className="text-sm text-muted-foreground">防止超出API调用限制</p>
                  </div>
                  <Switch
                    checked={currentConfig.settings.enableRateLimit}
                    onCheckedChange={(checked) => updateSetting('enableRateLimit', checked)}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <Label>启用故障转移</Label>
                    <p className="text-sm text-muted-foreground">主服务器故障时自动切换备用服务器</p>
                  </div>
                  <Switch
                    checked={currentConfig.settings.enableFailover}
                    onCheckedChange={(checked) => updateSetting('enableFailover', checked)}
                  />
                </div>
              </div>

              <Separator />

              <div className="grid grid-cols-1 gap-4">
                <div className="space-y-2">
                  <Label>主要API端点</Label>
                  <Input
                    value={currentConfig.settings.primaryEndpoint}
                    onChange={(e) => updateSetting('primaryEndpoint', e.target.value)}
                  />
                </div>

                {currentConfig.settings.enableFailover && (
                  <div className="space-y-2">
                    <Label>备用API端点</Label>
                    <Input
                      value={currentConfig.settings.backupEndpoint}
                      onChange={(e) => updateSetting('backupEndpoint', e.target.value)}
                    />
                  </div>
                )}
              </div>

              <div className="flex gap-2">
                <Button>保存配置</Button>
                <Button variant="outline">测试连接</Button>
                <Button variant="outline">重置默认</Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="limits" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Shield className="w-5 h-5" />
                交易限制设置
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 gap-6">
                <div className="space-y-2">
                  <Label>每日最大订单数</Label>
                  <Input
                    type="number"
                    value={currentConfig.limits.maxDailyOrders}
                    onChange={(e) => updateLimit('maxDailyOrders', parseInt(e.target.value))}
                    min="100"
                    max="100000"
                  />
                  <p className="text-xs text-muted-foreground">设置每日最大订单数量以控制风险</p>
                </div>

                <div className="space-y-2">
                  <Label>最大持仓金额 (USDT)</Label>
                  <Input
                    type="number"
                    value={currentConfig.limits.maxPositionSize}
                    onChange={(e) => updateLimit('maxPositionSize', parseInt(e.target.value))}
                    min="1000"
                    max="1000000"
                  />
                  <p className="text-xs text-muted-foreground">单个策略的最大持仓金额</p>
                </div>

                <div className="space-y-2">
                  <Label>最小订单金额 (USDT)</Label>
                  <Input
                    type="number"
                    value={currentConfig.limits.minOrderValue}
                    onChange={(e) => updateLimit('minOrderValue', parseFloat(e.target.value))}
                    min="0.1"
                    max="1000"
                    step="0.1"
                  />
                  <p className="text-xs text-muted-foreground">低于此金额的订单将被拒绝</p>
                </div>
              </div>

              <div className="flex gap-2">
                <Button>保存限制</Button>
                <Button variant="outline">重置默认</Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="fees" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>手续费信息</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-3 gap-4">
                <div className="text-center p-4 bg-muted/50 rounded-lg">
                  <div className="text-2xl font-bold">{currentConfig.fees.makerFee}%</div>
                  <div className="text-sm text-muted-foreground">Maker手续费</div>
                </div>
                <div className="text-center p-4 bg-muted/50 rounded-lg">
                  <div className="text-2xl font-bold">{currentConfig.fees.takerFee}%</div>
                  <div className="text-sm text-muted-foreground">Taker手续费</div>
                </div>
                <div className="text-center p-4 bg-muted/50 rounded-lg">
                  <div className="text-2xl font-bold">{currentConfig.fees.withdrawalFee}%</div>
                  <div className="text-sm text-muted-foreground">提现手续费</div>
                </div>
              </div>
              <p className="text-sm text-muted-foreground mt-4">
                手续费信息仅供参考，实际费用以交易所公布为准
              </p>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="accounts" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>平台账户管理</CardTitle>
            </CardHeader>
            <CardContent>
              <Accordion type="single" collapsible className="w-full">
                <AccordionItem value="account-1">
                  <AccordionTrigger>主账户 - 余额: 12,500.50 USDT</AccordionTrigger>
                  <AccordionContent>
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
                        <Button size="sm">编辑配置</Button>
                        <Button size="sm" variant="outline">禁用账户</Button>
                      </div>
                    </div>
                  </AccordionContent>
                </AccordionItem>
                
                <AccordionItem value="account-2">
                  <AccordionTrigger>副账户 - 余额: 8,200.75 USDT</AccordionTrigger>
                  <AccordionContent>
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
                        <Button size="sm">编辑配置</Button>
                        <Button size="sm" variant="outline">禁用账户</Button>
                      </div>
                    </div>
                  </AccordionContent>
                </AccordionItem>
              </Accordion>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}