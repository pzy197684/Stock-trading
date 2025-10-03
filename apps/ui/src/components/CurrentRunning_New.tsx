import { useState, useEffect } from "react";
import { useApiData } from "../contexts/ApiContext";
import apiService from "../services/apiService";
import { DEFAULT_CONFIG } from "../config/defaults";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "./ui/card";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "./ui/select";
import { Input } from "./ui/input";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "./ui/dialog";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "./ui/alert-dialog";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "./ui/collapsible";
import { InstanceSettings, InstanceParameters } from "./InstanceSettings";
import { useToast } from "./ui/toast";
import {
  Activity,
  AlertTriangle,
  ChevronDown,
  Clock,
  Plus,
  Settings,
  Square,
  Target,
  TrendingDown,
  TrendingUp,
  Zap,
  Play,
  Stop,
  Trash2,
} from "lucide-react";
import { cn } from "./ui/utils";
import { getStrategyDisplayName } from "../utils/strategyNames";

interface TradingInstance {
  id: string;
  platform: string;
  account: string;
  strategy: string;
  status: "initialized" | "running" | "stopped" | "error";
  owner: string;
  profit: number;
  profit_rate: number;
  symbol: string;
  positions: number;
  orders: number;
  runtime: number;
  last_signal: string | null;
  parameters: any;
}

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

interface CreateForm {
  platform: string;
  account: string;
  strategy: string;
  symbol: string;
}

