// apps/ui/src/contexts/ApiContext.tsx
// API数据上下文，提供全局数据管理

import React, { createContext, useContext, useState, useEffect } from 'react';
import { apiClient } from '../services/apiClient';

const ApiContext = createContext(null);

export function ApiProvider({ children }: { children: React.ReactNode }) {
  const [data, setData] = useState({
    dashboardSummary: null,
    runningInstances: [],
    availablePlatforms: [],
    availableStrategies: [],
    recentLogs: [],
    isLoading: false,
    error: null,
    isConnected: false,
  });

  const [missingFeatures, setMissingFeatures] = useState([]);

  const recordMissingFeature = (component, feature, description) => {
    const newFeature = {
      component,
      feature,
      description,
      timestamp: new Date().toISOString(),
    };
    setMissingFeatures(prev => [...prev, newFeature]);
    console.warn(`缺失功能记录: ${component}.${feature} - ${description}`);
  };

  const updateData = (updates) => {
    setData(prev => ({ ...prev, ...updates }));
  };

  const fetchDashboardSummary = async () => {
    try {
      updateData({ isLoading: true });
      const summary = await apiClient.getDashboardSummary();
      updateData({ dashboardSummary: summary, error: null });
    } catch (error) {
      console.error('获取仪表板摘要失败:', error);
      recordMissingFeature('Dashboard', 'summary', '仪表板摘要数据获取失败');
      updateData({ error: '获取仪表板摘要失败' });
    } finally {
      updateData({ isLoading: false });
    }
  };

  const fetchRunningInstances = async () => {
    try {
      const result = await apiClient.getRunningInstances();
      updateData({ runningInstances: result.instances });
    } catch (error) {
      console.error('获取运行实例失败:', error);
      recordMissingFeature('CurrentRunning', 'instances', '运行实例数据获取失败');
      updateData({ error: '获取运行实例失败' });
    }
  };

  const fetchAvailablePlatforms = async () => {
    try {
      const result = await apiClient.getAvailablePlatforms();
      updateData({ availablePlatforms: result.platforms });
    } catch (error) {
      console.error('获取可用平台失败:', error);
      recordMissingFeature('PlatformConfig', 'platforms', '可用平台数据获取失败');
      updateData({ error: '获取可用平台失败' });
    }
  };

  const fetchAvailableStrategies = async () => {
    try {
      const result = await apiClient.getAvailableStrategies();
      updateData({ availableStrategies: result.strategies });
    } catch (error) {
      console.error('获取可用策略失败:', error);
      recordMissingFeature('StrategyPanel', 'strategies', '可用策略数据获取失败');
      updateData({ error: '获取可用策略失败' });
    }
  };

  const fetchRecentLogs = async (limit = 100, level) => {
    try {
      const result = await apiClient.getRecentLogs(limit, level);
      updateData({ recentLogs: result.logs });
    } catch (error) {
      console.error('获取日志失败:', error);
      recordMissingFeature('LogsPanel', 'logs', '日志数据获取失败');
      updateData({ error: '获取日志失败' });
    }
  };

  const startStrategy = async (accountId, strategyName, parameters) => {
    try {
      const result = await apiClient.startStrategy(accountId, strategyName, parameters);
      if (result.success) {
        await fetchRunningInstances();
        await fetchDashboardSummary();
        return result;
      } else {
        throw new Error(result.message);
      }
    } catch (error) {
      console.error('启动策略失败:', error);
      recordMissingFeature('CurrentRunning', 'startStrategy', '策略启动功能失败');
      throw error;
    }
  };

  const stopStrategy = async (accountId, instanceId) => {
    try {
      const result = await apiClient.stopStrategy(accountId, instanceId);
      if (result.success) {
        await fetchRunningInstances();
        await fetchDashboardSummary();
        return result;
      } else {
        throw new Error(result.message);
      }
    } catch (error) {
      console.error('停止策略失败:', error);
      recordMissingFeature('CurrentRunning', 'stopStrategy', '策略停止功能失败');
      throw error;
    }
  };

  const executeCommand = async (command) => {
    try {
      const result = await apiClient.executeCommand(command);
      return result.output;
    } catch (error) {
      console.error('执行命令失败:', error);
      recordMissingFeature('ConsoleTools', 'executeCommand', '控制台命令执行失败');
      return [`错误: 命令执行失败 - ${error}`];
    }
  };

  const initializeData = async () => {
    updateData({ isLoading: true });
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
      updateData({ isLoading: false });
    }
  };

  // WebSocket连接
  useEffect(() => {
    const handleWebSocketMessage = (wsData) => {
      console.log('收到WebSocket消息:', wsData);
      
      switch (wsData.type) {
        case 'strategy_started':
        case 'strategy_stopped':
          fetchRunningInstances();
          fetchDashboardSummary();
          break;
        case 'status_update':
          updateData({ isConnected: true });
          break;
        default:
          console.log('未处理的WebSocket消息类型:', wsData.type);
      }
    };

    apiClient.connectWebSocket(
      handleWebSocketMessage,
      (error) => {
        updateData({ isConnected: false });
        console.error('WebSocket连接错误:', error);
      }
    );

    return () => {
      apiClient.disconnectWebSocket();
    };
  }, []);

  // 初始化数据和定期刷新
  useEffect(() => {
    initializeData();

    const interval = setInterval(() => {
      fetchDashboardSummary();
      fetchRunningInstances();
    }, 30000); // 每30秒刷新一次

    return () => clearInterval(interval);
  }, []);

  const value = {
    ...data,
    missingFeatures,
    fetchDashboardSummary,
    fetchRunningInstances,
    fetchAvailablePlatforms,
    fetchAvailableStrategies,
    fetchRecentLogs,
    startStrategy,
    stopStrategy,
    executeCommand,
    initializeData,
    recordMissingFeature,
  };

  return <ApiContext.Provider value={value}>{children}</ApiContext.Provider>;
}

export function useApiData() {
  const context = useContext(ApiContext);
  if (!context) {
    throw new Error('useApiData must be used within an ApiProvider');
  }
  return context;
}