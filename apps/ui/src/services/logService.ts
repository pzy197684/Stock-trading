// 前端日志服务 - 支持中文显示和实时日志推送

export interface LogEntry {
  timestamp: string;
  level: 'debug' | 'info' | 'warning' | 'error' | 'critical' | 'trade';
  message: string;
  source?: string;
  category?: string;
  data?: any;
}

export interface LogFilter {
  level?: string[];
  source?: string[];
  category?: string[];
  timeRange?: {
    start: Date;
    end: Date;
  };
  keyword?: string;
}

class LogService {
  private logs: LogEntry[] = [];
  private maxLogs = 1000; // 最大日志条数
  private listeners: ((logs: LogEntry[]) => void)[] = [];
  private wsConnection: WebSocket | null = null;

  constructor() {
    this.initWebSocketConnection();
  }

  private initWebSocketConnection() {
    try {
      this.wsConnection = new WebSocket('ws://localhost:8001/ws/logs');
      
      this.wsConnection.onmessage = (event) => {
        try {
          const logData = JSON.parse(event.data);
          if (logData.type === 'log') {
            this.addLog(logData.data);
          }
        } catch (error) {
          console.error('解析日志WebSocket消息失败:', error);
        }
      };

      this.wsConnection.onclose = () => {
        console.log('日志WebSocket连接已关闭，5秒后重连...');
        setTimeout(() => this.initWebSocketConnection(), 5000);
      };

      this.wsConnection.onerror = (error) => {
        console.error('日志WebSocket连接错误:', error);
      };
    } catch (error) {
      console.error('初始化日志WebSocket连接失败:', error);
    }
  }

  addLog(entry: LogEntry) {
    // 过滤掉空消息或无意义的日志
    if (!entry.message || entry.message.trim() === '' || entry.message === '-') {
      console.debug('跳过空日志消息:', entry);
      return;
    }
    
    // 过滤掉过于频繁的debug信息
    if (entry.level === 'debug' && (
      entry.message.includes('API调用开始') ||
      entry.message.includes('API调用成功') ||
      entry.message.includes('WebSocket连接状态')
    )) {
      return;
    }

    const newEntry = {
      ...entry,
      timestamp: entry.timestamp || new Date().toISOString(),
      message: entry.message.trim(),
      source: entry.source || 'System',
      level: entry.level || 'info'
    };

    this.logs.unshift(newEntry);
    
    // 限制日志数量
    if (this.logs.length > this.maxLogs) {
      this.logs = this.logs.slice(0, this.maxLogs);
    }

    // 通知监听器
    this.notifyListeners();
  }

  // 前端日志记录方法
  debug(message: string, source?: string, data?: any) {
    this.addLog({
      timestamp: new Date().toISOString(),
      level: 'debug',
      message: `🔍 ${message}`,
      source: source || 'Frontend',
      data
    });
  }

  info(message: string, source?: string, data?: any) {
    this.addLog({
      timestamp: new Date().toISOString(),
      level: 'info',
      message: `ℹ️ ${message}`,
      source: source || 'Frontend',
      data
    });
  }

  warning(message: string, source?: string, data?: any) {
    this.addLog({
      timestamp: new Date().toISOString(),
      level: 'warning',
      message: `⚠️ ${message}`,
      source: source || 'Frontend',
      data
    });
  }

  error(message: string, source?: string, error?: Error, data?: any) {
    let errorMsg = `❌ ${message}`;
    if (error) {
      errorMsg += ` | 错误详情: ${error.message}`;
      if (error.stack) {
        errorMsg += ` | 堆栈: ${error.stack.split('\n')[1]?.trim() || '未知'}`;
      }
    }

    this.addLog({
      timestamp: new Date().toISOString(),
      level: 'error',
      message: errorMsg,
      source: source || 'Frontend',
      data: { ...data, error: error?.stack }
    });
  }

  trade(message: string, data?: any) {
    this.addLog({
      timestamp: new Date().toISOString(),
      level: 'trade',
      message: `💰 ${message}`,
      source: 'Trading',
      category: 'trade',
      data
    });
  }