export function CurrentRunning() {
  const [selectedOwner, setSelectedOwner] = useState<string>("all");
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [expandedInstances, setExpandedInstances] = useState<Set<string>>(new Set());
  const [settingsInstance, setSettingsInstance] = useState<TradingInstance | null>(null);
  const [instances, setInstances] = useState<TradingInstance[]>([]);
  const [accounts, setAccounts] = useState<AccountInfo[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  
  // 创建实例相关状态
  const [availablePlatforms] = useState([
    { id: "binance", name: "Binance" },
    { id: "okx", name: "OKX" },
    { id: "coinw", name: "CoinW" },
  ]);
  const [availableStrategies] = useState([
    { id: "martingale_hedge", name: "马丁格尔对冲策略" },
    { id: "recovery", name: "恢复策略" },
  ]);
  const [availableAccounts, setAvailableAccounts] = useState<any[]>([]);
  const [allOwners, setAllOwners] = useState<string[]>([]);
  const [createForm, setCreateForm] = useState<CreateForm>({
    platform: '',
    account: '',
    strategy: '',
    symbol: 'BTCUSDT'
  });
  const [isCreating, setIsCreating] = useState(false);
  
  const { toast } = useToast();

  // 获取运行实例
  const fetchInstances = async () => {
    try {
      setIsLoading(true);
      const response = await apiService.get('/api/running/instances');
      if (response.instances) {
        setInstances(response.instances);
        
        // 提取所有拥有者
        const owners = [...new Set(response.instances.map((i: TradingInstance) => i.owner))];
        setAllOwners(owners);
      }
    } catch (error) {
      console.error('获取运行实例失败:', error);
      toast({
        type: "error",
        title: "获取实例失败",
        description: "无法获取运行中的交易实例"
      });
    } finally {
      setIsLoading(false);
    }
  };

  // 获取账户信息
  const fetchAccounts = async () => {
    try {
      const platforms = ['binance', 'okx', 'coinw'];
      const allAccounts: any[] = [];
      
      for (const platform of platforms) {
        try {
          const response = await apiService.get(`/api/accounts/${platform}`);
          if (response.accounts) {
            allAccounts.push(...response.accounts.map((acc: any) => ({
              ...acc,
              platform: platform,
              display_name: `${platform.toUpperCase()}-${acc.id}`
            })));
          }
        } catch (error) {
          console.warn(`获取${platform}账户失败:`, error);
        }
      }
      
      setAvailableAccounts(allAccounts);
    } catch (error) {
      console.error('获取账户列表失败:', error);
    }
  };

  // 初始化数据
  useEffect(() => {
    fetchInstances();
    fetchAccounts();
    
    // 定时刷新
    const interval = setInterval(fetchInstances, 5000);
    return () => clearInterval(interval);
  }, []);

  // 过滤实例
  const filteredInstances = instances.filter((instance) => {
    if (selectedOwner === "all") return true;
    return instance.owner === selectedOwner;
  });

  // 启动/停止策略
  const handleToggleStrategy = async (instance: TradingInstance) => {
    try {
      if (instance.status === "running") {
        // 停止策略
        const response = await apiService.post('/api/strategy/stop', {
          account_id: instance.account,
          instance_id: instance.id
        });
        
        if (response.success) {
          toast({
            type: "success",
            title: "策略已停止",
            description: `实例 ${instance.id} 已成功停止`
          });
          fetchInstances();
        } else {
          throw new Error(response.message || "停止失败");
        }
      } else {
        // 启动策略  
        const response = await apiService.post(`/api/strategy/start?account_id=${instance.account}&strategy_name=${instance.strategy}`);
        
        if (response.success) {
          toast({
            type: "success",
            title: "策略已启动",
            description: `实例 ${instance.id} 已成功启动`
          });
          fetchInstances();
        } else {
          throw new Error(response.message || "启动失败");
        }
      }
    } catch (error: any) {
      toast({
        type: "error",
        title: instance.status === "running" ? "停止失败" : "启动失败",
        description: error.message || "操作失败"
      });
    }
  };

  // 删除实例
  const handleDeleteInstance = async (instance: TradingInstance) => {
    try {
      const response = await apiService.post('/api/strategy/delete', {
        account_id: instance.account,
        instance_id: instance.id
      });
      
      if (response.success) {
        toast({
          type: "success",
          title: "实例已删除",
          description: `实例 ${instance.id} 已成功删除`
        });
        fetchInstances();
      } else {
        throw new Error(response.message || "删除失败");
      }
    } catch (error: any) {
      toast({
        type: "error",
        title: "删除失败",
        description: error.message || "删除实例失败"
      });
    }
  };

  // 创建新实例
  const handleCreateInstance = async () => {
    try {
      // 参数验证
      if (!createForm.platform || !createForm.account || !createForm.strategy || !createForm.symbol) {
        toast({
          type: "error",
          title: "参数不完整",
          description: "请填写所有必要参数"
        });
        return;
      }

      // 检查重复实例
      const existing = instances.find(i => 
        i.platform === createForm.platform &&
        i.account === createForm.account &&
        i.strategy === createForm.strategy &&
        i.symbol === createForm.symbol
      );

      if (existing) {
        toast({
          type: "error",
          title: "实例已存在",
          description: `相同配置的实例已存在: ${existing.id}`
        });
        return;
      }

      setIsCreating(true);
      
      const response = await apiService.post('/api/instances/create', {
        account_id: createForm.account,
        platform: createForm.platform,
        strategy: createForm.strategy,
        symbol: createForm.symbol,
        parameters: {
          autoTrade: false  // 默认不自动交易，需要手动启动
        }
      });
      
      if (response.success) {
        toast({
          type: "success",
          title: "实例创建成功",
          description: `实例 ${response.instance_id} 已创建，请配置参数后手动启动`
        });
        setShowCreateDialog(false);
        setCreateForm({
          platform: '',
          account: '',
          strategy: '',
          symbol: 'BTCUSDT'
        });
        fetchInstances();
      } else {
        // 显示API返回的具体错误信息
        const errorMsg = response.error || response.message || "创建失败";
        throw new Error(errorMsg);
      }
    } catch (error: any) {
      console.error('创建实例失败:', error);
      
      // 提取有意义的错误消息
      let errorMessage = "创建实例失败";
      if (error.message && error.message !== '[object Object]') {
        errorMessage = error.message;
      } else if (typeof error === 'string') {
        errorMessage = error;
      }
      
      toast({
        type: "error",
        title: "创建失败",
        description: errorMessage
      });
    } finally {
      setIsCreating(false);
    }
  };

  // 保存实例参数
  const handleSaveSettings = async (instanceId: string, parameters: InstanceParameters) => {
    try {
      // 验证所有必要参数都不为0且已填写
      const requiredParams = ['leverage', 'long.first_qty', 'short.first_qty'];
      for (const param of requiredParams) {
        const keys = param.split('.');
        let value = parameters;
        for (const key of keys) {
          value = value[key];
        }
        if (!value || value === 0) {
          toast({
            type: "error",
            title: "参数验证失败",
            description: `参数 ${param} 不能为0或空值`
          });
          return;
        }
      }

      const response = await apiService.post(`/api/running/instances/${instanceId}/parameters`, parameters);
      
      if (response.success) {
        toast({
          type: "success",
          title: "参数保存成功",
          description: "策略参数已更新并生效"
        });
        setSettingsInstance(null);
        fetchInstances(); // 刷新实例数据
      } else {
        throw new Error(response.message || "保存失败");
      }
    } catch (error: any) {
      toast({
        type: "error",
        title: "保存失败",
        description: error.message || "保存参数失败"
      });
    }
  };

  // 切换实例展开状态
  const toggleExpanded = (instanceId: string) => {
    const newExpanded = new Set(expandedInstances);
    if (newExpanded.has(instanceId)) {
      newExpanded.delete(instanceId);
    } else {
      newExpanded.add(instanceId);
    }
    setExpandedInstances(newExpanded);
  };

  // 状态显示
  const getStatusColor = (status: string) => {
    switch (status) {
      case "running":
        return "bg-green-500";
      case "stopped":
        return "bg-gray-500";
      case "initialized":
        return "bg-yellow-500";
      case "error":
        return "bg-red-500";
      default:
        return "bg-gray-400";
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case "running":
        return "运行中";
      case "stopped":
        return "已停止";
      case "initialized":
        return "已初始化";
      case "error":
        return "错误";
      default:
        return "未知";
    }
  };

  // 格式化运行时间
  const formatRuntime = (seconds: number) => {
    if (seconds < 60) return `${seconds}秒`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}分${seconds % 60}秒`;
    return `${Math.floor(seconds / 3600)}小时${Math.floor((seconds % 3600) / 60)}分`;
  };

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>正在运行的实例</CardTitle>
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
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            正在运行的实例 ({filteredInstances.length})
          </CardTitle>
          <div className="flex items-center gap-4">
            <Select value={selectedOwner} onValueChange={setSelectedOwner}>
              <SelectTrigger className="w-32">
                <SelectValue placeholder="选择拥有者" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部</SelectItem>
                {allOwners.map((owner) => (
                  <SelectItem key={owner} value={owner}>
                    {owner}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
              <DialogTrigger asChild>
                <Button>
                  <Plus className="w-4 h-4 mr-2" />
                  创建实例
                </Button>
              </DialogTrigger>
              <DialogContent className="sm:max-w-md">
                <DialogHeader>
                  <DialogTitle>创建新的交易实例</DialogTitle>
                  <DialogDescription>
                    配置新的交易策略实例。创建后需要手动配置参数并启动。
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-4">
                  <div>
                    <label className="text-sm font-medium">平台</label>
                    <Select
                      value={createForm.platform}
                      onValueChange={(value) => setCreateForm(prev => ({ ...prev, platform: value }))}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="选择交易平台" />
                      </SelectTrigger>
                      <SelectContent>
                        {availablePlatforms.map((platform) => (
                          <SelectItem key={platform.id} value={platform.id}>
                            {platform.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div>
                    <label className="text-sm font-medium">账户</label>
                    <Select
                      value={createForm.account}
                      onValueChange={(value) => setCreateForm(prev => ({ ...prev, account: value }))}
                      disabled={!createForm.platform}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="选择交易账户" />
                      </SelectTrigger>
                      <SelectContent>
                        {availableAccounts
                          .filter(acc => acc.platform === createForm.platform)
                          .map((account) => (
                            <SelectItem key={account.id} value={account.id}>
                              {account.display_name}
                            </SelectItem>
                          ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div>
                    <label className="text-sm font-medium">策略</label>
                    <Select
                      value={createForm.strategy}
                      onValueChange={(value) => setCreateForm(prev => ({ ...prev, strategy: value }))}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="选择交易策略" />
                      </SelectTrigger>
                      <SelectContent>
                        {availableStrategies.map((strategy) => (
                          <SelectItem key={strategy.id} value={strategy.id}>
                            {strategy.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div>
                    <label className="text-sm font-medium">交易对</label>
                    <Input
                      value={createForm.symbol}
                      onChange={(e) => setCreateForm(prev => ({ ...prev, symbol: e.target.value }))}
                      placeholder="如: BTCUSDT"
                    />
                  </div>
                </div>
                <DialogFooter>
                  <Button
                    variant="outline"
                    onClick={() => setShowCreateDialog(false)}
                  >
                    取消
                  </Button>
                  <Button
                    onClick={handleCreateInstance}
                    disabled={isCreating}
                  >
                    {isCreating ? "创建中..." : "创建"}
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>
        </CardHeader>
        <CardContent>
          {filteredInstances.length === 0 ? (
            <div className="text-center py-8">
              <div className="text-gray-400 mb-2">
                <Activity className="h-12 w-12 mx-auto" />
              </div>
              <p className="text-gray-500">没有运行中的实例</p>
              <p className="text-sm text-gray-400 mt-1">点击"创建实例"开始交易</p>
            </div>
          ) : (
            <div className="space-y-4">
              {filteredInstances.map((instance) => (
                <Card key={instance.id} className="border-l-4 border-l-blue-500">
                  <CardHeader className="pb-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <Badge className={cn("text-white", getStatusColor(instance.status))}>
                          {getStatusText(instance.status)}
                        </Badge>
                        <div>
                          <h3 className="font-semibold">
                            {instance.platform.toUpperCase()}-{instance.account}
                          </h3>
                          <p className="text-sm text-gray-500">
                            {getStrategyDisplayName(instance.strategy)} · {instance.symbol}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => setSettingsInstance(instance)}
                        >
                          <Settings className="h-4 w-4" />
                        </Button>
                        <Button
                          size="sm"
                          variant={instance.status === "running" ? "destructive" : "default"}
                          onClick={() => handleToggleStrategy(instance)}
                        >
                          {instance.status === "running" ? (
                            <>
                              <Stop className="h-4 w-4 mr-1" />
                              停止
                            </>
                          ) : (
                            <>
                              <Play className="h-4 w-4 mr-1" />
                              启动
                            </>
                          )}
                        </Button>
                        <AlertDialog>
                          <AlertDialogTrigger asChild>
                            <Button size="sm" variant="destructive">
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </AlertDialogTrigger>
                          <AlertDialogContent>
                            <AlertDialogHeader>
                              <AlertDialogTitle>确认删除</AlertDialogTitle>
                              <AlertDialogDescription>
                                确定要删除实例 {instance.id} 吗？此操作不可撤销。
                              </AlertDialogDescription>
                            </AlertDialogHeader>
                            <AlertDialogFooter>
                              <AlertDialogCancel>取消</AlertDialogCancel>
                              <AlertDialogAction
                                onClick={() => handleDeleteInstance(instance)}
                                className="bg-red-500 hover:bg-red-600"
                              >
                                删除
                              </AlertDialogAction>
                            </AlertDialogFooter>
                          </AlertDialogContent>
                        </AlertDialog>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <Collapsible
                      open={expandedInstances.has(instance.id)}
                      onOpenChange={() => toggleExpanded(instance.id)}
                    >
                      <CollapsibleTrigger asChild>
                        <Button variant="ghost" className="w-full justify-between p-0 h-auto">
                          <div className="grid grid-cols-4 gap-4 w-full text-left py-2">
                            <div className="flex items-center gap-2">
                              <TrendingUp className="h-4 w-4 text-green-500" />
                              <div>
                                <div className="text-sm font-medium">
                                  {instance.profit >= 0 ? '+' : ''}{instance.profit.toFixed(2)} USDT
                                </div>
                                <div className="text-xs text-gray-500">总盈亏</div>
                              </div>
                            </div>
                            <div className="flex items-center gap-2">
                              <Target className="h-4 w-4 text-blue-500" />
                              <div>
                                <div className="text-sm font-medium">{instance.positions}</div>
                                <div className="text-xs text-gray-500">持仓</div>
                              </div>
                            </div>
                            <div className="flex items-center gap-2">
                              <Zap className="h-4 w-4 text-yellow-500" />
                              <div>
                                <div className="text-sm font-medium">{instance.orders}</div>
                                <div className="text-xs text-gray-500">订单</div>
                              </div>
                            </div>
                            <div className="flex items-center gap-2">
                              <Clock className="h-4 w-4 text-gray-500" />
                              <div>
                                <div className="text-sm font-medium">
                                  {formatRuntime(instance.runtime)}
                                </div>
                                <div className="text-xs text-gray-500">运行时间</div>
                              </div>
                            </div>
                          </div>
                          <ChevronDown 
                            className={cn("h-4 w-4 transition-transform", 
                              expandedInstances.has(instance.id) && "transform rotate-180"
                            )} 
                          />
                        </Button>
                      </CollapsibleTrigger>
                      <CollapsibleContent className="mt-4 space-y-2">
                        <div className="grid grid-cols-2 gap-4 text-sm">
                          <div>
                            <span className="text-gray-500">实例ID：</span>
                            <span className="font-mono">{instance.id}</span>
                          </div>
                          <div>
                            <span className="text-gray-500">拥有者：</span>
                            <span>{instance.owner}</span>
                          </div>
                          <div>
                            <span className="text-gray-500">盈利率：</span>
                            <span className={cn(
                              instance.profit_rate >= 0 ? "text-green-600" : "text-red-600"
                            )}>
                              {instance.profit_rate >= 0 ? '+' : ''}{instance.profit_rate.toFixed(2)}%
                            </span>
                          </div>
                          <div>
                            <span className="text-gray-500">最后信号：</span>
                            <span>{instance.last_signal || "无"}</span>
                          </div>
                        </div>
                      </CollapsibleContent>
                    </Collapsible>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* 设置对话框 */}
      <Dialog 
        open={!!settingsInstance} 
        onOpenChange={() => setSettingsInstance(null)}
      >
        <DialogContent className="sm:max-w-4xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              实例设置 - {settingsInstance?.id}
            </DialogTitle>
            <DialogDescription>
              配置策略参数，所有参数必须填写完整且不为0才能保存。
            </DialogDescription>
          </DialogHeader>
          {settingsInstance && (
            <InstanceSettings
              instance={settingsInstance}
              onSave={(params) => handleSaveSettings(settingsInstance.id, params)}
              onCancel={() => setSettingsInstance(null)}
            />
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}