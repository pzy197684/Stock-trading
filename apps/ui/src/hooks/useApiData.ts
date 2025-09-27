// apps/ui/src/hooks/useApiData.ts
// 数据管理Hook，统一管理API数据状态

import { useState, useEffect, useCallback } from 'react';
import { apiClient, DashboardSummary, StrategyInstance, Platform, Strategy, LogEntry } from '../services/apiClient';

interface ApiDataState {
  // 数据状态
  dashboardSummary: DashboardSummary | null;
  runningInstances: StrategyInstance[];
  availablePlatforms: Platform[];
  availableStrategies: Strategy[];
  recentLogs: LogEntry[];
  
  // 加载状态
  isLoading: boolean;
  error: string | null;
  
  // WebSocket连接状态
  isConnected: boolean;
}

interface MissingFeature {
  component: string;
  feature: string;
  description: string;
  timestamp: string;
}

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
  const setLoading = useCallback((isLoading: boolean) => {
    setState(prev => ({ ...prev, isLoading, error: isLoading ? null : prev.error }));
  }, []);

  // 更新部分状态
  const updateState = useCallback((updates: Partial<ApiDataState>) => {
    setState(prev => ({ ...prev, ...updates }));
  }, []);

  // 获取仪表板摘要
  const fetchDashboardSummary = useCallback(async () => {
    try {
      setLoading(true);
      const summary = await apiClient.getDashboardSummary();
      updateState({ dashboardSummary: summary });
    } catch (error) {
      console.error('获取仪表板摘要失败:', error);
      recordMissingFeature('Dashboard', 'summary', '仪表板摘要数据获取失败');
      setError('获取仪表板摘要失败');
    } finally {
      setLoading(false);
    }
  }, [setLoading, updateState, recordMissingFeature, setError]);

  // 获取运行实例
  const fetchRunningInstances = useCallback(async () => {
    try {
      const { instances } = await apiClient.getRunningInstances();
      updateState({ runningInstances: instances });
    } catch (error) {
      console.error('获取运行实例失败:', error);
      recordMissingFeature('CurrentRunning', 'instances', '运行实例数据获取失败');
      setError('获取运行实例失败');
    }
  }, [updateState, recordMissingFeature, setError]);

  // 获取可用平台
  const fetchAvailablePlatforms = useCallback(async () => {
    try {
      const { platforms } = await apiClient.getAvailablePlatforms();
      updateState({ availablePlatforms: platforms });
    } catch (error) {
      console.error('获取可用平台失败:', error);
      recordMissingFeature('PlatformConfig', 'platforms', '可用平台数据获取失败');
      setError('获取可用平台失败');
    }
  }, [updateState, recordMissingFeature, setError]);

  // 获取可用策略
  const fetchAvailableStrategies = useCallback(async () => {
    try {
      const { strategies } = await apiClient.getAvailableStrategies();
      updateState({ availableStrategies: strategies });
    } catch (error) {
      console.error('获取可用策略失败:', error);
      recordMissingFeature('StrategyPanel', 'strategies', '可用策略数据获取失败');
      setError('获取可用策略失败');
    }
  }, [updateState, recordMissingFeature, setError]);

  // 获取最新日志
  const fetchRecentLogs = useCallback(async (limit: number = 100, level?: string) => {
    try {
      const { logs } = await apiClient.getRecentLogs(limit, level);
      updateState({ recentLogs: logs });
    } catch (error) {
      console.error('获取日志失败:', error);
      recordMissingFeature('LogsPanel', 'logs', '日志数据获取失败');
      setError('获取日志失败');
    }
  }, [updateState, recordMissingFeature, setError]);

  // 启动策略
  const startStrategy = useCallback(async (accountId: string, strategyName: string, parameters?: Record<string, any>) => {
    try {
      const result = await apiClient.startStrategy(accountId, strategyName, parameters);
      if (result.success) {
        // 刷新运行实例
        await fetchRunningInstances();
        return result;
      } else {
        throw new Error(result.message);
      }
    } catch (error) {
      console.error('启动策略失败:', error);
      recordMissingFeature('CurrentRunning', 'startStrategy', '策略启动功能失败');
      throw error;
    }
  }, [fetchRunningInstances, recordMissingFeature]);

  // 停止策略
  const stopStrategy = useCallback(async (accountId: string, instanceId: string) => {
    try {
      const result = await apiClient.stopStrategy(accountId, instanceId);
      if (result.success) {
        // 刷新运行实例
        await fetchRunningInstances();
        return result;
      } else {
        throw new Error(result.message);
      }
    } catch (error) {
      console.error('停止策略失败:', error);
      recordMissingFeature('CurrentRunning', 'stopStrategy', '策略停止功能失败');
      throw error;
    }
  }, [fetchRunningInstances, recordMissingFeature]);

  // 执行控制台命令
  const executeCommand = useCallback(async (command: string): Promise<string[]> => {
    try {
      const { output } = await apiClient.executeCommand(command);
      return output;
    } catch (error) {
      console.error('执行命令失败:', error);
      recordMissingFeature('ConsoleTools', 'executeCommand', '控制台命令执行失败');
      return [`错误: 命令执行失败 - ${error}`];
    }
  }, [recordMissingFeature]);

  // 初始化数据加载
  const initializeData = useCallback(async () => {
    setLoading(true);
    try {
      await Promise.all([
        fetchDashboardSummary(),
        fetchRunningInstances(),
        fetchAvailablePlatforms(),
        fetchAvailableStrategies(),
        fetchRecentLogs(),
      ]);
    } catch (error) {
      console.error('初始化数据失败:', error);
    } finally {
      setLoading(false);
    }
  }, [fetchDashboardSummary, fetchRunningInstances, fetchAvailablePlatforms, fetchAvailableStrategies, fetchRecentLogs, setLoading]);

  // WebSocket消息处理
  const handleWebSocketMessage = useCallback((data: any) => {
    console.log('收到WebSocket消息:', data);
    
    switch (data.type) {
      case 'strategy_started':
      case 'strategy_stopped':
        fetchRunningInstances();
        fetchDashboardSummary();
        break;
      case 'status_update':
        updateState({ isConnected: true });
        break;
      default:
        console.log('未处理的WebSocket消息类型:', data.type);
    }
  }, [fetchRunningInstances, fetchDashboardSummary, updateState]);

  // 建立WebSocket连接
  useEffect(() => {
    apiClient.connectWebSocket(
      handleWebSocketMessage,
      (error) => {
        updateState({ isConnected: false });
        console.error('WebSocket连接错误:', error);
      }
    );

    return () => {
      apiClient.disconnectWebSocket();
    };
  }, [handleWebSocketMessage, updateState]);

  // 定期刷新数据
  useEffect(() => {
    initializeData();

    const interval = setInterval(() => {
      fetchDashboardSummary();
      fetchRunningInstances();
    }, 30000); // 每30秒刷新一次

    return () => clearInterval(interval);
  }, [initializeData, fetchDashboardSummary, fetchRunningInstances]);

  return {
    // 数据状态
    ...state,
    missingFeatures,
    
    // 操作方法
    fetchDashboardSummary,
    fetchRunningInstances,
    fetchAvailablePlatforms,
    fetchAvailableStrategies,
    fetchRecentLogs,
    startStrategy,
    stopStrategy,
    executeCommand,
    initializeData,
    
    // 工具方法
    recordMissingFeature,
  };
}