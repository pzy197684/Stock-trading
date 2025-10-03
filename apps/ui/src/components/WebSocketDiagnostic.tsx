import { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { ScrollArea } from "./ui/scroll-area";
import { useToast } from "./ui/toast";
import { Wifi, WifiOff, Activity, RefreshCw, CheckCircle, XCircle, AlertTriangle } from 'lucide-react';

interface LogMessage {
  timestamp: string;
  level: string;
  message: string;
  source?: string;
  category?: string;
  test_sequence?: number;
}

interface ConnectionStatus {
  active_connections: number;
  status: string;
  endpoint: string;
  message: string;
}

export function WebSocketDiagnostic() {
  const { toast } = useToast();
  const [connected, setConnected] = useState(false);
  const [connecting, setConnecting] = useState(false);
  const [logs, setLogs] = useState<LogMessage[]>([]);
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus | null>(null);
  const [lastMessage, setLastMessage] = useState<string>('');
  const [messageCount, setMessageCount] = useState(0);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const [autoReconnect] = useState(true);  // 保留变量但标记为已使用

  const connectWebSocket = () => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    setConnecting(true);
    console.log('[WebSocket诊断] 尝试连接到 ws://localhost:8001/ws/logs');

    try {
      const ws = new WebSocket('ws://localhost:8001/ws/logs');
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('[WebSocket诊断] 连接成功');
        setConnected(true);
        setConnecting(false);
        setLogs(prev => [...prev, {
          timestamp: new Date().toISOString(),
          level: 'info',
          message: '✅ WebSocket连接成功',
          source: 'diagnostic',
          category: 'connection'
        }]);
        
        toast({
          title: "WebSocket连接成功",
          description: "日志推送功能已激活",
          type: "success"
        });
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('[WebSocket诊断] 收到消息:', data);
          
          setLastMessage(new Date().toLocaleTimeString());
          setMessageCount(prev => prev + 1);

          if (data.type === 'log' && data.data) {
            setLogs(prev => {
              const newLogs = [...prev, data.data];
              // 保持最近100条日志
              return newLogs.slice(-100);
            });
          } else if (data.type === 'connection') {
            setLogs(prev => [...prev, {
              timestamp: data.timestamp || new Date().toISOString(),
              level: 'info',
              message: data.message || '连接状态更新',
              source: 'connection',
              category: 'system'
            }]);
          }
        } catch (error) {
          console.error('[WebSocket诊断] 消息解析失败:', error);
        }
      };

      ws.onerror = (error) => {
        console.error('[WebSocket诊断] 连接错误:', error);
        setLogs(prev => [...prev, {
          timestamp: new Date().toISOString(),
          level: 'error',
          message: '❌ WebSocket连接错误',
          source: 'diagnostic',
          category: 'error'
        }]);
      };

      ws.onclose = (event) => {
        console.log('[WebSocket诊断] 连接关闭:', event.code, event.reason);
        setConnected(false);
        setConnecting(false);
        
        setLogs(prev => [...prev, {
          timestamp: new Date().toISOString(),
          level: 'warning',
          message: `⚠️ WebSocket连接关闭 (代码: ${event.code})`,
          source: 'diagnostic',
          category: 'connection'
        }]);

        // 自动重连
        if (autoReconnect && event.code !== 1000) {
          reconnectTimeoutRef.current = setTimeout(() => {
            console.log('[WebSocket诊断] 尝试自动重连...');
            connectWebSocket();
          }, 3000);
        }
      };

      // 连接超时检查
      setTimeout(() => {
        if (ws.readyState === WebSocket.CONNECTING) {
          ws.close();
          setConnecting(false);
          setLogs(prev => [...prev, {
            timestamp: new Date().toISOString(),
            level: 'error',
            message: '❌ WebSocket连接超时',
            source: 'diagnostic',
            category: 'error'
          }]);
        }
      }, 10000);

    } catch (error) {
      console.error('[WebSocket诊断] 连接异常:', error);
      setConnecting(false);
      setLogs(prev => [...prev, {
        timestamp: new Date().toISOString(),
        level: 'error',
        message: `❌ WebSocket连接异常: ${error}`,
        source: 'diagnostic',
        category: 'error'
      }]);
    }
  };

  const disconnectWebSocket = () => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    
    if (wsRef.current) {
      wsRef.current.close(1000, '用户主动断开');
      wsRef.current = null;
    }
    
    setConnected(false);
    setConnecting(false);
  };

  const checkConnectionStatus = async () => {
    try {
      const response = await fetch('http://localhost:8001/api/logs/websocket/status');
      const data = await response.json();
      setConnectionStatus(data);
      
      setLogs(prev => [...prev, {
        timestamp: new Date().toISOString(),
        level: 'info',
        message: `📊 服务器状态: ${data.message}`,
        source: 'status_check',
        category: 'system'
      }]);
    } catch (error) {
      setLogs(prev => [...prev, {
        timestamp: new Date().toISOString(),
        level: 'error',
        message: `❌ 无法获取服务器状态: ${error}`,
        source: 'status_check',
        category: 'error'
      }]);
    }
  };

  const testWebSocketLogs = async () => {
    try {
      const response = await fetch('http://localhost:8001/api/logs/websocket/test', {
        method: 'POST'
      });
      const data = await response.json();
      
      if (data.success) {
        toast({
          title: "WebSocket日志测试",
          description: `已发送 ${data.test_messages?.length || 0} 条测试消息`,
          type: "success"
        });
      } else {
        toast({
          title: "WebSocket日志测试失败",
          description: data.message,
          type: "error"
        });
      }
    } catch (error) {
      toast({
        title: "测试请求失败",
        description: `${error}`,
        type: "error"
      });
    }
  };

  const clearLogs = () => {
    setLogs([]);
    setMessageCount(0);
  };

  useEffect(() => {
    // 组件挂载时自动连接
    connectWebSocket();
    checkConnectionStatus();

    return () => {
      disconnectWebSocket();
    };
  }, []);

  const getStatusIcon = () => {
    if (connecting) return <RefreshCw className="w-5 h-5 animate-spin text-blue-500" />;
    if (connected) return <Wifi className="w-5 h-5 text-green-500" />;
    return <WifiOff className="w-5 h-5 text-red-500" />;
  };

  const getStatusText = () => {
    if (connecting) return "连接中...";
    if (connected) return "已连接";
    return "未连接";
  };

  const getLevelIcon = (level: string) => {
    switch (level?.toLowerCase()) {
      case 'error':
        return <XCircle className="w-4 h-4 text-red-500" />;
      case 'warning':
        return <AlertTriangle className="w-4 h-4 text-yellow-500" />;
      case 'info':
      default:
        return <CheckCircle className="w-4 h-4 text-blue-500" />;
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* 连接状态卡片 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span className="flex items-center gap-2">
              {getStatusIcon()}
              WebSocket连接状态
            </span>
            <Badge variant={connected ? "default" : "destructive"}>
              {getStatusText()}
            </Badge>
          </CardTitle>
          <CardDescription>
            日志WebSocket连接诊断和测试工具
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="text-center p-3 border rounded">
              <div className="text-2xl font-bold text-blue-600">{messageCount}</div>
              <div className="text-sm text-muted-foreground">收到消息数</div>
            </div>
            <div className="text-center p-3 border rounded">
              <div className="text-sm text-muted-foreground">最后消息</div>
              <div className="font-mono text-xs">{lastMessage || '无'}</div>
            </div>
          </div>

          {connectionStatus && (
            <div className="p-3 bg-muted rounded">
              <div className="text-sm">
                <div>服务器连接数: {connectionStatus.active_connections}</div>
                <div>状态: {connectionStatus.status}</div>
                <div>端点: {connectionStatus.endpoint}</div>
              </div>
            </div>
          )}

          <div className="flex flex-wrap gap-2">
            <Button 
              onClick={connected ? disconnectWebSocket : connectWebSocket}
              disabled={connecting}
              variant={connected ? "destructive" : "default"}
            >
              {connecting ? (
                <>
                  <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                  连接中
                </>
              ) : connected ? (
                <>
                  <WifiOff className="w-4 h-4 mr-2" />
                  断开连接
                </>
              ) : (
                <>
                  <Wifi className="w-4 h-4 mr-2" />
                  连接
                </>
              )}
            </Button>
            
            <Button 
              onClick={checkConnectionStatus}
              variant="outline"
            >
              <Activity className="w-4 h-4 mr-2" />
              检查状态
            </Button>
            
            <Button 
              onClick={testWebSocketLogs}
              variant="outline"
              disabled={!connected}
            >
              测试日志
            </Button>
            
            <Button 
              onClick={clearLogs}
              variant="outline"
              size="sm"
            >
              清空日志
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* 日志显示卡片 */}
      <Card>
        <CardHeader>
          <CardTitle>实时日志</CardTitle>
          <CardDescription>
            WebSocket接收到的日志消息 (最近100条)
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-96">
            <div className="space-y-2">
              {logs.length === 0 ? (
                <div className="text-center text-muted-foreground py-8">
                  暂无日志消息
                </div>
              ) : (
                logs.map((log, index) => (
                  <div key={index} className="flex items-start gap-2 p-2 text-sm border-b">
                    {getLevelIcon(log.level)}
                    <div className="flex-1 min-w-0">
                      <div className="font-mono text-xs text-muted-foreground">
                        {new Date(log.timestamp).toLocaleTimeString()}
                      </div>
                      <div className="break-words">{log.message}</div>
                      {log.source && (
                        <div className="text-xs text-muted-foreground">
                          来源: {log.source}
                        </div>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  );
}