import React, { useState, useEffect } from "react";
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
import { InstanceSettings } from "./InstanceSettings";
import { useToast } from "./ui/toast";
import {
  ChevronDown,
  Plus,
  Square,
  AlertTriangle,
  Activity,
  TrendingUp,
  TrendingDown,
  Settings,
  Clock,
  Zap,
  Target,
} from "lucide-react";
import { cn } from "./ui/utils";

interface Position {
  long: {
    quantity: number;
    avgPrice: number;
    addCount: number;
    isLocked: boolean;
    isMaxPosition: boolean;
  };
  short: {
    quantity: number;
    avgPrice: number;
    addCount: number;
    isLocked: boolean;
    isMaxPosition: boolean;
  };
}

interface InstanceParameters {
  maxPosition: number;
  riskLevel: number;
  stopLoss: number;
  takeProfit: number;
  autoTrade: boolean;
  notifications: boolean;
  gridSpacing: number;
  maxGrids: number;
}

interface TradingInstance {
  id: string;
  platform: string;
  account: string;
  strategy: string;
  status: "running" | "stopped" | "error";
  owner: string;
  profit: number;
  tradingPair: string;
  pid: number;
  createdAt: string;
  runningTime: number; // in minutes
  currentTime: string;
  positions: Position;
  liquidationPrice: {
    long: number | null;
    short: number | null;
  };
  logs: string[];
  parameters: InstanceParameters;
}

interface CreateForm {
  platform: string;
  account: string;
  strategy: string;
  symbol: string;
}

interface PlatformInfo {
  id: string;
  name: string;
}

interface SymbolInfo {
  symbol: string;
  name: string;
}

interface AccountInfo {
  id: string;
  name: string;
  platform: string;
  status: string;
}

interface StrategyInfo {
  id: string;
  name: string;
}