  // 获取过滤后的日志
  getLogs(filter?: LogFilter): LogEntry[] {
    let filteredLogs = [...this.logs];

    if (filter) {
      if (filter.level && filter.level.length > 0) {
        filteredLogs = filteredLogs.filter(log => filter.level!.includes(log.level));
      }

      if (filter.source && filter.source.length > 0) {
        filteredLogs = filteredLogs.filter(log => 
          filter.source!.some(source => log.source?.includes(source))
        );
      }

      if (filter.category && filter.category.length > 0) {
        filteredLogs = filteredLogs.filter(log => 
          filter.category!.includes(log.category || '')
        );
      }

      if (filter.keyword) {
        const keyword = filter.keyword.toLowerCase();
        filteredLogs = filteredLogs.filter(log => 
          log.message.toLowerCase().includes(keyword)
        );
      }

      if (filter.timeRange) {
        filteredLogs = filteredLogs.filter(log => {
          try {
            const logTime = new Date(log.timestamp);
            // 验证日期有效性
            if (isNaN(logTime.getTime())) {
              console.warn('跳过无效时间戳的日志:', log.timestamp);
              return false;
            }
            return logTime >= filter.timeRange!.start && logTime <= filter.timeRange!.end;
          } catch (error) {
            console.error('时间范围过滤错误:', error, log.timestamp);
            return false;
          }
        });
      }
    }

    return filteredLogs;
  }

  // 添加监听器
  addListener(callback: (logs: LogEntry[]) => void) {
    this.listeners.push(callback);
    return () => {
      const index = this.listeners.indexOf(callback);
      if (index > -1) {
        this.listeners.splice(index, 1);
      }
    };
  }

  private notifyListeners() {
    this.listeners.forEach(callback => callback([...this.logs]));
  }

  // 清空日志
  clearLogs() {
    this.logs = [];
    this.notifyListeners();
  }

  // 导出日志
  exportLogs(filter?: LogFilter): string {
    const logsToExport = this.getLogs(filter);
    const lines = logsToExport.map(log => {
      try {
        let timestamp = '无效时间';
        if (log.timestamp) {
          const date = new Date(log.timestamp);
          if (!isNaN(date.getTime())) {
            timestamp = date.toLocaleString('zh-CN');
          }
        }
        return `[${timestamp}] [${log.level.toUpperCase()}] ${log.source ? `[${log.source}] ` : ''}${log.message}`;
      } catch (error) {
        console.error('导出日志时间戳处理错误:', error);
        return `[时间错误] [${log.level.toUpperCase()}] ${log.source ? `[${log.source}] ` : ''}${log.message}`;
      }
    });
    return lines.join('\n');
  }

  // 获取日志统计
  getLogStats(filter?: LogFilter): Record<string, number> {
    const logs = this.getLogs(filter);
    const stats: Record<string, number> = {
      total: logs.length,
      debug: 0,
      info: 0,
      warning: 0,
      error: 0,
      critical: 0,
      trade: 0
    };

    logs.forEach(log => {
      stats[log.level] = (stats[log.level] || 0) + 1;
    });

    return stats;
  }
}

// 创建全局日志服务实例
export const logService = new LogService();

// 重写console方法，自动记录到日志服务
const originalConsole = {
  log: console.log,
  info: console.info,
  warn: console.warn,
  error: console.error,
  debug: console.debug
};

console.log = (...args) => {
  originalConsole.log(...args);
  logService.debug(args.join(' '), 'Console');
};

console.info = (...args) => {
  originalConsole.info(...args);
  logService.info(args.join(' '), 'Console');
};

console.warn = (...args) => {
  originalConsole.warn(...args);
  logService.warning(args.join(' '), 'Console');
};

console.error = (...args) => {
  originalConsole.error(...args);
  logService.error(args.join(' '), 'Console');
};

console.debug = (...args) => {
  originalConsole.debug(...args);
  logService.debug(args.join(' '), 'Console');
};

export default logService;