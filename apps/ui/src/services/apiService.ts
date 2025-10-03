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
            // 检查是否是嵌套的错误对象
            if (typeof errorData.detail === 'object' && errorData.detail.message) {
              errorMessage = errorData.detail.message;
              // 如果有解决方案，也包含在错误信息中
              if (errorData.detail.solution) {
                errorMessage += `\n建议: ${errorData.detail.solution}`;
              }
            } else if (typeof errorData.detail === 'string') {
              errorMessage = errorData.detail;
            }
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
        error: error instanceof Error ? error.message : '获取运行实例失败'
      };
    }
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

  // 删除策略实例
  async deleteInstance(accountId: string, instanceId: string): Promise<ApiResponse> {
    return this.makeRequest('/api/instances/delete', {
      method: 'POST',
      body: {
        account_id: accountId,
        instance_id: instanceId
      }
    });
  }

  // 启动策略
  async startStrategy(accountId: string, instanceId: string): Promise<ApiResponse> {
    return this.makeRequest('/api/strategy/start', {
      method: 'POST',
      body: {
        account_id: accountId,
        instance_id: instanceId
      }
    });
  }

  // 配置文件管理
  async listConfigProfiles(): Promise<ApiResponse> {
    return this.makeRequest('/api/config/profiles');
  }

  async getConfigProfile(platform: string, account: string, strategy: string): Promise<ApiResponse> {
    return this.makeRequest(`/api/config/profiles/${platform}/${account}/${strategy}`);
  }

  async saveConfigProfile(platform: string, account: string, strategy: string, config: any): Promise<ApiResponse> {
    return this.makeRequest(`/api/config/profiles/${platform}/${account}/${strategy}`, {
      method: 'POST',
      body: config
    });
  }

  async deleteConfigProfile(platform: string, account: string, strategy: string): Promise<ApiResponse> {
    return this.makeRequest(`/api/config/profiles/${platform}/${account}/${strategy}`, {
      method: 'DELETE'
    });
  }

  // 日志管理
  async getRecentLogs(limit: number = 100, level?: string): Promise<ApiResponse> {
    const params = new URLSearchParams();
    params.append('limit', limit.toString());
    if (level) {
      params.append('level', level);
    }
    return this.makeRequest(`/api/logs/recent?${params.toString()}`);
  }

  async getLogFile(filePath: string): Promise<ApiResponse> {
    return this.makeRequest(`/api/logs/file?path=${encodeURIComponent(filePath)}`);
  }

  // 停止策略
  async stopStrategy(accountId: string, instanceId: string): Promise<ApiResponse> {
    return this.makeRequest('/api/strategy/stop', {
      method: 'POST',
      body: {
        account_id: accountId,
        instance_id: instanceId
      }
    });
  }
}

// 单例模式
export const apiService = new ApiService();
export default apiService;