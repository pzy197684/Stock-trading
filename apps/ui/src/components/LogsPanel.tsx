import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select";
import { Input } from "./ui/input";
import { Badge } from "./ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "./ui/table";
import { ScrollArea } from "./ui/scroll-area";
import { useToast } from "./ui/toast";
import { Download, Wifi, WifiOff } from "lucide-react";

interface LogEntry {
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

export function LogsPanel() {
  const [levelFilter, setLevelFilter] = useState("all");
  const [sourceFilter, setSourceFilter] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [isConnected, setIsConnected] = useState(false);
  
  // 日志数据状态
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [filteredLogs, setFilteredLogs] = useState<LogEntry[]>([]);
  
  const { toast } = useToast();

  // WebSocket连接
  useEffect(() => {
    const connectWebSocket = () => {
      console.log('尝试连接WebSocket: ws://localhost:8001/ws/logs');
      const ws = new WebSocket('ws://localhost:8001/ws/logs');
      
      ws.onopen = () => {
        setIsConnected(true);
        console.log('✅ 日志WebSocket连接成功');
        toast({
          type: "success",
          title: "WebSocket连接成功",
          description: "实时日志已启用",
        });
      };
      
      ws.onmessage = (event) => {
        try {
          console.log('📨 收到WebSocket消息:', event.data);
          const message = JSON.parse(event.data);
          if (message.type === 'log' && message.data) {
            const logData = message.data;
            
            // 过滤空日志和垃圾信息
            if (!logData.message || 
                logData.message.trim() === '' || 
                logData.message === '-' ||
                (logData.level === 'debug' && (
                  logData.message.includes('API调用开始') ||
                  logData.message.includes('API调用成功') ||
                  logData.message.includes('WebSocket连接状态')
                ))) {
              return; // 跳过这些消息
            }
            
            console.log('📝 添加新日志:', logData);
            setLogs(prev => [...prev, logData].slice(-1000)); // 保留最新1000条
          }
        } catch (error) {
          console.error('❌ 解析日志消息失败:', error);
        }
      };
      
      ws.onclose = () => {
        setIsConnected(false);
        console.log('❌ 日志WebSocket连接关闭，5秒后重连');
        toast({
          type: "error",
          title: "WebSocket连接断开",
          description: "5秒后自动重连"
        });
        setTimeout(connectWebSocket, 5000);
      };
      
      ws.onerror = (error) => {
        console.error('❌ 日志WebSocket错误:', error);
        setIsConnected(false);
        toast({
          type: "error",
          title: "WebSocket连接失败",
          description: "请检查API服务器状态"
        });
      };
    };

    connectWebSocket();
  }, []);

  // 过滤日志
  useEffect(() => {
    let filtered = logs;

    // 级别过滤
    if (levelFilter !== "all") {
      filtered = filtered.filter(log => log.level === levelFilter);
    }

    // 来源过滤
    if (sourceFilter !== "all") {
      filtered = filtered.filter(log => log.source === sourceFilter);
    }

    // 搜索过滤
    if (searchQuery) {
      filtered = filtered.filter(log => 
        log.message.toLowerCase().includes(searchQuery.toLowerCase()) ||
        log.source?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        log.category?.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    setFilteredLogs(filtered);
  }, [logs, levelFilter, sourceFilter, searchQuery]);

  // 获取日志级别的颜色
  const getLevelBadgeColor = (level: string) => {
    switch (level) {
      case 'error':
      case 'critical':
        return 'bg-red-500';
      case 'warning':
        return 'bg-yellow-500';
      case 'info':
        return 'bg-blue-500';
      case 'debug':
        return 'bg-gray-500';
      case 'trade':
        return 'bg-green-500';
      default:
        return 'bg-gray-400';
    }
  };

  // 将英文日志级别转换为中文
  const getLevelDisplayName = (level: string) => {
    switch (level) {
      case 'debug':
        return '调试';
      case 'info':
        return '信息';
      case 'warning':
        return '警告';
      case 'error':
        return '错误';
      case 'critical':
        return '严重';
      case 'trade':
        return '交易';
      default:
        return level; // 如果没有匹配的，返回原值
    }
  };

  // 格式化时间戳
  const formatTimestamp = (timestamp: string) => {
    try {
      if (!timestamp) {
        return new Date().toLocaleString('zh-CN');
      }
      
      const date = new Date(timestamp);
      
      // 检查日期是否有效
      if (isNaN(date.getTime())) {
        console.warn('无效的时间戳:', timestamp);
        return new Date().toLocaleString('zh-CN');
      }
      
      return date.toLocaleString('zh-CN');
    } catch (error) {
      console.error('时间戳格式化错误:', error, timestamp);
      return new Date().toLocaleString('zh-CN');
    }
  };

  // 清空日志
  const clearLogs = () => {
    setLogs([]);
    toast({
      type: "success",
      title: "日志已清空",
      description: "所有日志记录已被清除"
    });
  };

  // 导出日志
  const exportLogs = () => {
    const dataStr = JSON.stringify(filteredLogs, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `trading-logs-${new Date().toISOString().slice(0, 10)}.json`;
    link.click();
    URL.revokeObjectURL(url);
    
    toast({
      type: "success",
      title: "日志已导出",
      description: "日志文件已下载到本地"
    });
  };

  return (
    <Card className="w-full h-full">
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between">
          <CardTitle className="text-xl font-bold">系统日志</CardTitle>
          <div className="flex items-center gap-2">
            {isConnected ? (
              <Badge variant="outline" className="text-green-600">
                <Wifi className="w-3 h-3 mr-1" />
                已连接
              </Badge>
            ) : (
              <Badge variant="outline" className="text-red-600">
                <WifiOff className="w-3 h-3 mr-1" />
                未连接
              </Badge>
            )}
            <Button variant="outline" size="sm" onClick={clearLogs}>
              清空日志
            </Button>
            <Button variant="outline" size="sm" onClick={exportLogs}>
              <Download className="w-4 h-4 mr-1" />
              导出
            </Button>
          </div>
        </div>
      </CardHeader>
      
      <CardContent>
        {/* 过滤器 */}
        <div className="flex gap-4 mb-4">
          <Select value={levelFilter} onValueChange={setLevelFilter}>
            <SelectTrigger className="w-32">
              <SelectValue placeholder="级别" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">全部级别</SelectItem>
              <SelectItem value="debug">调试</SelectItem>
              <SelectItem value="info">信息</SelectItem>
              <SelectItem value="warning">警告</SelectItem>
              <SelectItem value="error">错误</SelectItem>
              <SelectItem value="critical">严重</SelectItem>
              <SelectItem value="trade">交易</SelectItem>
            </SelectContent>
          </Select>

          <Select value={sourceFilter} onValueChange={setSourceFilter}>
            <SelectTrigger className="w-32">
              <SelectValue placeholder="来源" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">全部来源</SelectItem>
              <SelectItem value="API">API</SelectItem>
              <SelectItem value="strategy">策略</SelectItem>
              <SelectItem value="trading">交易</SelectItem>
              <SelectItem value="websocket">WebSocket</SelectItem>
              <SelectItem value="system">系统</SelectItem>
            </SelectContent>
          </Select>

          <div className="flex-1">
            <Input
              placeholder="搜索日志..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full"
            />
          </div>
        </div>

        {/* 日志表格 */}
        <ScrollArea className="h-[500px] w-full border rounded-md">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[140px]">时间</TableHead>
                <TableHead className="w-[80px]">级别</TableHead>
                <TableHead className="w-[100px]">来源</TableHead>
                <TableHead>消息</TableHead>
                <TableHead className="w-[120px]">位置</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredLogs.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} className="text-center text-gray-500 py-8">
                    {logs.length === 0 ? '暂无日志记录' : '没有符合条件的日志'}
                  </TableCell>
                </TableRow>
              ) : (
                filteredLogs.slice(-100).reverse().map((log, index) => (
                  <TableRow key={index} className="hover:bg-gray-50">
                    <TableCell className="text-xs">
                      {formatTimestamp(log.timestamp)}
                    </TableCell>
                    <TableCell>
                      <Badge className={`${getLevelBadgeColor(log.level)} text-white text-xs`}>
                        {getLevelDisplayName(log.level)}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-xs">
                      {log.source || '-'}
                    </TableCell>
                    <TableCell className="max-w-[400px] truncate text-xs">
                      {log.message}
                    </TableCell>
                    <TableCell className="text-xs text-gray-500">
                      {log.file && log.function && log.line 
                        ? `${log.file}:${log.function}:${log.line}`
                        : '-'
                      }
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </ScrollArea>

        {/* 统计信息 */}
        <div className="mt-4 text-sm text-gray-500">
          总计 {logs.length} 条日志，显示 {filteredLogs.length} 条
        </div>
      </CardContent>
    </Card>
  );
}