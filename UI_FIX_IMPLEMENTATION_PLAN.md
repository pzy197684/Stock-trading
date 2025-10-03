# UI模块修复实施方案

## 🎯 修复目标

根据UI模块分析报告，针对6个主要模块的问题，按优先级进行系统性修复。

## 🔥 第一阶段：核心数据结构修复

### 1. CurrentRunning模块数据结构统一

**问题**: 前端期望的数据结构与后端API返回格式不匹配
**影响**: 实例列表显示错误，按钮状态异常

**解决方案**:

#### 1.1 统一数据接口类型定义

```typescript
// apps/ui/src/types/api.ts - 新建
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
  tradingPair?: string;         // 兼容字段
  owner?: string;               // 拥有者
}

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}
```

#### 1.2 后端API响应格式标准化

```python
# apps/api/main.py - 更新get_running_instances接口
@app.get("/api/running/instances")
@handle_api_errors
async def get_running_instances():
    """获取当前运行的策略实例 - 标准化响应格式"""
    try:
        instances = []
        
        # 获取所有策略实例
        all_strategies = []
        for account_instances in strategy_manager.strategy_instances.values():
            for instance in account_instances.values():
                all_strategies.append(instance)
        
        logger.log_info(f"Found {len(all_strategies)} total strategy instances")
        
        for strategy_instance in all_strategies:
            try:
                # 标准化数据格式
                instance_data = {
                    "id": getattr(strategy_instance, 'instance_id', 'unknown'),
                    "account": getattr(strategy_instance, 'account', 'unknown'),
                    "platform": getattr(strategy_instance, 'platform', 'unknown'),
                    "strategy": getattr(strategy_instance, 'strategy_name', 'unknown'),
                    "status": normalize_status(strategy_instance),
                    "symbol": normalize_symbol(strategy_instance),
                    "profit": float(getattr(strategy_instance, 'total_profit', 0.0)),
                    "profit_rate": float(getattr(strategy_instance, 'profit_rate', 0.0)),
                    "positions": len(getattr(strategy_instance, 'positions', [])),
                    "orders": len(getattr(strategy_instance, 'orders', [])),
                    "runtime": int(getattr(strategy_instance, 'runtime_seconds', 0)),
                    "last_signal": getattr(strategy_instance, 'last_signal_time', None),
                    "created_at": getattr(strategy_instance, 'created_at', datetime.now().isoformat()),
                    "pid": getattr(strategy_instance, 'pid', None),
                    "owner": get_account_owner(getattr(strategy_instance, 'account', 'unknown'))
                }
                
                # 兼容字段
                instance_data["tradingPair"] = instance_data["symbol"]
                
                instances.append(instance_data)
                
            except Exception as e:
                logger.log_error(f"Error processing strategy instance: {e}")
                continue
        
        # 按创建时间排序
        instances.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        return {
            "success": True,
            "data": {
                "instances": instances,
                "total": len(instances),
                "running": len([i for i in instances if i['status'] == 'running']),
                "stopped": len([i for i in instances if i['status'] == 'stopped'])
            }
        }
        
    except Exception as e:
        logger.log_error(f"获取运行实例失败: {e}")
        return {
            "success": False,
            "error": str(e),
            "data": {
                "instances": [],
                "total": 0,
                "running": 0,
                "stopped": 0
            }
        }

def normalize_status(strategy_instance) -> str:
    """标准化策略状态"""
    try:
        if hasattr(strategy_instance, 'strategy') and hasattr(strategy_instance.strategy, 'status'):
            status_value = strategy_instance.strategy.status
            if hasattr(status_value, 'value'):
                status = status_value.value.lower()
            else:
                status = str(status_value).lower()
        elif hasattr(strategy_instance, 'status'):
            status = str(getattr(strategy_instance, 'status', 'stopped')).lower()
        else:
            status = 'stopped'
        
        # 映射到标准状态
        status_mapping = {
            'active': 'running',
            'inactive': 'stopped',
            'running': 'running',
            'stopped': 'stopped',
            'error': 'error',
            'starting': 'starting'
        }
        
        return status_mapping.get(status, 'stopped')
        
    except Exception:
        return 'stopped'

def normalize_symbol(strategy_instance) -> str:
    """标准化交易对格式"""
    try:
        parameters = getattr(strategy_instance, 'parameters', {})
        symbol = parameters.get('symbol', 'OP/USDT')
        
        # 标准化格式
        if symbol and 'USDT' in symbol and '/' not in symbol:
            symbol = symbol.replace('USDT', '/USDT')
        
        return symbol
        
    except Exception:
        return 'OP/USDT'
```

#### 1.3 前端数据处理优化

