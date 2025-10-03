// 统一的API类型定义
// 解决前后端数据结构不一致问题

export interface TradingInstance {
  id: string;                    // 实例ID
  account: string;              // 账户名称  
  platform: string;            // 平台名称
  strategy: string;             // 策略名称
  status: 'running' | 'stopped' | 'error' | 'starting';
  symbol: string;               // 交易对
  profit: number;               // 盈亏金额
  profit_rate: number;          // 盈亏比率
  positions: number;            // 持仓数量
  orders: number;               // 订单数量
  runtime: number;              // 运行时间(秒)
  last_signal?: string;         // 最后信号时间
  created_at: string;           // 创建时间
  pid?: number;                 // 进程ID
  tradingPair?: string;         // 兼容字段，等同于symbol
  owner?: string;               // 拥有者
}

export interface CreateInstanceRequest {
  account_id: string;
  platform: string;
  strategy: string;
  symbol: string;
  parameters?: Record<string, any>;
}

export interface PlatformInfo {
  id: string;
  name: string;
  status?: 'active' | 'inactive';
  supported_features?: string[];
}

export interface AccountInfo {
  id: string;
  name: string;
  platform: string;
  status: 'active' | 'inactive' | 'error';
  balance?: number;
  owner?: string;
}

export interface StrategyInfo {
  id: string;
  name: string;
  display_name?: string;
  category?: string;
  description?: string;
  supported_platforms?: string[];
  parameters?: Record<string, any>;
}

export interface LogEntry {
  timestamp: string;
  level: 'debug' | 'info' | 'warning' | 'error' | 'critical' | 'trade';
  message: string;
  source?: string;
  category?: string;
  data?: any;
  file?: string;
  function?: string;
  line?: number;
}

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface DashboardSummary {
  total_accounts: number;
  total_balance: number;
  total_profit: number;
  profit_rate: number;
  running_strategies: number;
  total_trades?: number;
  success_rate?: number;
  daily_profit?: number;
  system_status?: string;
}

export interface InstancesResponse {
  instances: TradingInstance[];
  total: number;
  running: number;
  stopped: number;
}

export interface ConfigProfile {
  platform: string;
  account: string;
  strategy: string;
  config: Record<string, any>;
  file_info?: {
    path: string;
    last_modified: number;
    size: number;
  };
}

export interface ConfigProfilesResponse {
  profiles: Record<string, Record<string, Record<string, any>>>;
  total_platforms: number;
  total_accounts: number;
}

// WebSocket消息类型
export interface WebSocketMessage {
  type: 'log' | 'instance_update' | 'system_status' | 'heartbeat';
  data?: any;
  timestamp: string;
}

// 错误处理类型
export interface ErrorInfo {
  title: string;
  message: string;
  timestamp: string;
  context?: string;
  code?: string;
}

// 组件Props类型
export interface ErrorBoundaryProps {
  children: React.ReactNode;
  fallback?: React.ComponentType<{error: Error, retry: () => void}>;
}

// Hook返回类型
export interface ApiDataState {
  dashboardSummary: DashboardSummary | null;
  runningInstances: TradingInstance[];
  availablePlatforms: PlatformInfo[];
  availableStrategies: StrategyInfo[];
  recentLogs: LogEntry[];
  isLoading: boolean;
  error: string | null;
  isConnected: boolean;
}

export interface UseApiDataReturn extends ApiDataState {
  fetchRunningInstances: () => Promise<void>;
  fetchDashboardSummary: () => Promise<void>;
  fetchAvailablePlatforms: () => Promise<void>;
  fetchAvailableStrategies: () => Promise<void>;
  fetchRecentLogs: (limit?: number, level?: string) => Promise<void>;
  startStrategy: (accountId: string, strategyName: string, parameters: any) => Promise<ApiResponse>;
  stopStrategy: (accountId: string, instanceId: string) => Promise<ApiResponse>;
  createInstance: (request: CreateInstanceRequest) => Promise<ApiResponse>;
  recordMissingFeature: (component: string, feature: string, description: string) => void;
}

// 表单类型
export interface CreateForm {
  platform: string;
  account: string;
  strategy: string;
  symbol: string;
  parameters?: Record<string, any>;
}

// 策略参数类型
export interface StrategyParameters {
  symbol: string;
  base_amount: number;
  price_step: number;
  max_orders?: number;
  hedge_enabled?: boolean;
  [key: string]: any;
}

// 实例设置类型
export interface InstanceSettings {
  parameters: StrategyParameters;
  autoTrade: boolean;
  notifications: boolean;
}

// 系统设置类型
export interface GlobalSettings {
  appearance: {
    theme: 'light' | 'dark' | 'system';
    language: string;
    timezone: string;
    fontSize: number;
  };
  notifications: {
    enableDesktop: boolean;
    enableEmail: boolean;
    enableSound: boolean;
    tradingAlerts: boolean;
    systemAlerts: boolean;
    profitLossAlerts: boolean;
    emailAddress: string;
    soundVolume: number;
  };
  security: {
    enableTwoFactor: boolean;
    sessionTimeout: number;
    enableEncryption: boolean;
    logLevel: string;
    autoLogout: boolean;
    autoTradeMode: boolean;
  };
  performance: {
    maxConcurrentConnections: number;
    cacheTimeout: number;
    enableCompression: boolean;
    optimizeMemory: boolean;
  };
  backup: {
    autoBackup: boolean;
    backupInterval: number;
    backupLocation: string;
    keepBackups: number;
  };
}

// 验证函数类型
export type ConfigValidator = (config: any) => string[];
export type DataNormalizer<T> = (data: any) => T;

// 常量
export const INSTANCE_STATUS = {
  RUNNING: 'running',
  STOPPED: 'stopped',
  ERROR: 'error',
  STARTING: 'starting'
} as const;

export const LOG_LEVELS = {
  DEBUG: 'debug',
  INFO: 'info',
  WARNING: 'warning',
  ERROR: 'error',
  CRITICAL: 'critical',
  TRADE: 'trade'
} as const;

export const WEBSOCKET_MESSAGE_TYPES = {
  LOG: 'log',
  INSTANCE_UPDATE: 'instance_update',
  SYSTEM_STATUS: 'system_status',
  HEARTBEAT: 'heartbeat'
} as const;