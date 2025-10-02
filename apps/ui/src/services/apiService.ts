// 统一的API服务层，消除重复的fetch调用
import { DEFAULT_CONFIG } from '../config/defaults';

interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

interface RequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE';
  body?: any;
  headers?: Record<string, string>;
  timeout?: number;
}

class ApiService {
  private baseUrl: string;
  private defaultTimeout: number;

  constructor() {
    this.baseUrl = DEFAULT_CONFIG.api.base_url;
    this.defaultTimeout = DEFAULT_CONFIG.api.timeout;
  }

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
      const response = await fetch(url, {
        method,
        headers: requestHeaders,
        body: body ? JSON.stringify(body) : undefined,
        signal: controller.signal
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        return {
          success: false,
          error: `HTTP ${response.status}: ${response.statusText}`
        };
      }

      const data = await response.json();
      return {
        success: true,
        data
      };

    } catch (error) {
      clearTimeout(timeoutId);
      
      if (error instanceof Error) {
        return {
          success: false,
          error: error.message
        };
      }
      
      return {
        success: false,
        error: 'Unknown error occurred'
      };
    }
  }

  // 实例管理
  async getRunningInstances(): Promise<ApiResponse> {
    return this.makeRequest('/api/running/instances');
  }

  async createInstance(instanceData: any): Promise<ApiResponse> {
    return this.makeRequest('/api/instances/create', {
      method: 'POST',
      body: instanceData
    });
  }

  async updateInstanceParameters(instanceId: string, parameters: any): Promise<ApiResponse> {
    return this.makeRequest(`/api/running/instances/${instanceId}/parameters`, {
      method: 'POST',
      body: parameters
    });
  }

  async updateProfileConfig(platform: string, account: string, strategy: string, parameters: any): Promise<ApiResponse> {
    return this.makeRequest(`/api/config/profiles/${platform}/${account}/${strategy}`, {
      method: 'POST',
      body: parameters
    });
  }

  async getInstanceParameters(instanceId: string): Promise<ApiResponse> {
    return this.makeRequest(`/api/running/instances/${instanceId}/parameters`);
  }

  async stopInstance(accountId: string, instanceId: string): Promise<ApiResponse> {
    return this.makeRequest(`/api/strategy/stop?account_id=${encodeURIComponent(accountId)}&instance_id=${encodeURIComponent(instanceId)}`, {
      method: 'POST'
    });
  }

  async forceStopInstance(accountId: string, instanceId: string): Promise<ApiResponse> {
    return this.makeRequest(`/api/strategy/force-stop-and-close?account_id=${encodeURIComponent(accountId)}&instance_id=${encodeURIComponent(instanceId)}`, {
      method: 'POST'
    });
  }

  // 配置管理
  async updateConfig(configData: any): Promise<ApiResponse> {
    return this.makeRequest('/api/config/update', {
      method: 'POST',
      body: configData
    });
  }

  // 平台和策略信息
  async getAvailablePlatforms(): Promise<ApiResponse> {
    return this.makeRequest('/api/platforms/available');
  }

  async getAvailableStrategies(): Promise<ApiResponse> {
    return this.makeRequest('/api/strategies/available');
  }

  async getAvailableAccounts(platform?: string): Promise<ApiResponse> {
    const endpoint = platform 
      ? `/api/accounts/available?platform=${platform}`
      : '/api/accounts/available';
    return this.makeRequest(endpoint);
  }

  async getAvailableSymbols(platform: string): Promise<ApiResponse> {
    return this.makeRequest(`/api/symbols/available?platform=${platform}`);
  }

  // 策略模板
  async getStrategyTemplates(strategy: string = 'martingale_hedge'): Promise<ApiResponse> {
    return this.makeRequest(`/api/strategies/${strategy}/templates`);
  }

  // 账户测试
  async testConnection(connectionData: any): Promise<ApiResponse> {
    return this.makeRequest('/api/accounts/test-connection', {
      method: 'POST',
      body: connectionData
    });
  }

  // 系统信息
  async getSystemHealth(): Promise<ApiResponse> {
    return this.makeRequest('/health');
  }

  async getDashboardSummary(): Promise<ApiResponse> {
    return this.makeRequest('/api/dashboard/summary');
  }

  // 日志测试
  async testLogs(): Promise<ApiResponse> {
    return this.makeRequest('/api/logs/test', {
      method: 'POST'
    });
  }
}

// 单例模式
export const apiService = new ApiService();
export default apiService;