```typescript
// apps/ui/src/hooks/useApiData.ts - 更新
export function useApiData() {
  const [state, setState] = useState<ApiDataState>({
    dashboardSummary: null,
    runningInstances: [],
    availablePlatforms: [],
    availableStrategies: [],
    recentLogs: [],
    isLoading: false,
    error: null,
    isConnected: false,
  });

  // 获取运行实例 - 优化版本
  const fetchRunningInstances = useCallback(async () => {
    try {
      setLoading(true);
      const response = await apiService.getRunningInstances();
      
      if (response.success && response.data) {
        // 确保数据结构正确
        const instances = response.data.instances || [];
        
        // 数据验证和清理
        const validatedInstances = instances.map((instance: any) => ({
          id: instance.id || 'unknown',
          account: instance.account || 'unknown',
          platform: instance.platform || 'unknown',
          strategy: instance.strategy || 'unknown',
          status: ['running', 'stopped', 'error', 'starting'].includes(instance.status) 
            ? instance.status : 'stopped',
          symbol: instance.symbol || instance.tradingPair || 'OP/USDT',
          profit: typeof instance.profit === 'number' ? instance.profit : 0,
          profit_rate: typeof instance.profit_rate === 'number' ? instance.profit_rate : 0,
          positions: typeof instance.positions === 'number' ? instance.positions : 0,
          orders: typeof instance.orders === 'number' ? instance.orders : 0,
          runtime: typeof instance.runtime === 'number' ? instance.runtime : 0,
          last_signal: instance.last_signal || null,
          created_at: instance.created_at || new Date().toISOString(),
          pid: instance.pid || null,
          owner: instance.owner || '未知',
          // 兼容字段
          tradingPair: instance.symbol || instance.tradingPair || 'OP/USDT'
        }));
        
        updateState({ 
          runningInstances: validatedInstances,
          error: null 
        });
        
        logger.debug(`成功获取 ${validatedInstances.length} 个实例`);
        
      } else {
        throw new Error(response.error || '获取实例列表失败');
      }
      
    } catch (error) {
      console.error('获取运行实例失败:', error);
      recordMissingFeature('CurrentRunning', 'instances', '运行实例数据获取失败');
      setError(error.message || '获取运行实例失败');
      
      // 设置空数据而不是保持旧数据
      updateState({ runningInstances: [] });
      
    } finally {
      setLoading(false);
    }
  }, [updateState, recordMissingFeature, setError, setLoading]);

  // 实时数据更新
  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8001/ws/logs');
    
    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        
        if (message.type === 'log' && message.data) {
          const logEntry = message.data;
          
          // 检查是否是实例状态更新日志
          if (logEntry.category === 'strategy_status' || 
              logEntry.message.includes('策略') ||
              logEntry.message.includes('实例')) {
            
            // 延迟刷新，避免过于频繁的更新
            setTimeout(() => {
              fetchRunningInstances();
            }, 1000);
          }
        }
        
      } catch (error) {
        console.error('WebSocket消息处理失败:', error);
      }
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket连接错误:', error);
      updateState({ isConnected: false });
    };
    
    ws.onopen = () => {
      console.log('WebSocket连接已建立');
      updateState({ isConnected: true });
    };
    
    ws.onclose = () => {
      console.log('WebSocket连接已关闭');
      updateState({ isConnected: false });
    };
    
    return () => {
      ws.close();
    };
    
  }, [fetchRunningInstances, updateState]);

  return {
    ...state,
    fetchRunningInstances,
    // ... 其他方法
  };
}
```

### 2. 错误处理机制完善

#### 2.1 统一错误处理组件

```typescript
// apps/ui/src/components/ErrorBoundary.tsx - 新建
import React from 'react';
import { Alert, AlertDescription, AlertTitle } from './ui/alert';
import { Button } from './ui/button';
import { RefreshCw, AlertTriangle } from 'lucide-react';

interface ErrorBoundaryState {
  hasError: boolean;
  error?: Error;
  errorInfo?: React.ErrorInfo;
}

interface ErrorBoundaryProps {
  children: React.ReactNode;
  fallback?: React.ComponentType<{error: Error, retry: () => void}>;
}

export class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return {
      hasError: true,
      error
    };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('ErrorBoundary捕获到错误:', error, errorInfo);
    this.setState({
      error,
      errorInfo
    });
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: undefined, errorInfo: undefined });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return <this.props.fallback error={this.state.error!} retry={this.handleRetry} />;
      }

      return (
        <Alert variant="destructive" className="m-4">
          <AlertTriangle className="h-4 w-4" />
          <AlertTitle>组件错误</AlertTitle>
          <AlertDescription className="mt-2">
            <div className="mb-2">
              {this.state.error?.message || '组件渲染时发生未知错误'}
            </div>
            <Button onClick={this.handleRetry} variant="outline" size="sm">
              <RefreshCw className="h-4 w-4 mr-2" />
              重试
            </Button>
          </AlertDescription>
        </Alert>
      );
    }

    return this.props.children;
  }
}

// 错误处理Hook
export const useErrorHandler = () => {
  const handleError = useCallback((error: any, context: string) => {
    console.error(`${context}错误:`, error);
    
    // 这里可以添加错误上报逻辑
    // 例如发送到监控服务
    
    let errorMessage = '未知错误';
    
    if (error?.response?.data?.detail) {
      errorMessage = error.response.data.detail;
    } else if (error?.message) {
      errorMessage = error.message;
    } else if (typeof error === 'string') {
      errorMessage = error;
    }
    
    return {
      title: `${context}失败`,
      message: errorMessage,
      timestamp: new Date().toISOString()
    };
  }, []);
  
  return { handleError };
};
```

