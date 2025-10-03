import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import { useToast } from "./ui/toast";
import { RefreshCw, Wallet, TrendingUp, TrendingDown, AlertCircle } from "lucide-react";

interface AccountInfo {
  id: string;
  platform: string;
  status: string;
  balance: number;
  available_balance: number;
  profit: number;
  profit_rate: number;
  positions: number;
  orders: number;
  last_update: string;
}

interface PlatformSummary {
  platform: string;
  accounts: AccountInfo[];
  total_balance: number;
  total_profit: number;
  total_positions: number;
  total_orders: number;
  connected_count: number;
  total_count: number;
}

export function AccountPanel() {
  const [platformData, setPlatformData] = useState<Record<string, PlatformSummary>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const { toast } = useToast();

  const platforms = [
    { id: "binance", name: "Binance", color: "bg-yellow-500" },
    { id: "okx", name: "OKX", color: "bg-blue-500" },
    { id: "coinw", name: "CoinW", color: "bg-green-500" },
  ];

  // 获取所有平台的账户数据
  const fetchAllPlatformData = async () => {
    try {
      setIsLoading(true);
      const data: Record<string, PlatformSummary> = {};

      for (const platform of platforms) {
        try {
          const response = await fetch(`http://localhost:8001/api/accounts/${platform.id}`);
          const data = await response.json();
          
          if (data.accounts) {
            const accounts = data.accounts.map((acc: any) => ({
              ...acc,
              platform: platform.id
            }));

            data[platform.id] = {
              platform: platform.id,
              accounts: accounts,
              total_balance: accounts.reduce((sum: number, acc: any) => sum + (acc.balance || 0), 0),
              total_profit: accounts.reduce((sum: number, acc: any) => sum + (acc.profit || 0), 0),
              total_positions: accounts.reduce((sum: number, acc: any) => sum + (acc.positions || 0), 0),
              total_orders: accounts.reduce((sum: number, acc: any) => sum + (acc.orders || 0), 0),
              connected_count: accounts.filter((acc: any) => acc.status === 'connected').length,
              total_count: accounts.length
            };
          } else {
            // 平台没有账户或获取失败
            data[platform.id] = {
              platform: platform.id,
              accounts: [],
              total_balance: 0,
              total_profit: 0,
              total_positions: 0,
              total_orders: 0,
              connected_count: 0,
              total_count: 0
            };
          }
        } catch (error) {
          console.warn(`获取${platform.id}平台数据失败:`, error);
          data[platform.id] = {
            platform: platform.id,
            accounts: [],
            total_balance: 0,
            total_profit: 0,
            total_positions: 0,
            total_orders: 0,
            connected_count: 0,
            total_count: 0
          };
        }
      }

      setPlatformData(data);
      setLastUpdate(new Date());
    } catch (error) {
      console.error('获取平台账户数据失败:', error);
      toast({
        type: "error",
        title: "获取数据失败",
        description: "无法获取平台账户信息"
      });
    } finally {
      setIsLoading(false);
    }
  };

  // 初始化和定时刷新
  useEffect(() => {
    fetchAllPlatformData();
    
    // 每30秒刷新一次
    const interval = setInterval(fetchAllPlatformData, 30000);
    return () => clearInterval(interval);
  }, []);

  // 获取状态颜色
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'connected':
        return 'bg-green-500';
      case 'disconnected':
        return 'bg-gray-500';
      case 'error':
        return 'bg-red-500';
      default:
        return 'bg-yellow-500';
    }
  };

  // 获取状态文本
  const getStatusText = (status: string) => {
    switch (status) {
      case 'connected':
        return '已连接';
      case 'disconnected':
        return '未连接';
      case 'error':
        return '错误';
      default:
        return '未知';
    }
  };

  // 格式化时间
  const formatTime = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleString('zh-CN');
    } catch {
      return '未知';
    }
  };

  // 总览统计
  const totalStats = Object.values(platformData).reduce(
    (totals, platform) => ({
      balance: totals.balance + platform.total_balance,
      profit: totals.profit + platform.total_profit,
      positions: totals.positions + platform.total_positions,
      orders: totals.orders + platform.total_orders,
      connected: totals.connected + platform.connected_count,
      total: totals.total + platform.total_count
    }),
    { balance: 0, profit: 0, positions: 0, orders: 0, connected: 0, total: 0 }
  );

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>账户管理</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
            <p className="mt-2 text-gray-500">加载中...</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* 总览卡片 */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Wallet className="h-5 w-5" />
            账户总览
          </CardTitle>
          <Button
            variant="outline"
            size="sm"
            onClick={fetchAllPlatformData}
            disabled={isLoading}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
            刷新
          </Button>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">
                {totalStats.balance.toFixed(2)}
              </div>
              <div className="text-sm text-gray-500">总余额 (USDT)</div>
            </div>
            <div className="text-center">
              <div className={`text-2xl font-bold ${totalStats.profit >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {totalStats.profit >= 0 ? '+' : ''}{totalStats.profit.toFixed(2)}
              </div>
              <div className="text-sm text-gray-500">总盈亏 (USDT)</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">
                {totalStats.positions}
              </div>
              <div className="text-sm text-gray-500">总持仓</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">
                {totalStats.orders}
              </div>
              <div className="text-sm text-gray-500">总订单</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-600">
                {totalStats.connected}/{totalStats.total}
              </div>
              <div className="text-sm text-gray-500">连接状态</div>
            </div>
          </div>
          {lastUpdate && (
            <div className="text-xs text-gray-400 mt-4 text-center">
              最后更新: {lastUpdate.toLocaleString('zh-CN')}
            </div>
          )}
        </CardContent>
      </Card>

      {/* 平台详情 */}
      <Card>
        <CardHeader>
          <CardTitle>平台账户管理</CardTitle>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="binance" className="w-full">
            <TabsList className="grid w-full grid-cols-3">
              {platforms.map((platform) => (
                <TabsTrigger key={platform.id} value={platform.id}>
                  <div className={`w-3 h-3 rounded-full ${platform.color} mr-2`}></div>
                  {platform.name}
                </TabsTrigger>
              ))}
            </TabsList>

            {platforms.map((platform) => {
              const data = platformData[platform.id];
              
              return (
                <TabsContent key={platform.id} value={platform.id} className="space-y-4">
                  {/* 平台统计 */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <Card>
                      <CardContent className="p-4">
                        <div className="flex items-center gap-2">
                          <Wallet className="h-4 w-4 text-blue-500" />
                          <div>
                            <div className="text-lg font-semibold">
                              {data?.total_balance.toFixed(2) || '0.00'}
                            </div>
                            <div className="text-xs text-gray-500">余额 (USDT)</div>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                    
                    <Card>
                      <CardContent className="p-4">
                        <div className="flex items-center gap-2">
                          {data?.total_profit >= 0 ? (
                            <TrendingUp className="h-4 w-4 text-green-500" />
                          ) : (
                            <TrendingDown className="h-4 w-4 text-red-500" />
                          )}
                          <div>
                            <div className={`text-lg font-semibold ${
                              data?.total_profit >= 0 ? 'text-green-600' : 'text-red-600'
                            }`}>
                              {data?.total_profit >= 0 ? '+' : ''}{data?.total_profit.toFixed(2) || '0.00'}
                            </div>
                            <div className="text-xs text-gray-500">盈亏 (USDT)</div>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                    
                    <Card>
                      <CardContent className="p-4">
                        <div className="flex items-center gap-2">
                          <AlertCircle className="h-4 w-4 text-purple-500" />
                          <div>
                            <div className="text-lg font-semibold">
                              {data?.total_positions || 0}
                            </div>
                            <div className="text-xs text-gray-500">持仓数</div>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                    
                    <Card>
                      <CardContent className="p-4">
                        <div className="flex items-center gap-2">
                          <div className={`w-3 h-3 rounded-full ${
                            data?.connected_count === data?.total_count && data?.total_count > 0
                              ? 'bg-green-500' 
                              : data?.connected_count > 0 
                                ? 'bg-yellow-500' 
                                : 'bg-red-500'
                          }`}></div>
                          <div>
                            <div className="text-lg font-semibold">
                              {data?.connected_count || 0}/{data?.total_count || 0}
                            </div>
                            <div className="text-xs text-gray-500">连接状态</div>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </div>

                  {/* 账户列表 */}
                  <div className="space-y-2">
                    <h3 className="text-lg font-semibold">账户列表</h3>
                    {data?.accounts.length > 0 ? (
                      <div className="grid gap-3">
                        {data.accounts.map((account) => (
                          <Card key={account.id} className="border-l-4 border-l-blue-500">
                            <CardContent className="p-4">
                              <div className="flex items-center justify-between">
                                <div className="flex items-center gap-3">
                                  <Badge className={`text-white ${getStatusColor(account.status)}`}>
                                    {getStatusText(account.status)}
                                  </Badge>
                                  <div>
                                    <h4 className="font-semibold">{account.id}</h4>
                                    <p className="text-sm text-gray-500">
                                      {platform.name} 账户
                                    </p>
                                  </div>
                                </div>
                                <div className="text-right">
                                  <div className="text-lg font-semibold">
                                    {account.balance.toFixed(2)} USDT
                                  </div>
                                  <div className="text-sm text-gray-500">
                                    可用: {account.available_balance.toFixed(2)}
                                  </div>
                                </div>
                              </div>
                              
                              <div className="grid grid-cols-3 gap-4 mt-3 pt-3 border-t">
                                <div className="text-center">
                                  <div className={`font-semibold ${
                                    account.profit >= 0 ? 'text-green-600' : 'text-red-600'
                                  }`}>
                                    {account.profit >= 0 ? '+' : ''}{account.profit.toFixed(2)}
                                  </div>
                                  <div className="text-xs text-gray-500">盈亏</div>
                                </div>
                                <div className="text-center">
                                  <div className="font-semibold">{account.positions}</div>
                                  <div className="text-xs text-gray-500">持仓</div>
                                </div>
                                <div className="text-center">
                                  <div className="font-semibold">{account.orders}</div>
                                  <div className="text-xs text-gray-500">订单</div>
                                </div>
                              </div>
                              
                              <div className="text-xs text-gray-400 mt-2">
                                最后更新: {formatTime(account.last_update)}
                              </div>
                            </CardContent>
                          </Card>
                        ))}
                      </div>
                    ) : (
                      <div className="text-center py-8 text-gray-500">
                        <Wallet className="h-12 w-12 mx-auto mb-2 opacity-50" />
                        <p>暂无{platform.name}账户</p>
                        <p className="text-sm">请先配置API密钥</p>
                      </div>
                    )}
                  </div>
                </TabsContent>
              );
            })}
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
}