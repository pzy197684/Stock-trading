// apps/ui/src/services/apiClient.ts
// API 客户端服务，用于与后端API通信

export interface DashboardSummary {
  summary: {
    total_accounts: number;
    total_balance: number;
    total_profit: number;
    profit_rate: number;
    running_strategies: number;
  };
  accounts: AccountInfo[];
}

export interface AccountInfo {
  id: string;
  platform: string;
  status: 'connected' | 'disconnected' | 'error';
  balance: number;
  profit: number;
  profit_rate: number;
  strategy: string | null;
  last_update: string;
}

export interface StrategyInstance {
  id: string;
  account: string;
  platform: string;
  strategy: string;
  status: 'running' | 'stopped' | 'error';
  profit: number;
  profit_rate: number;
  positions: number;
  orders: number;
  runtime: number;
  last_signal: string | null;
  parameters: Record<string, any>;
}

export interface Platform {
  id: string;
  name: string;
  status: 'available' | 'unavailable';
  capabilities: Record<string, any>;
  icon: string;
}

export interface Strategy {
  id: string;
  name: string;
  version: string;
  description: string;
  parameters: Record<string, any>;
  supported_platforms: string[];
}

export interface LogEntry {
  timestamp: string;
  level: string;
  message: string;
  source: string;
}

export interface SystemStatus {
  status: string;
  timestamp: string;
  missing_features: number;
}

class ApiClient {
  private baseUrl = 'http://localhost:8000';
  private ws: WebSocket | null = null;

  async get<T>(endpoint: string): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`);
    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }
    return response.json();
  }

  async post<T>(endpoint: string, data?: any): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: data ? JSON.stringify(data) : undefined,
    });
    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }
    return response.json();
  }

  // 仪表板数据
  async getDashboardSummary(): Promise<DashboardSummary> {
    return this.get('/api/dashboard/summary');
  }

  // 运行中的实例
  async getRunningInstances(): Promise<{ instances: StrategyInstance[] }> {
    return this.get('/api/running/instances');
  }

  // 可用平台
  async getAvailablePlatforms(): Promise<{ platforms: Platform[] }> {
    return this.get('/api/platforms/available');
  }

  // 可用策略
  async getAvailableStrategies(): Promise<{ strategies: Strategy[] }> {
    return this.get('/api/strategies/available');
  }

  // 账号状态
  async getAccountStatus(accountId: string): Promise<AccountInfo> {
    return this.get(`/api/accounts/${accountId}/status`);
  }

  // 启动策略
  async startStrategy(accountId: string, strategyName: string, parameters?: Record<string, any>): Promise<{ success: boolean; message: string; instance_id?: string }> {
    return this.post('/api/strategy/start', {
      account_id: accountId,
      strategy_name: strategyName,
      parameters,
    });
  }

  // 停止策略
  async stopStrategy(accountId: string, instanceId: string): Promise<{ success: boolean; message: string }> {
    return this.post('/api/strategy/stop', {
      account_id: accountId,
      instance_id: instanceId,
    });
  }

  // 获取日志
  async getRecentLogs(limit: number = 100, level?: string): Promise<{ logs: LogEntry[]; count: number }> {
    const params = new URLSearchParams();
    params.append('limit', limit.toString());
    if (level) params.append('level', level);
    return this.get(`/api/logs/recent?${params}`);
  }

  // 系统健康检查
  async getHealthStatus(): Promise<SystemStatus> {
    return this.get('/health');
  }

  // WebSocket连接
  connectWebSocket(onMessage: (data: any) => void, onError?: (error: Event) => void): void {
    if (this.ws) {
      this.ws.close();
    }

    this.ws = new WebSocket('ws://localhost:8000/ws');
    
    this.ws.onopen = () => {
      console.log('WebSocket连接已建立');
    };

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onMessage(data);
      } catch (error) {
        console.error('WebSocket消息解析错误:', error);
      }
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket错误:', error);
      if (onError) onError(error);
    };

    this.ws.onclose = () => {
      console.log('WebSocket连接已关闭');
      // 尝试重连
      setTimeout(() => {
        if (!this.ws || this.ws.readyState === WebSocket.CLOSED) {
          this.connectWebSocket(onMessage, onError);
        }
      }, 3000);
    };
  }

  // 断开WebSocket
  disconnectWebSocket(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  // 执行控制台命令 (模拟)
  async executeCommand(command: string): Promise<{ output: string[] }> {
    // 这里应该调用真实的API端点，现在先返回模拟数据
    return new Promise((resolve) => {
      setTimeout(() => {
        const output = [`> ${command}`, `命令 "${command}" 执行结果: 模拟输出`];
        resolve({ output });
      }, 500);
    });
  }
}

export const apiClient = new ApiClient();