#### 2.2 API调用错误处理

```typescript
// apps/ui/src/services/apiService.ts - 更新错误处理
class ApiService {
  // ... 现有代码

  private async makeRequest<T = any>(
    endpoint: string, 
    options: RequestOptions = {}
  ): Promise<ApiResponse<T>> {
    const {
      method = 'GET',
      body,
      headers = {},
      timeout = this.defaultTimeout
    } = options;

    const url = `${this.baseUrl}${endpoint}`;
    const requestHeaders = {
      'Content-Type': 'application/json',
      ...headers
    };

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    try {
      // 添加请求开始日志
      console.debug(`API请求开始: ${method} ${endpoint}`);
      
      const response = await fetch(url, {
        method,
        headers: requestHeaders,
        body: body ? JSON.stringify(body) : undefined,
        signal: controller.signal
      });

      clearTimeout(timeoutId);

      // 详细的响应处理
      if (!response.ok) {
        let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
        
        try {
          const errorData = await response.json();
          if (errorData.detail) {
            errorMessage = errorData.detail;
          } else if (errorData.message) {
            errorMessage = errorData.message;
          }
        } catch {
          // 无法解析响应体，使用状态码信息
        }
        
        console.error(`API请求失败: ${method} ${endpoint} - ${errorMessage}`);
        
        return {
          success: false,
          error: errorMessage
        };
      }

      const data = await response.json();
      
      console.debug(`API请求成功: ${method} ${endpoint}`);
      
      return {
        success: true,
        data
      };

    } catch (error) {
      clearTimeout(timeoutId);
      
      let errorMessage = 'Network error';
      
      if (error instanceof Error) {
        if (error.name === 'AbortError') {
          errorMessage = `请求超时 (${timeout}ms)`;
        } else {
          errorMessage = error.message;
        }
      }
      
      console.error(`API请求异常: ${method} ${endpoint} - ${errorMessage}`);
      
      return {
        success: false,
        error: errorMessage
      };
    }
  }

  // 增强的实例管理方法
  async getRunningInstances(): Promise<ApiResponse> {
    try {
      const response = await this.makeRequest('/api/running/instances');
      
      if (response.success && response.data) {
        // 验证响应数据结构
        if (!response.data.instances || !Array.isArray(response.data.instances)) {
          throw new Error('API响应数据格式错误：缺少instances数组');
        }
        
        // 验证每个实例的必要字段
        const validInstances = response.data.instances.filter((instance: any) => {
          return instance.id && instance.account && instance.platform;
        });
        
        if (validInstances.length !== response.data.instances.length) {
          console.warn(`过滤掉 ${response.data.instances.length - validInstances.length} 个无效实例`);
        }
        
        return {
          success: true,
          data: {
            ...response.data,
            instances: validInstances
          }
        };
      }
      
      return response;
      
    } catch (error) {
      console.error('获取运行实例时发生错误:', error);
      return {
        success: false,
        error: error.message || '获取运行实例失败'
      };
    }
  }
}
```

### 3. 配置文件管理API实现

#### 3.1 后端配置文件管理接口

