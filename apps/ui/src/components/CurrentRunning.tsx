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
} from "lucide-react";
import { cn } from "./ui/utils";
import { getStrategyDisplayName } from "../utils/strategyNames";

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
  statistics: {
    daily_trades: number;
    success_rate: number;
    max_drawdown: number;
    sharpe_ratio: number;
  };
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
  
  // 使用ApiContext的数据
  const { 
    runningInstances: apiInstances = [], 
    error: apiError,
    fetchRunningInstances
  } = useApiData();
  const isLoading = false; // ApiContext处理loading状态
  
  // 添加调试日志
  console.log('CurrentRunning组件渲染，apiInstances:', apiInstances);
  console.log('apiInstances长度:', apiInstances?.length || 0);
  console.log('apiError:', apiError);
  
  // 显示实例数量的窗口提醒
  useEffect(() => {
    if (apiInstances && apiInstances.length > 0) {
      console.log(`数据加载成功：找到 ${apiInstances.length} 个实例`);
    } else {
      console.log('数据加载问题：没有找到实例数据');
    }
  }, [apiInstances]);
  
  // 添加类型断言，确保TypeScript知道数据结构
  const typedApiInstances = (apiInstances as any[]) || [];
  
  // 创建实例相关状态
  const [availablePlatforms, setAvailablePlatforms] = useState<PlatformInfo[]>([]);
  const [availableStrategies, setAvailableStrategies] = useState<StrategyInfo[]>([]);
  const [availableAccounts, setAvailableAccounts] = useState<AccountInfo[]>([]);
  const [allOwners, setAllOwners] = useState<string[]>([]);
  const [availableSymbols, setAvailableSymbols] = useState<SymbolInfo[]>([]);
  const [accountsLoading, setAccountsLoading] = useState(false);
  const [customSymbol, setCustomSymbol] = useState('');
  const [symbolInputMode, setSymbolInputMode] = useState<'select' | 'input'>('select');
  const [customSymbolHistory, setCustomSymbolHistory] = useState<string[]>([]);
  const [createForm, setCreateForm] = useState<CreateForm>({
    platform: '',
    account: '',
    strategy: '',
    symbol: DEFAULT_CONFIG.trading.symbol
  });
  const [isCreating, setIsCreating] = useState(false);
  
  const { toast } = useToast();

  // 初始化时获取数据
  useEffect(() => {
    console.log('CurrentRunning组件初始化，获取实例数据...');
    fetchRunningInstances();
  }, [fetchRunningInstances]);

  // 本地存储键名
  const CUSTOM_SYMBOLS_KEY = 'trading_custom_symbols_history';
  
  // 加载自定义交易对历史
  const loadCustomSymbolHistory = () => {
    try {
      const stored = localStorage.getItem(CUSTOM_SYMBOLS_KEY);
      return stored ? JSON.parse(stored) : [];
    } catch (error) {
      console.error('加载自定义交易对历史失败:', error);
      return [];
    }
  };

  // 保存自定义交易对到历史
  const saveCustomSymbol = (symbol: string) => {
    try {
      const history = loadCustomSymbolHistory();
      const newHistory = [symbol, ...history.filter((s: string) => s !== symbol)].slice(0, 20); // 最多保存20个
      localStorage.setItem(CUSTOM_SYMBOLS_KEY, JSON.stringify(newHistory));
      setCustomSymbolHistory(newHistory);
    } catch (error) {
      console.error('保存自定义交易对失败:', error);
    }
  };

  // 初始化时加载历史记录
  useEffect(() => {
    const history = loadCustomSymbolHistory();
    setCustomSymbolHistory(history);
  }, []);

  // 转换API参数到UI参数结构
  const convertToUIParameters = (apiParams: any): InstanceParameters => {
    if (!apiParams) {
      // 返回默认参数
      return {
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
        },
        autoTrade: true,
        notifications: true
      };
    }
    
    // 如果已经是正确的结构，确保所有字段都有默认值
    if (apiParams.long && apiParams.short && apiParams.hedge) {
      return {
        ...apiParams,
        autoTrade: apiParams.autoTrade ?? true,
        notifications: apiParams.notifications ?? true,
        advanced: {
          symbol: apiParams.symbol || 'OPUSDT',
          leverage: apiParams.leverage || 5,
          mode: apiParams.mode || 'dual',
          order_type: apiParams.order_type || 'MARKET',
          interval: apiParams.interval || 5,
          max_daily_loss: apiParams.max_daily_loss || apiParams.risk_control?.max_daily_loss || 100.0,
          emergency_stop_loss: apiParams.emergency_stop_loss || apiParams.risk_control?.emergency_stop_loss || 0.1,
          enable_logging: apiParams.monitoring?.enable_logging ?? true,
          enable_performance_monitoring: apiParams.monitoring?.enable_performance_monitoring ?? false,
          enable_webhooks: apiParams.monitoring?.enable_webhooks ?? false
        } as any  // 使用 any 避免类型冲突，因为这个对象会在其他地方被展开使用
      };
    }
    
    // 否则返回默认值
    return {
      long: {
        first_qty: apiParams.first_qty || 0.01,
        add_ratio: apiParams.add_ratio || 2.0,
        add_interval: apiParams.add_interval || 0.02,
        max_add_times: apiParams.max_add_times || 3,
        tp_first_order: apiParams.tp_first_order || 0.01,
        tp_before_full: apiParams.tp_before_full || 0.015,
        tp_after_full: apiParams.tp_after_full || 0.02
      },
      short: {
        first_qty: apiParams.first_qty || 0.01,
        add_ratio: apiParams.add_ratio || 2.0,
        add_interval: apiParams.add_interval || 0.02,
        max_add_times: apiParams.max_add_times || 3,
        tp_first_order: apiParams.tp_first_order || 0.01,
        tp_before_full: apiParams.tp_before_full || 0.015,
        tp_after_full: apiParams.tp_after_full || 0.02
      },
      hedge: {
        trigger_loss: apiParams.trigger_loss || 0.05,
        equal_eps: apiParams.equal_eps || 0.01,
        min_wait_seconds: apiParams.min_wait_seconds || 60,
        release_tp_after_full: { long: 0.02, short: 0.02 },
        release_sl_loss_ratio: { long: 1.0, short: 1.0 }
      },
      autoTrade: apiParams.autoTrade ?? true,
      notifications: apiParams.notifications ?? true
    };
  };

  // 获取可用平台
  const fetchAvailablePlatforms = async () => {
    try {
      const result = await apiService.getAvailablePlatforms();
      if (result.success && result.data) {
        setAvailablePlatforms(result.data.platforms || []);
      } else {
        console.error('获取平台列表失败:', result.error);
      }
    } catch (error) {
      console.error('获取平台列表失败:', error);
    }
  };

  // 获取可用策略
  const fetchAvailableStrategies = async () => {
    try {
      const result = await apiService.getAvailableStrategies();
      if (result.success && result.data) {
        setAvailableStrategies(result.data.strategies || []);
      } else {
        console.error('获取策略列表失败:', result.error);
      }
    } catch (error) {
      console.error('获取策略列表失败:', error);
    }
  };

  // 获取所有账号的拥有人信息
  const fetchAllOwners = async () => {
    try {
      const result = await apiService.getAvailableAccounts();
      if (result.success && result.data) {
        const owners = Array.from(new Set(result.data.accounts.map((acc: any) => acc.owner).filter(Boolean))) as string[];
        setAllOwners(owners);
      } else {
        console.error('获取账号列表失败:', result.error);
      }
    } catch (error) {
      console.error('获取拥有人列表失败:', error);
    }
  };







  // 重置创建表单
  const resetCreateForm = () => {
    setCreateForm({
      platform: '',
      account: '',
      strategy: '',
      symbol: ''
    });
    setAvailableSymbols([]);
    setAvailableAccounts([]);
  };

  // 处理创建对话框状态变化
  const handleCreateDialogChange = (open: boolean) => {
    setShowCreateDialog(open);
    if (open) {
      // 对话框打开时重置表单
      resetCreateForm();
    }
  };

  // 创建新实例
  const createInstance = async () => {
    // 详细的表单验证
    const missingFields = [];
    if (!createForm.platform) missingFields.push('交易平台');
    if (!createForm.symbol) missingFields.push('交易对');
    if (!createForm.account) missingFields.push('交易账号');
    if (!createForm.strategy) missingFields.push('交易策略');

    if (missingFields.length > 0) {
      toast({
        type: "error",
        title: "参数不完整",
        description: `请选择：${missingFields.join('、')}`,
      });
      return;
    }

    setIsCreating(true);
    try {
      const instanceData = {
        account_id: createForm.account,
        platform: createForm.platform,
        strategy: createForm.strategy,
        symbol: createForm.symbol,
        parameters: {
          symbol: createForm.symbol
        }
      };
      
      const result = await apiService.createInstance(instanceData);
      
      if (result.success && result.data?.success) {
        // 保存交易对到历史记录
        if (createForm.symbol) {
          saveCustomSymbol(createForm.symbol);
        }
        
        toast({
          type: "success",
          title: "实例创建成功",
          description: `策略 ${getStrategyDisplayName(result.data.strategy)} 实例已创建`,
        });
        setShowCreateDialog(false);
        // 重置表单和相关状态
        resetCreateForm();
        // 立即刷新数据显示
        fetchRunningInstances();
      } else {
        // 显示API返回的具体错误信息
        const errorMsg = result.error || result.data?.message || '创建失败';
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
        description: errorMessage,
      });
    } finally {
      setIsCreating(false);
    }
  };

  // 启动策略
  const startStrategy = async (accountId: string, instanceId: string) => {
    try {
      const result = await apiService.startStrategy(accountId, instanceId);
      
      if (result.success && result.data?.success) {
        toast({
          type: "success",
          title: "策略启动成功",
          description: `实例 ${instanceId} 已开始运行`,
        });
        // 立即刷新数据显示
        fetchRunningInstances();
      } else {
        throw new Error(result.message || result.data?.message || '启动失败');
      }
    } catch (error) {
      console.error('启动策略失败:', error);
      toast({
        type: "error",
        title: "策略启动失败",
        description: (error as Error).message || '未知错误',
      });
    }
  };

  // 停止策略
  const stopStrategy = async (accountId: string, instanceId: string) => {
    try {
      const result = await apiService.stopStrategy(accountId, instanceId);
      
      if (result.success && result.data?.success) {
        toast({
          type: "success",
          title: "策略停止成功",
          description: `实例 ${instanceId} 已停止运行`,
        });
        // 立即刷新数据显示
        fetchRunningInstances();
      } else {
        throw new Error(result.message || result.data?.message || '停止失败');
      }
    } catch (error) {
      console.error('停止策略失败:', error);
      toast({
        type: "error",
        title: "策略停止失败",
        description: (error as Error).message || '未知错误',
      });
    }
  };

  // 一键平仓并停止策略
  const forceCloseAndStop = async (accountId: string, instanceId: string) => {
    try {
      const result = await apiService.forceStopInstance(accountId, instanceId);
      
      if (result.success && result.data?.success) {
        toast({
          type: "success",
          title: "紧急平仓成功",
          description: `平仓${result.data.details.positions_closed}个持仓，撤销${result.data.details.orders_cancelled}个订单`,
        });
        // 立即刷新数据显示
        fetchRunningInstances();
      } else {
        throw new Error(result.message);
      }
    } catch (error) {
      console.error('紧急平仓失败:', error);
      toast({
        type: "error",
        title: "紧急平仓失败",
        description: (error as Error).message || '未知错误',
      });
    }
  };

  // 初始化和定期刷新数据
  useEffect(() => {
    fetchAvailablePlatforms();
    fetchAvailableStrategies();
    fetchAllOwners(); // 加载所有拥有人信息
    // 不再默认加载账号和交易对，等待用户选择平台
    // 删除了重复的刷新逻辑，现在使用ApiContext统一管理
  }, []);

  // Update current time every second
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  // 添加自动刷新数据的效果
  useEffect(() => {
    // 立即执行一次刷新
    fetchRunningInstances();
    
    const refreshTimer = setInterval(() => {
      fetchRunningInstances(); // 每5秒刷新一次实例数据
    }, 5000);
    return () => clearInterval(refreshTimer);
  }, [fetchRunningInstances]); // 现在fetchRunningInstances用useCallback包装，不会无限循环

  // 直接使用API数据
  const instances = typedApiInstances.map((apiInstance: any) => ({
    id: apiInstance.id,
    platform: apiInstance.platform,
    account: apiInstance.account,
    strategy: apiInstance.strategy,
    status: apiInstance.status,
    owner: apiInstance.owner || '未知', // 使用API返回的真实拥有人信息
    profit: typeof apiInstance.profit === 'number' && !isNaN(apiInstance.profit) ? apiInstance.profit : 0,
    tradingPair: apiInstance.tradingPair || apiInstance.symbol || "OP/USDT", // 使用API返回的交易对信息
    pid: apiInstance.pid || (() => {
      // 如果API没有返回PID，从字符串ID中提取数字部分作为备选
      if (apiInstance.id) {
        const match = apiInstance.id.toString().match(/(\d+)$/);
        if (match) {
          return parseInt(match[1], 10);
        }
      }
      // 如果无法提取，使用哈希值
      return Math.abs((apiInstance.platform + apiInstance.account + apiInstance.strategy).split('').reduce((a: number, b: string) => { a = ((a << 5) - a) + b.charCodeAt(0); return a & a; }, 0));
    })(), // 优先使用API返回的真实PID
    createdAt: apiInstance.createdAt || new Date().toLocaleString("zh-CN"),
    runningTime: apiInstance.runningTime || (typeof apiInstance.runtime === 'number' && !isNaN(apiInstance.runtime) ? Math.floor(apiInstance.runtime / 60) : 0),
    currentTime: currentTime.toLocaleString("zh-CN", { 
      year: 'numeric', 
      month: '2-digit', 
      day: '2-digit', 
      hour: '2-digit', 
      minute: '2-digit', 
      second: '2-digit' 
    }), // 始终使用本地实时时间，确保每秒更新
    positions: apiInstance.positions || {
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
    liquidationPrice: apiInstance.liquidationPrice || {
      long: null,
      short: null,
    },
    logs: [`策略 ${getStrategyDisplayName(apiInstance.strategy)} 运行中...`],
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
    // 添加统计数据字段
    statistics: {
      daily_trades: apiInstance.daily_trades || 0,
      success_rate: apiInstance.success_rate || 0,
      max_drawdown: apiInstance.max_drawdown || 0,
      sharpe_ratio: apiInstance.sharpe_ratio || 0,
    },
  }));

  console.log('转换后的instances:', instances);
  console.log('instances长度:', instances.length);

  // 合并运行实例的拥有人和所有账号的拥有人信息
  const owners = [
    "all",
    ...Array.from(new Set([
      ...instances.map((i) => i.owner),
      ...allOwners
    ])).filter(Boolean),
  ];
  const filteredInstances =
    selectedOwner === "all"
      ? instances
      : instances.filter((i) => i.owner === selectedOwner);

  console.log('filteredInstances:', filteredInstances);
  console.log('filteredInstances.length:', filteredInstances.length);
  console.log('selectedOwner:', selectedOwner);

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
      case "initialized":
        return (
          <Badge className="bg-blue-100 text-blue-800 border-blue-200">
            已初始化
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
    const validMinutes = typeof minutes === 'number' && !isNaN(minutes) ? minutes : 0;
    const hours = Math.floor(validMinutes / 60);
    const mins = Math.floor(validMinutes % 60);
    return `${hours}小时${mins}分钟`;
  };

  const handleParametersChange = async (
    instanceId: string,
    newParameters: InstanceParameters,
  ) => {
    try {
      console.log('更新参数:', instanceId, newParameters);
      console.log('前端传入的杠杆值:', (newParameters as any).leverage || newParameters.advanced?.leverage);
      
      // 将UI参数转换为API参数格式
      // 注意：InstanceSettings传来的参数可能是展平结构，需要适配
      const apiParameters = {
        symbol: (newParameters as any).symbol || newParameters.advanced?.symbol || DEFAULT_CONFIG.trading.symbol,
        leverage: (newParameters as any).leverage || newParameters.advanced?.leverage || DEFAULT_CONFIG.trading.leverage,
        mode: (newParameters as any).mode || newParameters.advanced?.mode || DEFAULT_CONFIG.trading.mode,
        order_type: (newParameters as any).order_type || newParameters.advanced?.order_type || DEFAULT_CONFIG.trading.order_type,
        interval: (newParameters as any).interval || newParameters.advanced?.interval || DEFAULT_CONFIG.trading.interval,
        long: newParameters.long,
        short: newParameters.short,
        hedge: newParameters.hedge,
        safety: {
          require_manual_start: (newParameters.advanced as any)?.require_manual_start ?? !newParameters.autoTrade,
          auto_stop_on_error: (newParameters.advanced as any)?.auto_stop_on_error ?? DEFAULT_CONFIG.safety.auto_stop_on_error,
          max_consecutive_losses: (newParameters.advanced as any)?.max_consecutive_losses ?? DEFAULT_CONFIG.safety.max_consecutive_losses,
          circuit_breaker: {
            enabled: (newParameters.advanced as any)?.circuit_breaker_enabled ?? DEFAULT_CONFIG.safety.circuit_breaker_enabled,
            max_drawdown: (newParameters.advanced as any)?.circuit_breaker_max_drawdown ?? DEFAULT_CONFIG.safety.circuit_breaker_max_drawdown
          }
        },
        risk_control: {
          max_daily_loss: (newParameters as any).max_daily_loss || (newParameters.advanced?.max_daily_loss ?? DEFAULT_CONFIG.risk_control.max_daily_loss),
          emergency_stop_loss: (newParameters as any).emergency_stop_loss || (newParameters.advanced?.emergency_stop_loss ?? DEFAULT_CONFIG.risk_control.emergency_stop_loss),
          max_total_qty: (newParameters as any).max_total_qty || ((newParameters.advanced as any)?.max_total_qty ?? DEFAULT_CONFIG.risk_control.max_total_qty),
          tp_slippage: (newParameters as any).tp_slippage || ((newParameters.advanced as any)?.tp_slippage ?? DEFAULT_CONFIG.risk_control.tp_slippage)
        },
        execution: {
          max_slippage: (newParameters.advanced as any)?.max_slippage ?? DEFAULT_CONFIG.execution.max_slippage,
          retry_attempts: (newParameters.advanced as any)?.retry_attempts ?? DEFAULT_CONFIG.execution.retry_attempts,
          order_timeout: (newParameters.advanced as any)?.order_timeout ?? DEFAULT_CONFIG.execution.order_timeout,
          enable_order_confirmation: (newParameters.advanced as any)?.enable_order_confirmation ?? DEFAULT_CONFIG.execution.enable_order_confirmation
        },
        monitoring: {
          enable_logging: (newParameters as any).enable_logging || (newParameters.advanced?.enable_logging ?? DEFAULT_CONFIG.monitoring.enable_logging),
          enable_alerts: (newParameters as any).enable_alerts || (newParameters.notifications ?? DEFAULT_CONFIG.monitoring.enable_alerts),
          log_level: (newParameters as any).log_level || ((newParameters.advanced as any)?.log_level ?? DEFAULT_CONFIG.monitoring.log_level)
        }
      };
      
      console.log('发送到API的参数:', JSON.stringify(apiParameters, null, 2));
      
      // 调用API更新参数
      const result = await apiService.updateInstanceParameters(instanceId, apiParameters);
      
      if (result.success && result.data?.success) {
        console.log('参数更新成功');
        // 重新加载实例列表以反映更新
        await fetchRunningInstances();
      } else {
        console.error('运行实例更新失败:', result.error);
        console.log('尝试直接更新配置文件...');
        
        // 如果运行实例更新失败，直接更新配置文件
        // 从实例ID推断平台和账户信息
        const platform = instanceId.startsWith('BN') ? 'BINANCE' : 
                         instanceId.startsWith('CW') ? 'COINW' : 
                         instanceId.startsWith('OK') ? 'OKX' : 'BINANCE';
        const account = instanceId;
        const strategy = 'martingale_hedge'; // 默认策略
        
        const configResult = await apiService.updateProfileConfig(platform, account, strategy, apiParameters);
        
        if (configResult.success) {
          console.log('配置文件更新成功');
          // 重新加载实例列表以反映更新
          await fetchRunningInstances();
        } else {
          console.error('配置文件更新也失败:', configResult.error);
          alert('参数保存失败，请检查控制台日志');
        }
      }
    } catch (error) {
      console.error('更新参数时发生错误:', error);
    }
  };

  const handleDeleteInstance = async (instanceId: string) => {
    try {
      // 对于API实例，调用删除实例API
      const instance = instances.find((i: any) => i.id === instanceId);
      if (instance && typedApiInstances.length > 0) {
        console.log('删除实例:', instanceId, '账号:', instance.account);
        
        // 调用真实的删除API
        const deleteResult = await apiService.deleteInstance(instance.account, instanceId);
        
        if (deleteResult.success) {
          // 删除成功后刷新数据
          await fetchRunningInstances();
          
          // 关闭设置对话框
          setSettingsInstance(null);
          
          toast({
            type: "success",
            title: "实例删除成功",
            description: `实例 ${instanceId} 已成功删除`,
          });
        } else {
          throw new Error(deleteResult.error || "删除失败");
        }
      }
    } catch (error: any) {
      console.error('删除实例失败:', error);
      
      // 如果是包含错误编码的错误，显示中文说明
      let errorMessage = `删除实例 ${instanceId} 时发生错误`;
      if (error.response && error.response.detail) {
        const detail = error.response.detail;
        if (detail.message) {
          errorMessage = detail.message;
        }
        if (detail.solution) {
          errorMessage += `\n解决方案: ${detail.solution}`;
        }
      }
      
      toast({
        type: "error",
        title: "删除失败",
        description: errorMessage,
      });
    }
  };

  // 平台变更处理函数
  const handlePlatformChange = async (platform: string) => {
    console.log('🔄 Platform changed to:', platform);
    console.log('🔄 Previous availableAccounts:', availableAccounts.length);
    
    setCreateForm(prev => ({
      ...prev, 
      platform, 
      symbol: '', 
      account: ''
    }));
    
    // 加载该平台的交易对
    try {
      console.log('📡 Fetching symbols for platform:', platform);
      const result = await apiService.getAvailableSymbols(platform);
      if (result.success && result.data) {
        console.log('✅ Symbols loaded:', result.data.symbols?.length || 0);
        setAvailableSymbols(result.data.symbols || []);
      } else {
        console.error('❌ Failed to load symbols:', result.error);
        setAvailableSymbols([]);
      }
    } catch (error) {
      console.error('获取交易对失败:', error);
      setAvailableSymbols([]);
    }
    
    // 加载该平台的账号
    try {
      setAccountsLoading(true);
      console.log('📡 Fetching accounts for platform:', platform);
      const result = await apiService.getAvailableAccounts(platform);
      if (result.success && result.data) {
        console.log('✅ Accounts loaded:', result.data.accounts?.length || 0, result.data.accounts);
        setAvailableAccounts(result.data.accounts || []);
      } else {
        console.error('❌ Failed to load accounts:', result.error);
        setAvailableAccounts([]);
      }
    } catch (error) {
      console.error('获取账号失败:', error);
      setAvailableAccounts([]);
    } finally {
      setAccountsLoading(false);
    }
  };

  // 账号变更处理函数
  const handleAccountChange = async (accountId: string) => {
    setCreateForm(prev => ({...prev, account: accountId}));
    
    console.log('账号变更:', accountId);
    
    try {
      const connectionData = {
        platform: createForm.platform,
        account_id: accountId
      };
      
      const result = await apiService.testConnection(connectionData);
      
      console.log('连接测试响应:', result);
      
      if (result.success && result.data) {
        console.log('连接测试结果:', result.data);
        
        if (result.data.success) {
          toast({
            type: "success",
            title: "账号连接成功",
            description: `${accountId} 连接正常`,
          });
        } else {
          // 处理示例账号的预期失败情况
          if (result.data.status === "connection_failed" && 
              (result.data.message?.includes("401") || result.data.message?.includes("API密钥无效"))) {
            toast({
              type: "warning", 
              title: "示例账号已选择",
              description: `${accountId} - 这是示例账号，API密钥无效但可用于演示`,
            });
          } else {
            toast({
              type: "error",
              title: "账号连接失败",
              description: result.data.message || "无法连接到交易平台",
            });
          }
        }
      } else {
        throw new Error(result.error || "连接测试失败");
      }
    } catch (error) {
      console.error('测试账号连接失败:', error);
      toast({
        type: "error",
        title: "连接测试失败",
        description: "无法测试账号连接，请检查API服务器状态",
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

        <div className="flex items-center gap-2">
          {/* 刷新数据按钮 */}
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              console.log('手动刷新数据...');
              fetchRunningInstances();
            }}
          >
            刷新
          </Button>

          <Dialog
            open={showCreateDialog}
            onOpenChange={handleCreateDialogChange}
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
                <Select 
                  value={createForm.platform} 
                  onValueChange={(value) => {
                    console.log('🎯 Platform select onValueChange triggered:', value);
                    handlePlatformChange(value);
                  }}
                >
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
                <div className="space-y-2">
                  <div className="flex items-center space-x-2">
                    <Button
                      type="button"
                      variant={symbolInputMode === 'select' ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => setSymbolInputMode('select')}
                    >
                      选择
                    </Button>
                    <Button
                      type="button"
                      variant={symbolInputMode === 'input' ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => setSymbolInputMode('input')}
                    >
                      手动输入
                    </Button>
                  </div>
                  
                  {symbolInputMode === 'select' ? (
                    <Select 
                      value={createForm.symbol} 
                      onValueChange={(value: string) => setCreateForm((prev: CreateForm) => ({...prev, symbol: value}))}
                      disabled={!createForm.platform}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder={createForm.platform ? "选择交易对" : "请先选择平台"} />
                      </SelectTrigger>
                      <SelectContent>
                        {/* 历史记录分组 */}
                        {customSymbolHistory.length > 0 && (
                          <>
                            <div className="px-2 py-1.5 text-xs font-semibold text-muted-foreground">
                              历史记录
                            </div>
                            {customSymbolHistory.map((symbol: string) => (
                              <SelectItem key={`history-${symbol}`} value={symbol}>
                                <div className="flex items-center space-x-2">
                                  <span>{symbol}</span>
                                  <span className="text-xs text-muted-foreground">(历史)</span>
                                </div>
                              </SelectItem>
                            ))}
                            {availableSymbols.length > 0 && (
                              <div className="px-2 py-1.5 text-xs font-semibold text-muted-foreground border-t">
                                平台交易对
                              </div>
                            )}
                          </>
                        )}
                        {/* 平台交易对 */}
                        {availableSymbols.map((symbol: SymbolInfo) => (
                          <SelectItem key={symbol.symbol} value={symbol.symbol}>
                            {symbol.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  ) : (
                    <div className="space-y-2">
                      <Input
                        value={customSymbol}
                        onChange={(e) => setCustomSymbol(e.target.value.toUpperCase())}
                        placeholder="输入交易对，如：BTCUSDT, ETHUSDT"
                        className="w-full"
                      />
                      <div className="flex items-center space-x-2">
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            if (customSymbol.trim()) {
                              const symbol = customSymbol.trim();
                              setCreateForm((prev: CreateForm) => ({...prev, symbol}));
                              // 保存到历史记录
                              saveCustomSymbol(symbol);
                            }
                          }}
                          disabled={!customSymbol.trim()}
                        >
                          确认使用
                        </Button>
                        <span className="text-xs text-muted-foreground">
                          当前: {createForm.symbol || '未选择'}
                        </span>
                      </div>
                      <div className="text-xs text-muted-foreground">
                        <p>• 输入格式：基础货币+计价货币，如 BTCUSDT、ETHUSDT</p>
                        <p>• 请确保交易对在选定平台上可用</p>
                      </div>
                    </div>
                  )}
                </div>
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
                    <SelectValue placeholder={
                      accountsLoading ? "加载账号中..." : 
                      createForm.platform ? `选择账号 (共${availableAccounts.length}个)` : 
                      "请先选择平台"
                    } />
                  </SelectTrigger>
                  <SelectContent>
                    {(() => {
                      console.log('🚀 Account SelectContent render - platform:', createForm.platform, 'accounts:', availableAccounts.length);
                      return availableAccounts.map((account: AccountInfo) => (
                        <SelectItem key={account.id} value={account.id}>
                          {account.name} ({account.platform || '未知平台'})
                          <Badge variant="outline" className="ml-2 text-xs">
                            {account.status}
                          </Badge>
                        </SelectItem>
                      ));
                    })()}
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
                        {getStrategyDisplayName(strategy.id)}
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
                  disabled={isCreating || !createForm.platform || !createForm.symbol || !createForm.account || !createForm.strategy}
                >
                  {isCreating ? '创建中...' : '创建实例'}
                </Button>
              </DialogFooter>
            </div>
          </DialogContent>
          </Dialog>
        </div>
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
                        {instance.owner}
                      </CardTitle>
                      {getStatusBadge(instance.status)}
                      <span className="text-xs md:text-sm text-muted-foreground hidden sm:block">
                        账号: {instance.account}
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
                          {(typeof instance.profit === 'number' && !isNaN(instance.profit) ? instance.profit : 0).toFixed(2)} USDT
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
                        {getStrategyDisplayName(instance.strategy)}
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
                    {/* 启动/停止策略按钮 - 根据状态动态显示 */}
                    {instance.status === 'running' ? (
                      <AlertDialog>
                        <AlertDialogTrigger asChild>
                          <Button
                            variant="outline"
                            size="sm"
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
                              {getStrategyDisplayName(instance.strategy)} 吗？
                            </AlertDialogDescription>
                          </AlertDialogHeader>
                          <AlertDialogFooter>
                            <AlertDialogCancel>
                              取消
                            </AlertDialogCancel>
                            <AlertDialogAction
                              onClick={async () => {
                                await stopStrategy(instance.account, instance.id);
                              }}
                            >
                              确认停止
                            </AlertDialogAction>
                          </AlertDialogFooter>
                        </AlertDialogContent>
                      </AlertDialog>
                    ) : (
                      <AlertDialog>
                        <AlertDialogTrigger asChild>
                          <Button
                            variant="default"
                            size="sm"
                            className="bg-green-600 hover:bg-green-700"
                          >
                            <Target className="w-3 h-3 md:w-4 md:h-4 mr-1" />
                            开始策略
                          </Button>
                        </AlertDialogTrigger>
                        <AlertDialogContent>
                          <AlertDialogHeader>
                            <AlertDialogTitle>
                              确认启动策略
                            </AlertDialogTitle>
                            <AlertDialogDescription>
                              您确定要启动 {instance.account} 的{" "}
                              {getStrategyDisplayName(instance.strategy)} 吗？请确保参数配置正确。
                            </AlertDialogDescription>
                          </AlertDialogHeader>
                          <AlertDialogFooter>
                            <AlertDialogCancel>
                              取消
                            </AlertDialogCancel>
                            <AlertDialogAction
                              onClick={async () => {
                                await startStrategy(instance.account, instance.id);
                              }}
                              className="bg-green-600 hover:bg-green-700"
                            >
                              确认启动
                            </AlertDialogAction>
                          </AlertDialogFooter>
                        </AlertDialogContent>
                      </AlertDialog>
                    )}

                    <AlertDialog>
                      <AlertDialogTrigger asChild>
                        <Button
                          variant="destructive"
                          size="sm"
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
                            onClick={async () => {
                              try {
                                await forceCloseAndStop(instance.account, instance.id);
                              } catch (error) {
                                console.error('一键平仓失败:', error);
                              }
                            }}
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
                              ? `$${(instance.liquidationPrice.long as number).toLocaleString()}`
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
                              ? `$${(instance.liquidationPrice.short as number).toLocaleString()}`
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
                    <div>今日交易次数: {instance.statistics.daily_trades}</div>
                    <div>成功率: {instance.statistics.success_rate.toFixed(1)}%</div>
                    <div>最大回撤: {instance.statistics.max_drawdown.toFixed(1)}%</div>
                    <div>夏普比率: {instance.statistics.sharpe_ratio.toFixed(2)}</div>
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
          currentParameters={convertToUIParameters(settingsInstance.parameters)}
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