export function CurrentRunning() {
  const [selectedOwner, setSelectedOwner] =
    useState<string>("all");
  const [showCreateDialog, setShowCreateDialog] =
    useState(false);
  const [expandedInstances, setExpandedInstances] = useState<
    Set<string>
  >(new Set());
  const [settingsInstance, setSettingsInstance] =
    useState<TradingInstance | null>(null);
  const [currentTime, setCurrentTime] = useState(new Date());
  
  // API数据状态
  const [apiInstances, setApiInstances] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);
  
  // 创建实例相关状态
  const [availablePlatforms, setAvailablePlatforms] = useState<PlatformInfo[]>([]);
  const [availableStrategies, setAvailableStrategies] = useState<StrategyInfo[]>([]);
  const [availableAccounts, setAvailableAccounts] = useState<AccountInfo[]>([]);
  const [availableSymbols, setAvailableSymbols] = useState<SymbolInfo[]>([]);
  const [createForm, setCreateForm] = useState<CreateForm>({
    platform: '',
    account: '',
    strategy: '',
    symbol: 'ETHUSDT'
  });
  const [isCreating, setIsCreating] = useState(false);
  
  const { toast } = useToast();

  // 从API获取运行实例
  const fetchRunningInstances = async () => {
    try {
      setIsLoading(true);
      setApiError(null);
      const response = await fetch('http://localhost:8000/api/running/instances');
      if (!response.ok) {
        throw new Error(`API错误: ${response.status}`);
      }
      const data = await response.json();
      setApiInstances(data.instances || []);
    } catch (error) {
      console.error('获取运行实例失败:', error);
      setApiError('无法连接到API服务器');
    } finally {
      setIsLoading(false);
    }
  };

  // 获取可用平台
  const fetchAvailablePlatforms = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/platforms/available');
      if (!response.ok) throw new Error('获取平台列表失败');
      const data = await response.json();
      setAvailablePlatforms(data.platforms || []);
    } catch (error) {
      console.error('获取平台列表失败:', error);
    }
  };

  // 获取可用策略
  const fetchAvailableStrategies = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/strategies/available');
      if (!response.ok) throw new Error('获取策略列表失败');
      const data = await response.json();
      setAvailableStrategies(data.strategies || []);
    } catch (error) {
      console.error('获取策略列表失败:', error);
    }
  };

  // 获取可用交易对
  const fetchAvailableSymbols = async (selectedPlatform?: string) => {
    try {
      const params = selectedPlatform ? `?platform=${selectedPlatform}` : '';
      const response = await fetch(`http://localhost:8000/api/symbols/available${params}`);
      if (!response.ok) throw new Error('获取交易对列表失败');
      const data = await response.json();
      setAvailableSymbols(data.symbols || []);
    } catch (error) {
      console.error('获取交易对列表失败:', error);
    }
  };

  // 获取可用账号（支持平台筛选）
  const fetchAvailableAccounts = async (selectedPlatform?: string) => {
    try {
      const params = selectedPlatform ? `?platform=${selectedPlatform}` : '';
      const response = await fetch(`http://localhost:8000/api/accounts/available${params}`);
      if (!response.ok) throw new Error('获取账号列表失败');
      const data = await response.json();
      setAvailableAccounts(data.accounts || []);
    } catch (error) {
      console.error('获取账号列表失败:', error);
    }
  };

  // 测试账号连接
  const testAccountConnection = async (accountId: string) => {
    try {
      const response = await fetch(`http://localhost:8000/api/accounts/${accountId}/test-connection`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) {
        throw new Error(`连接测试失败: ${response.status}`);
      }
      
      const result = await response.json();
      
      if (result.success) {
        toast({
          type: "success",
          title: "连接成功",
          description: `账号 ${accountId} 连接到 ${result.platform} 成功！`,
        });
      } else {
        toast({
          type: "error",
          title: "连接失败",
          description: result.message || `账号 ${accountId} 连接失败`,
        });
      }
      
      return result;
    } catch (error: any) {
      toast({
        title: "连接错误", 
        description: error.message || '未知错误',
        variant: "destructive",
      });
      return { success: false, message: error.message };
    }
  };

  // 创建新实例
  const createInstance = async () => {
    if (!createForm.platform || !createForm.account || !createForm.strategy || !createForm.symbol) {
      toast({
        title: "参数不完整",
        description: "请填写所有必需字段",
        variant: "destructive",
      });
      return;
    }

    setIsCreating(true);
    try {
      const response = await fetch('http://localhost:8000/api/instances/create', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          account_id: createForm.account,
          platform: createForm.platform,
          strategy: createForm.strategy,
          symbol: createForm.symbol,
          parameters: {
            symbol: createForm.symbol
          }
        }),
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `创建失败: ${response.status}`);
      }
      
      const result = await response.json();
      if (result.success) {
        toast({
          type: "success",
          title: "实例创建成功",
          description: `策略 ${result.strategy} 实例已创建`,
        });
        setShowCreateDialog(false);
        // 重置表单
        setCreateForm({
          platform: '',
          account: '',
          strategy: '',
          symbol: 'ETHUSDT'
        });
        fetchRunningInstances(); // 刷新数据
      } else {
        throw new Error(result.message || '创建失败');
      }
    } catch (error: any) {
      console.error('创建实例失败:', error);
      toast({
        title: "创建失败", 
        description: error.message || '未知错误',
        variant: "destructive",
      });
    } finally {
      setIsCreating(false);
    }
  };

  // 启动策略
  const startStrategy = async (accountId: string, strategyName: string, parameters: any = {}) => {
    try {
      const response = await fetch('http://localhost:8000/api/strategy/start', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          account_id: accountId,
          strategy_name: strategyName,
          parameters,
        }),
      });
      
      if (!response.ok) {
        throw new Error(`启动失败: ${response.status}`);
      }
      
      const result = await response.json();
      if (result.success) {
        toast({
          type: "success",
          title: "策略启动成功",
          description: result.message,
        });
        fetchRunningInstances(); // 刷新数据
      } else {
        throw new Error(result.message);
      }
    } catch (error: any) {
      console.error('启动策略失败:', error);
      toast({
        type: "error",
        title: "启动失败",
        description: error.message || '未知错误',
      });
    }
  };

  // 停止策略
  const stopStrategy = async (accountId: string, instanceId: string) => {
    try {
      const response = await fetch('http://localhost:8000/api/strategy/stop', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          account_id: accountId,
          instance_id: instanceId,
        }),
      });
      
      if (!response.ok) {
        throw new Error(`停止失败: ${response.status}`);
      }
      
      const result = await response.json();
      if (result.success) {
        toast({
          type: "success",
          title: "策略停止成功",
          description: result.message,
        });
        fetchRunningInstances(); // 刷新数据
      } else {
        throw new Error(result.message);
      }
    } catch (error) {
      console.error('停止策略失败:', error);
      toast({
        type: "error",
        title: "停止失败",
        description: (error as Error).message || '未知错误',
      });
    }
  };

  // 初始化和定期刷新数据
  useEffect(() => {
    fetchRunningInstances();
    fetchAvailablePlatforms();
    fetchAvailableStrategies();
    // 不再默认加载账号和交易对，等待用户选择平台
    
    const interval = setInterval(fetchRunningInstances, 30000); // 每30秒刷新
    return () => clearInterval(interval);
  }, []);

  // Update current time every second
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  // 直接使用API数据
  const instances = apiInstances.map(apiInstance => ({
    id: apiInstance.id,
    platform: apiInstance.platform,
    account: apiInstance.account,
    strategy: apiInstance.strategy,
    status: apiInstance.status,
    owner: apiInstance.account, // 使用account作为owner
    profit: apiInstance.profit || 0,
    tradingPair: "BTC/USDT", // 默认交易对，API暂不支持
    pid: Math.floor(Math.random() * 99999), // 模拟PID
    createdAt: new Date().toLocaleString("zh-CN"),
    runningTime: apiInstance.runtime || 0,
    currentTime: currentTime.toLocaleString("zh-CN"),
    positions: {
      long: {
        quantity: 0,
        avgPrice: 0,
        addCount: 0,
        isLocked: false,
        isMaxPosition: false,
      },
      short: {
        quantity: 0,
        avgPrice: 0,
        addCount: 0,
        isLocked: false,
        isMaxPosition: false,
      },
    },
    liquidationPrice: {
      long: null,
      short: null,
    },
    logs: [`策略 ${apiInstance.strategy} 运行中...`],
    parameters: apiInstance.parameters || {
      maxPosition: 50,
      riskLevel: 50,
      stopLoss: 8,
      takeProfit: 15,
      autoTrade: true,
      notifications: true,
      gridSpacing: 0.5,
      maxGrids: 20,
    },
  }));

  const owners = [
    "all",
    ...Array.from(new Set(instances.map((i) => i.owner))),
  ];
  const filteredInstances =
    selectedOwner === "all"
      ? instances
      : instances.filter((i) => i.owner === selectedOwner);

  const toggleExpanded = (instanceId: string) => {
    const newExpanded = new Set(expandedInstances);
    if (newExpanded.has(instanceId)) {
      newExpanded.delete(instanceId);
    } else {
      newExpanded.add(instanceId);
    }
    setExpandedInstances(newExpanded);
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "running":
        return (
          <Badge className="bg-green-100 text-green-800 border-green-200">
            运行中
          </Badge>
        );
      case "stopped":
        return (
          <Badge className="bg-gray-100 text-gray-800 border-gray-200">
            已停止
          </Badge>
        );
      case "error":
        return (
          <Badge className="bg-red-100 text-red-800 border-red-200">
            错误
          </Badge>
        );
      default:
        return <Badge>未知</Badge>;
    }
  };

  const formatRunningTime = (minutes: number) => {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return `${hours}小时${mins}分钟`;
  };

  const handleParametersChange = (
    instanceId: string,
    newParameters: InstanceParameters,
  ) => {
    // 对于API实例，这里应该调用更新参数的API
    console.log('更新参数:', instanceId, newParameters);
    // 暂时不支持API参数更新，记录待实现功能
  };

  const handleDeleteInstance = (instanceId: string) => {
    // 对于API实例，调用停止策略API
    const instance = instances.find(i => i.id === instanceId);
    if (instance && apiInstances.length > 0) {
      stopStrategy(instance.account, instanceId);
    }
  };

  // 平台变更处理函数
  const handlePlatformChange = async (platform: string) => {
    setCreateForm(prev => ({
      ...prev, 
      platform, 
      symbol: '', 
      account: ''
    }));
    
    // 加载该平台的交易对
    try {
      const symbolsResponse = await fetch(`http://localhost:8000/api/symbols/available?platform=${platform}`);
      if (symbolsResponse.ok) {
        const data = await symbolsResponse.json();
        setAvailableSymbols(data.symbols || []);
      } else {
        setAvailableSymbols([]);
      }
    } catch (error) {
      console.error('获取交易对失败:', error);
      setAvailableSymbols([]);
    }
    
    // 加载该平台的账号
    try {
      const accountsResponse = await fetch(`http://localhost:8000/api/accounts/available?platform=${platform}`);
      if (accountsResponse.ok) {
        const data = await accountsResponse.json();
        setAvailableAccounts(data.accounts || []);
      } else {
        setAvailableAccounts([]);
      }
    } catch (error) {
      console.error('获取账号失败:', error);
      setAvailableAccounts([]);
    }
  };

  // 账号变更处理函数
  const handleAccountChange = async (accountId: string) => {
    setCreateForm(prev => ({...prev, account: accountId}));
    
    // 测试账号连接
    try {
      const testResponse = await fetch(`http://localhost:8000/api/accounts/${accountId}/test-connection`, {
        method: 'POST'
      });
      
      if (testResponse.ok) {
        const result = await testResponse.json();
        if (result.connected) {
          toast({
            type: "success",
            title: "账号连接成功",
            description: `${result.account_name || accountId} 连接正常`,
          });
        } else {
          toast({
            type: "error",
            title: "账号连接失败",
            description: result.error || "无法连接到交易平台",
          });
        }
      }
    } catch (error) {
      console.error('测试账号连接失败:', error);
      toast({
        type: "error",
        title: "连接测试失败",
        description: "无法测试账号连接",
      });
    }
  };

  return (
    <div className="space-y-4 md:space-y-6">
      {/* 加载状态和错误显示 */}
      {isLoading && (
        <div className="text-center text-muted-foreground py-4">
          正在加载运行实例...
        </div>
      )}
      {apiError && (
        <div className="text-sm text-amber-600 bg-amber-50 p-3 rounded border">
          ⚠️ {apiError}
        </div>
      )}
      
      {/* Owner Filter and Add Button */}
      <div className="flex items-center justify-between gap-2 md:gap-4">
        <div className="flex items-center gap-2 md:gap-4">
          <label className="text-sm whitespace-nowrap">
            拥有人筛选:
          </label>
          <Select
            value={selectedOwner}
            onValueChange={setSelectedOwner}
          >
            <SelectTrigger className="w-32 md:w-48">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">全部</SelectItem>
              {owners.slice(1).map((owner) => (
                <SelectItem key={owner} value={owner}>
                  {owner}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <Dialog
          open={showCreateDialog}
          onOpenChange={setShowCreateDialog}
        >
          <DialogTrigger asChild>
            {/* 添加新实例按钮 */}
            <Button>
              <Plus className="w-4 h-4 mr-2" />
              <span className="hidden sm:inline">
                添加新实例
              </span>
              <span className="sm:hidden">添加</span>
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-md">
            <div className="sticky top-0 bg-[rgba(255,255,255,0)] z-10 border-b pb-4 mb-4">
              <DialogHeader className="bg-[rgba(255,255,255,0)]">
                <DialogTitle>创建新交易实例</DialogTitle>
                <DialogDescription>
                  选择平台、账号和策略来创建新的交易实例
                </DialogDescription>
              </DialogHeader>
            </div>
            <div className="space-y-4 max-h-[60vh] md:max-h-96 overflow-y-auto pr-2 -mr-2">
              <div>
                <label className="text-sm font-medium">
                  交易平台 *
                </label>
                <Select value={createForm.platform} onValueChange={handlePlatformChange}>
                  <SelectTrigger>
                    <SelectValue placeholder="请先选择交易平台" />
                  </SelectTrigger>
                  <SelectContent>
                    {availablePlatforms.map((platform: PlatformInfo) => (
                      <SelectItem key={platform.id} value={platform.id}>
                        {platform.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-sm font-medium">
                  交易对 *
                </label>
                <Select 
                  value={createForm.symbol} 
                  onValueChange={(value: string) => setCreateForm((prev: CreateForm) => ({...prev, symbol: value}))}
                  disabled={!createForm.platform}
                >
                  <SelectTrigger>
                    <SelectValue placeholder={createForm.platform ? "选择交易对" : "请先选择平台"} />
                  </SelectTrigger>
                  <SelectContent>
                    {availableSymbols.map((symbol: SymbolInfo) => (
                      <SelectItem key={symbol.symbol} value={symbol.symbol}>
                        {symbol.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-sm font-medium">
                  账号 *
                </label>
                <Select 
                  value={createForm.account} 
                  onValueChange={handleAccountChange}
                  disabled={!createForm.platform}
                >
                  <SelectTrigger>
                    <SelectValue placeholder={createForm.platform ? "选择账号" : "请先选择平台"} />
                  </SelectTrigger>
                  <SelectContent>
                    {availableAccounts.length > 0 && (
                      availableAccounts.map((account: AccountInfo) => (
                        <SelectItem key={account.id} value={account.id}>
                          {account.name} ({account.platform || '未知平台'})
                          <Badge variant="outline" className="ml-2 text-xs">
                            {account.status}
                          </Badge>
                        </SelectItem>
                      ))
                    )}
                  </SelectContent>
                </Select>
                {createForm.platform && availableAccounts.length === 0 && (
                  <p className="text-xs text-muted-foreground mt-1">
                    该平台暂无配置账号，请先在 profiles/ 目录下配置账号
                  </p>
                )}
              </div>
              <div>
                <label className="text-sm font-medium">
                  交易策略
                </label>
                <Select value={createForm.strategy} onValueChange={(value: string) => setCreateForm((prev: CreateForm) => ({...prev, strategy: value}))}>
                  <SelectTrigger>
                    <SelectValue placeholder="选择策略" />
                  </SelectTrigger>
                  <SelectContent>
                    {availableStrategies.map((strategy: StrategyInfo) => (
                      <SelectItem key={strategy.id} value={strategy.id}>
                        {strategy.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="flex-shrink-0 bg-background border-t pt-4 mt-4">
              <DialogFooter>
                <Button
                  variant="outline"
                  onClick={() => setShowCreateDialog(false)}
                >
                  取消
                </Button>
                <Button
                  onClick={createInstance}
                  disabled={isCreating}
                >
                  {isCreating ? '创建中...' : '创建实例'}
                </Button>
              </DialogFooter>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* Running Instances */}
      {filteredInstances.length === 0 ? (
        <Card>
          <CardContent className="text-center py-12">
            <div className="flex flex-col items-center gap-4">
              <div className="w-16 h-16 bg-muted rounded-full flex items-center justify-center">
                <Activity className="w-8 h-8 text-muted-foreground" />
              </div>
              <div>
                <h3 className="text-lg font-medium">暂无运行实例</h3>
                <p className="text-muted-foreground mt-1">
                  {isLoading 
                    ? "正在加载运行实例..." 
                    : apiError 
                    ? "无法连接到API服务器" 
                    : "当前没有策略在运行，点击上方按钮添加新的交易实例"
                  }
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      ) : (
      <div className="space-y-3 md:space-y-4">
        {filteredInstances.map((instance) => (
          <Card
            key={instance.id}
            className="w-full overflow-hidden instance-card relative"
          >
            <div className="flex">
              {/* Left content area - takes most of the space */}
              <div className="flex-1 pr-20">
                <CardHeader className="pb-2 md:pb-3">
                  <div className="flex items-center justify-between gap-2 md:gap-4">
                    <div className="flex items-center gap-2 md:gap-4 flex-1 min-w-0">
                      <CardTitle className="text-base md:text-lg truncate">
                        {instance.account}
                      </CardTitle>
                      {getStatusBadge(instance.status)}
                      <span className="text-xs md:text-sm text-muted-foreground hidden sm:block">
                        拥有人: {instance.owner}
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div
                        className={cn(
                          "flex items-center gap-1 px-2 py-1 rounded text-xs md:text-sm whitespace-nowrap",
                          instance.profit >= 0
                            ? "text-green-600 bg-green-50"
                            : "text-red-600 bg-red-50",
                        )}
                      >
                        {instance.profit >= 0 ? (
                          <TrendingUp className="w-3 h-3 md:w-4 md:h-4" />
                        ) : (
                          <TrendingDown className="w-3 h-3 md:w-4 md:h-4" />
                        )}
                        <span className="font-medium">
                          {instance.profit >= 0 ? "+" : ""}
                          {instance.profit.toFixed(2)} USDT
                        </span>
                      </div>
                    </div>
                  </div>
                </CardHeader>

                <CardContent className="pt-0 space-y-4">
                  {/* Basic Info Grid */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-2 md:gap-4 text-xs md:text-sm">
                    <div>
                      <span className="text-muted-foreground">
                        运行平台
                      </span>
                      <p className="font-medium">
                        {instance.platform}
                      </p>
                    </div>
                    <div>
                      <span className="text-muted-foreground">
                        交易对
                      </span>
                      <p className="font-medium">
                        {instance.tradingPair}
                      </p>
                    </div>
                    <div>
                      <span className="text-muted-foreground">
                        策略
                      </span>
                      <p className="font-medium">
                        {instance.strategy}
                      </p>
                    </div>
                    <div>
                      <span className="text-muted-foreground">
                        PID进程
                      </span>
                      <p className="font-medium font-mono">
                        {instance.pid}
                      </p>
                    </div>
                  </div>

                  {/* Time Info */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-2 md:gap-4 text-xs md:text-sm bg-muted/30 p-2 md:p-3 rounded">
                    <div className="flex items-center gap-2">
                      <Clock className="w-3 h-3 md:w-4 md:h-4 text-muted-foreground" />
                      <div>
                        <span className="text-muted-foreground">
                          创建时间
                        </span>
                        <p className="font-medium font-mono">
                          {instance.createdAt}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Activity className="w-3 h-3 md:w-4 md:h-4 text-muted-foreground" />
                      <div>
                        <span className="text-muted-foreground">
                          运行时长
                        </span>
                        <p className="font-medium">
                          {formatRunningTime(
                            instance.runningTime,
                          )}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Zap className="w-3 h-3 md:w-4 md:h-4 text-muted-foreground" />
                      <div>
                        <span className="text-muted-foreground">
                          当前时间
                        </span>
                        <p className="font-medium font-mono">
                          {instance.currentTime}
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Action Buttons */}
                  <div className="flex gap-2 flex-wrap">
                    <AlertDialog>
                      <AlertDialogTrigger asChild>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() =>
                            toast({
                              type: "warning",
                              title: "准备停止策略",
                            })
                          }
                        >
                          <Square className="w-3 h-3 md:w-4 md:h-4 mr-1" />
                          停止策略
                        </Button>
                      </AlertDialogTrigger>
                      <AlertDialogContent>
                        <AlertDialogHeader>
                          <AlertDialogTitle>
                            确认停止策略
                          </AlertDialogTitle>
                          <AlertDialogDescription>
                            您确定要停止 {instance.account} 的{" "}
                            {instance.strategy} 吗？
                          </AlertDialogDescription>
                        </AlertDialogHeader>
                        <AlertDialogFooter>
                          <AlertDialogCancel>
                            取消
                          </AlertDialogCancel>
                          <AlertDialogAction
                            onClick={() =>
                              toast({
                                type: "success",
                                title: "策略已停止",
                              })
                            }
                          >
                            确认停止
                          </AlertDialogAction>
                        </AlertDialogFooter>
                      </AlertDialogContent>
                    </AlertDialog>

                    <AlertDialog>
                      <AlertDialogTrigger asChild>
                        <Button
                          variant="destructive"
                          size="sm"
                          onClick={() =>
                            toast({
                              type: "error",
                              title: "准备紧急平仓",
                            })
                          }
                        >
                          <AlertTriangle className="w-3 h-3 md:w-4 md:h-4 mr-1" />
                          <span className="hidden sm:inline">
                            一键平仓并停止
                          </span>
                          <span className="sm:hidden">
                            平仓
                          </span>
                        </Button>
                      </AlertDialogTrigger>
                      <AlertDialogContent>
                        <AlertDialogHeader>
                          <AlertDialogTitle>
                            确认平仓并停止
                          </AlertDialogTitle>
                          <AlertDialogDescription>
                            这将立即平仓所有持仓并停止策略，此操作不可撤销。您确定要继续吗？
                          </AlertDialogDescription>
                        </AlertDialogHeader>
                        <AlertDialogFooter>
                          <AlertDialogCancel>
                            取消
                          </AlertDialogCancel>
                          <AlertDialogAction
                            className="bg-destructive text-destructive-foreground"
                            onClick={() =>
                              toast({
                                type: "success",
                                title: "已平仓并停止",
                                description: "所有持仓已清空",
                              })
                            }
                          >
                            确认平仓并停止
                          </AlertDialogAction>
                        </AlertDialogFooter>
                      </AlertDialogContent>
                    </AlertDialog>

                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        setSettingsInstance(instance);
                        toast({
                          type: "info",
                          title: "打开实例设置",
                        });
                      }}
                    >
                      <Settings className="w-3 h-3 md:w-4 md:h-4 mr-1" />
                      设置
                    </Button>
                  </div>
                </CardContent>
              </div>

              {/* Right side expand button - full height */}
              <div className="absolute top-0 right-0 h-full w-16 md:w-20">
                <Collapsible
                  open={expandedInstances.has(instance.id)}
                  onOpenChange={() =>
                    toggleExpanded(instance.id)
                  }
                >
                  <CollapsibleTrigger asChild>
                    <Button
                      variant="ghost"
                      className={cn(
                        "!h-full !min-h-full w-full flex flex-col items-center justify-center gap-2 transition-all duration-300 rounded-l-lg rounded-r-none border-l border-border/30 !p-2",
                        expandedInstances.has(instance.id)
                          ? "bg-primary/10 hover:bg-primary/15 text-primary border-primary/20"
                          : "bg-muted/30 hover:bg-muted/50 text-muted-foreground"
                      )}
                      style={{ height: '100%', minHeight: '100%' }}
                      onClick={(e) => {
                        e.preventDefault();
                        toggleExpanded(instance.id);
                        // 平滑滚动到合适位置
                        setTimeout(() => {
                          if (
                            !expandedInstances.has(
                              instance.id,
                            )
                          ) {
                            const element =
                              e.currentTarget.closest(
                                ".instance-card",
                              );
                            if (element) {
                              element.scrollIntoView({
                                behavior: "smooth",
                                block: "nearest",
                              });
                            }
                          }
                        }, 100);
                      }}
                    >
                      <span className="text-xs md:text-sm text-center leading-tight">
                        {expandedInstances.has(instance.id)
                          ? "收起\n详情"
                          : "展开\n详情"}
                      </span>
                      <ChevronDown
                        className={cn(
                          "w-4 h-4 transition-transform duration-300",
                          expandedInstances.has(
                            instance.id,
                          ) && "rotate-180",
                        )}
                      />
                    </Button>
                  </CollapsibleTrigger>
                </Collapsible>
              </div>
            </div>

            {/* Expanded content */}
            <Collapsible
              open={expandedInstances.has(instance.id)}
            >
              <CollapsibleContent className="space-y-4 animate-in slide-in-from-top-2 duration-300 px-4 pb-4">
                {/* Position Snapshot - Now in expanded area */}
                <div className="space-y-3 bg-muted/20 md:p-4 rounded-[10px] border-t bg-[rgba(237,240,236,0.99)] px-[15px] py-[12px] mt-[0px] mr-[5px] mb-[16px] ml-[5px]">
                  <h4 className="font-medium text-sm flex items-center gap-2">
                    <Target className="w-4 h-4" />
                    仓位快照
                  </h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {/* Long Position */}
                    <div className="border rounded p-3 bg-green-50/50">
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-medium text-green-700">
                          多仓
                        </span>
                        <div className="flex gap-1">
                          {instance.positions.long
                            .isLocked && (
                            <Badge
                              variant="outline"
                              className="text-xs border-orange-200 text-orange-700"
                            >
                              锁仓
                            </Badge>
                          )}
                          {instance.positions.long
                            .isMaxPosition && (
                            <Badge
                              variant="outline"
                              className="text-xs border-red-200 text-red-700"
                            >
                              满仓
                            </Badge>
                          )}
                        </div>
                      </div>
                      <div className="grid grid-cols-2 gap-2 text-xs">
                        <div>
                          <span className="text-muted-foreground">
                            数量
                          </span>
                          <p className="font-medium">
                            {instance.positions.long.quantity}{" "}
                            {
                              instance.tradingPair.split(
                                "/",
                              )[0]
                            }
                          </p>
                        </div>
                        <div>
                          <span className="text-muted-foreground">
                            均价
                          </span>
                          <p className="font-medium">
                            $
                            {instance.positions.long.avgPrice.toLocaleString()}
                          </p>
                        </div>
                        <div>
                          <span className="text-muted-foreground">
                            加仓次数
                          </span>
                          <p className="font-medium">
                            {instance.positions.long.addCount}
                            次
                          </p>
                        </div>
                        <div>
                          <span className="text-muted-foreground">
                            强平价格
                          </span>
                          <p className="font-medium text-red-600">
                            {instance.liquidationPrice.long
                              ? `$${instance.liquidationPrice.long.toLocaleString()}`
                              : "无"}
                          </p>
                        </div>
                      </div>
                    </div>

                    {/* Short Position */}
                    <div className="border rounded p-3 bg-red-50/50">
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-medium text-red-700">
                          空仓
                        </span>
                        <div className="flex gap-1">
                          {instance.positions.short
                            .isLocked && (
                            <Badge
                              variant="outline"
                              className="text-xs border-orange-200 text-orange-700"
                            >
                              锁仓
                            </Badge>
                          )}
                          {instance.positions.short
                            .isMaxPosition && (
                            <Badge
                              variant="outline"
                              className="text-xs border-red-200 text-red-700"
                            >
                              满仓
                            </Badge>
                          )}
                        </div>
                      </div>
                      <div className="grid grid-cols-2 gap-2 text-xs">
                        <div>
                          <span className="text-muted-foreground">
                            数量
                          </span>
                          <p className="font-medium">
                            {
                              instance.positions.short
                                .quantity
                            }{" "}
                            {
                              instance.tradingPair.split(
                                "/",
                              )[0]
                            }
                          </p>
                        </div>
                        <div>
                          <span className="text-muted-foreground">
                            均价
                          </span>
                          <p className="font-medium">
                            $
                            {instance.positions.short.avgPrice.toLocaleString()}
                          </p>
                        </div>
                        <div>
                          <span className="text-muted-foreground">
                            加仓次数
                          </span>
                          <p className="font-medium">
                            {
                              instance.positions.short
                                .addCount
                            }
                            次
                          </p>
                        </div>
                        <div>
                          <span className="text-muted-foreground">
                            强平价格
                          </span>
                          <p className="font-medium text-red-600">
                            {instance.liquidationPrice.short
                              ? `$${instance.liquidationPrice.short.toLocaleString()}`
                              : "无"}
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="border rounded-lg p-3 md:p-4 bg-muted/50">
                  <h4 className="font-medium mb-2 flex items-center gap-2">
                    <Activity className="w-4 h-4" />
                    详细状态
                  </h4>
                  <div className="grid grid-cols-2 gap-2 md:gap-4 text-xs md:text-sm">
                    <div>今日交易次数: 42</div>
                    <div>成功率: 78.5%</div>
                    <div>最大回撤: -2.3%</div>
                    <div>夏普比率: 1.65</div>
                  </div>
                </div>

                <div className="border rounded-lg p-3 md:p-4 bg-muted/50">
                  <h4 className="font-medium mb-2">
                    最近日志
                  </h4>
                  <div className="space-y-1 text-xs md:text-sm text-muted-foreground max-h-32 overflow-y-auto">
                    {instance.logs.map((log, index) => (
                      <div key={index} className="font-mono">
                        {log}
                      </div>
                    ))}
                  </div>
                </div>

                <div className="border rounded-lg p-3 md:p-4 bg-muted/50">
                  <h4 className="font-medium mb-2">
                    收益波浪图
                  </h4>
                  <div className="h-16 md:h-20 flex items-end gap-1">
                    {Array.from({ length: 20 }, (_, i) => (
                      <div
                        key={i}
                        className="bg-blue-500 w-2 rounded-t"
                        style={{
                          height: `${Math.random() * 80 + 10}%`,
                        }}
                      />
                    ))}
                  </div>
                </div>
              </CollapsibleContent>
            </Collapsible>
          </Card>
        ))}

        {/* Add New Instance Card */}
        <Card className="w-full border-dashed border-2 border-muted-foreground/25">
          <CardContent className="flex items-center justify-center p-6 md:p-8">
            <Button
              variant="ghost"
              className="h-auto flex-col gap-2"
            >
              <Plus className="w-6 h-6 md:w-8 md:h-8 text-muted-foreground" />
              <span className="text-sm md:text-base text-muted-foreground">
                添加新实例
              </span>
            </Button>
          </CardContent>
        </Card>
      </div>
      )}

      {/* Instance Settings Dialog */}
      {settingsInstance && (
        <InstanceSettings
          open={!!settingsInstance}
          onOpenChange={(open) =>
            !open && setSettingsInstance(null)
          }
          instanceId={settingsInstance.id}
          instanceName={settingsInstance.account}
          platform={settingsInstance.platform}
          currentParameters={settingsInstance.parameters}
          onParametersChange={(params) =>
            handleParametersChange(settingsInstance.id, params)
          }
          onDeleteInstance={() =>
            handleDeleteInstance(settingsInstance.id)
          }
        />
      )}
    </div>
  );
}