```python
# apps/api/main.py - 添加配置文件管理接口

@app.get("/api/config/profiles")
@handle_api_errors
async def list_config_profiles():
    """列出所有配置文件"""
    try:
        profiles = {}
        
        # 扫描profiles目录
        profiles_dir = project_root / "profiles"
        if profiles_dir.exists():
            for platform_dir in profiles_dir.iterdir():
                if platform_dir.is_dir() and not platform_dir.name.startswith('_'):
                    platform_name = platform_dir.name
                    profiles[platform_name] = {}
                    
                    for account_dir in platform_dir.iterdir():
                        if account_dir.is_dir():
                            account_name = account_dir.name
                            profiles[platform_name][account_name] = {}
                            
                            # 列出该账户下的所有策略配置
                            for config_file in account_dir.glob("*.json"):
                                if config_file.name != "profile.json":
                                    strategy_name = config_file.stem
                                    profiles[platform_name][account_name][strategy_name] = {
                                        "file_path": str(config_file),
                                        "last_modified": config_file.stat().st_mtime,
                                        "size": config_file.stat().st_size
                                    }
        
        return {
            "success": True,
            "data": {
                "profiles": profiles,
                "total_platforms": len(profiles),
                "total_accounts": sum(len(accounts) for accounts in profiles.values())
            }
        }
        
    except Exception as e:
        logger.log_error(f"列出配置文件失败: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@app.get("/api/config/profiles/{platform}/{account}/{strategy}")
@handle_api_errors
async def get_config_profile(platform: str, account: str, strategy: str):
    """获取特定的配置文件内容"""
    try:
        config_file = project_root / "profiles" / platform / account / f"{strategy}.json"
        
        if not config_file.exists():
            return {
                "success": False,
                "error": f"配置文件不存在: {config_file}"
            }
        
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        return {
            "success": True,
            "data": {
                "config": config_data,
                "file_info": {
                    "path": str(config_file),
                    "last_modified": config_file.stat().st_mtime,
                    "size": config_file.stat().st_size
                }
            }
        }
        
    except Exception as e:
        logger.log_error(f"获取配置文件失败: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/api/config/profiles/{platform}/{account}/{strategy}")
@handle_api_errors
async def save_config_profile(platform: str, account: str, strategy: str, config_data: dict):
    """保存配置文件"""
    try:
        config_dir = project_root / "profiles" / platform / account
        config_dir.mkdir(parents=True, exist_ok=True)
        
        config_file = config_dir / f"{strategy}.json"
        
        # 备份现有文件
        if config_file.exists():
            backup_file = config_file.with_suffix(f".json.backup.{int(time.time())}")
            shutil.copy2(config_file, backup_file)
            logger.log_info(f"已备份配置文件到: {backup_file}")
        
        # 验证配置数据
        validated_config = validate_config_data(config_data, strategy)
        
        # 保存新配置
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(validated_config, f, indent=2, ensure_ascii=False)
        
        logger.log_info(f"配置文件已保存: {config_file}")
        
        # 广播配置更新事件
        await manager.broadcast_log({
            "timestamp": datetime.now().isoformat(),
            "level": "info",
            "message": f"配置文件已更新: {platform}/{account}/{strategy}",
            "source": "ConfigAPI",
            "category": "config_update",
            "data": {
                "platform": platform,
                "account": account,
                "strategy": strategy,
                "file_path": str(config_file)
            }
        })
        
        return {
            "success": True,
            "data": {
                "message": "配置文件保存成功",
                "file_path": str(config_file)
            }
        }
        
    except Exception as e:
        logger.log_error(f"保存配置文件失败: {e}")
        return {
            "success": False,
            "error": str(e)
        }

def validate_config_data(config_data: dict, strategy: str) -> dict:
    """验证配置数据的有效性"""
    validated = config_data.copy()
    
    # 基本验证
    if not isinstance(validated, dict):
        raise ValueError("配置数据必须是字典格式")
    
    # 策略特定验证
    if strategy == "martingale_hedge":
        required_fields = ["symbol", "base_amount", "price_step"]
        for field in required_fields:
            if field not in validated:
                validated[field] = get_default_value(field)
    
    # 数据类型验证
    if "base_amount" in validated:
        try:
            validated["base_amount"] = float(validated["base_amount"])
        except (ValueError, TypeError):
            validated["base_amount"] = 10.0
    
    if "price_step" in validated:
        try:
            validated["price_step"] = float(validated["price_step"])
        except (ValueError, TypeError):
            validated["price_step"] = 0.01
    
    return validated

def get_default_value(field: str):
    """获取字段的默认值"""
    defaults = {
        "symbol": "OP/USDT",
        "base_amount": 10.0,
        "price_step": 0.01,
        "max_orders": 20,
        "hedge_enabled": True
    }
    return defaults.get(field, None)

@app.delete("/api/config/profiles/{platform}/{account}/{strategy}")
@handle_api_errors
async def delete_config_profile(platform: str, account: str, strategy: str):
    """删除配置文件"""
    try:
        config_file = project_root / "profiles" / platform / account / f"{strategy}.json"
        
        if not config_file.exists():
            return {
                "success": False,
                "error": "配置文件不存在"
            }
        
        # 创建备份
        backup_file = config_file.with_suffix(f".json.deleted.{int(time.time())}")
        shutil.move(config_file, backup_file)
        
        logger.log_info(f"配置文件已删除，备份到: {backup_file}")
        
        return {
            "success": True,
            "data": {
                "message": "配置文件删除成功",
                "backup_path": str(backup_file)
            }
        }
        
    except Exception as e:
        logger.log_error(f"删除配置文件失败: {e}")
        return {
            "success": False,
            "error": str(e)
        }
```

这是第一阶段修复的核心内容。接下来我将继续实施这些修复方案。