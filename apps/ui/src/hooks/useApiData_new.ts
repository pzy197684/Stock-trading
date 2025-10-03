// apps/ui/src/hooks/useApiData.ts
// 数据管理Hook，统一管理API数据状态 - 更新版本

import { useState, useEffect, useCallback } from 'react';
import type { 
  ApiDataState, 
  UseApiDataReturn, 
  TradingInstance, 
  CreateInstanceRequest,
  ApiResponse,
  DashboardSummary,
  PlatformInfo,
  StrategyInfo,
  LogEntry
} from '../types/api';
import apiService from '../services/apiService';

interface MissingFeature {
  component: string;
  feature: string;
  description: string;
  timestamp: string;
}

export function useApiData(): UseApiDataReturn {
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

  const [missingFeatures, setMissingFeatures] = useState<MissingFeature[]>([]);

  // 记录缺失功能
  const recordMissingFeature = useCallback((component: string, feature: string, description: string) => {
    const newFeature: MissingFeature = {
      component,
      feature,
      description,
      timestamp: new Date().toISOString(),
    };
    setMissingFeatures(prev => [...prev, newFeature]);
    console.warn(`缺失功能记录: ${component}.${feature} - ${description}`);
  }, []);

  // 设置错误状态
  const setError = useCallback((error: string) => {
    setState(prev => ({ ...prev, error, isLoading: false }));
  }, []);

  // 设置加载状态
  const setLoading = useCallback((loading: boolean) => {
    setState(prev => ({ ...prev, isLoading: loading }));
  }, []);

  // 更新状态
  const updateState = useCallback((updates: Partial<ApiDataState>) => {
    setState(prev => ({ ...prev, ...updates }));
  }, []);

  // 获取仪表板摘要
  const fetchDashboardSummary = useCallback(async () => {
    try {
      setLoading(true);
      const response = await apiService.getDashboardSummary();
      if (response.success && response.data) {
        updateState({ dashboardSummary: response.data.summary, error: null });
      } else {
        throw new Error(response.error || '获取仪表板摘要失败');
      }
    } catch (error) {
      console.error('获取仪表板摘要失败:', error);
      recordMissingFeature('Dashboard', 'summary', '仪表板摘要数据获取失败');
      setError(error instanceof Error ? error.message : '获取仪表板摘要失败');
    } finally {
      setLoading(false);
    }
  }, [updateState, recordMissingFeature, setError, setLoading]);

  // 获取运行实例 - 优化版本
  const fetchRunningInstances = useCallback(async () => {
    try {
      setLoading(true);
      const response = await apiService.getRunningInstances();
      
      if (response.success && response.data) {
        // 确保数据结构正确
        const instances = response.data.instances || [];
        
        // 数据验证和清理
        const validatedInstances: TradingInstance[] = instances.map((instance: any) => ({
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
        
        console.debug(`成功获取 ${validatedInstances.length} 个实例`);
        
      } else {
        throw new Error(response.error || '获取实例列表失败');
      }
      
    } catch (error) {
      console.error('获取运行实例失败:', error);
      recordMissingFeature('CurrentRunning', 'instances', '运行实例数据获取失败');
      setError(error instanceof Error ? error.message : '获取运行实例失败');
      
      // 设置空数据而不是保持旧数据
      updateState({ runningInstances: [] });
      
    } finally {
      setLoading(false);
    }
  }, [updateState, recordMissingFeature, setError, setLoading]);

  // 获取可用平台
  const fetchAvailablePlatforms = useCallback(async () => {
    try {
      const response = await apiService.getAvailablePlatforms();
      if (response.success && response.data) {
        updateState({ availablePlatforms: response.data.platforms || [], error: null });
      } else {
        throw new Error(response.error || '获取平台列表失败');
      }
    } catch (error) {
      console.error('获取可用平台失败:', error);
      recordMissingFeature('PlatformConfig', 'platforms', '可用平台数据获取失败');
      setError(error instanceof Error ? error.message : '获取可用平台失败');
    }
  }, [updateState, recordMissingFeature, setError]);

  // 获取可用策略
  const fetchAvailableStrategies = useCallback(async () => {
    try {
      const response = await apiService.getAvailableStrategies();
      if (response.success && response.data) {
        updateState({ availableStrategies: response.data.strategies || [], error: null });
      } else {
        throw new Error(response.error || '获取策略列表失败');
      }
    } catch (error) {
      console.error('获取可用策略失败:', error);
      recordMissingFeature('StrategyPanel', 'strategies', '可用策略数据获取失败');
      setError(error instanceof Error ? error.message : '获取可用策略失败');
    }
  }, [updateState, recordMissingFeature, setError]);

  // 获取最新日志
  const fetchRecentLogs = useCallback(async (limit: number = 100, level?: string) => {
    try {
      const response = await apiService.getRecentLogs(limit, level);
      if (response.success && response.data) {
        updateState({ recentLogs: response.data.logs || [], error: null });
      } else {
        throw new Error(response.error || '获取日志失败');
      }
    } catch (error) {
      console.error('获取日志失败:', error);
      recordMissingFeature('LogsPanel', 'logs', '日志数据获取失败');
      setError(error instanceof Error ? error.message : '获取日志失败');
    }
  }, [updateState, recordMissingFeature, setError]);

  // 启动策略
  const startStrategy = useCallback(async (accountId: string, instanceId: string): Promise<ApiResponse> => {
    try {
      const result = await apiService.startStrategy(accountId, instanceId);
      if (result.success) {
        // 刷新实例列表
        await fetchRunningInstances();
        await fetchDashboardSummary();
      }
      return result;
    } catch (error) {
      console.error('启动策略失败:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : '启动策略失败'
      };
    }
  }, [fetchRunningInstances, fetchDashboardSummary]);

  // 停止策略
  const stopStrategy = useCallback(async (accountId: string, instanceId: string): Promise<ApiResponse> => {
    try {
      const result = await apiService.stopStrategy(accountId, instanceId);
      if (result.success) {
        // 刷新实例列表
        await fetchRunningInstances();
        await fetchDashboardSummary();
      }
      return result;
    } catch (error) {
      console.error('停止策略失败:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : '停止策略失败'
      };
    }
  }, [fetchRunningInstances, fetchDashboardSummary]);

  // 创建实例
  const createInstance = useCallback(async (request: CreateInstanceRequest): Promise<ApiResponse> => {
    try {
      const result = await apiService.createInstance(request);
      if (result.success) {
        // 刷新实例列表
        await fetchRunningInstances();
        await fetchDashboardSummary();
      }
      return result;
    } catch (error) {
      console.error('创建实例失败:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : '创建实例失败'
      };
    }
  }, [fetchRunningInstances, fetchDashboardSummary]);

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
          
          // 更新日志列表
          setState(prev => ({
            ...prev,
            recentLogs: [logEntry, ...prev.recentLogs.slice(0, 99)] // 保持最新100条
          }));
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
    fetchDashboardSummary,
    fetchAvailablePlatforms,
    fetchAvailableStrategies,
    fetchRecentLogs,
    startStrategy,
    stopStrategy,
    createInstance,
    recordMissingFeature,
  };
}