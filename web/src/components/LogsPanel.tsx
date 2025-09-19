import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select";
import { Input } from "./ui/input";
import { Badge } from "./ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "./ui/table";
import { ScrollArea } from "./ui/scroll-area";
import { Download, Search, Filter, TrendingUp, TrendingDown, DollarSign } from "lucide-react";

interface LogEntry {
  id: string;
  timestamp: string;
  level: 'info' | 'warning' | 'error' | 'success';
  account: string;
  strategy: string;
  message: string;
  profit?: number;
}

export function LogsPanel() {
  const [levelFilter, setLevelFilter] = useState("all");
  const [accountFilter, setAccountFilter] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");

  const mockLogs: LogEntry[] = [
    {
      id: "1",
      timestamp: "2024-09-19 14:35:22",
      level: "success",
      account: "币安-账户A",
      strategy: "网格策略",
      message: "买入订单执行成功 BTC/USDT @67,500",
      profit: 25.5
    },
    {
      id: "2",
      timestamp: "2024-09-19 14:34:15",
      level: "info",
      account: "火币-账户B",
      strategy: "套利策略",
      message: "检测到套利机会 ETH/USDT 价差0.5%"
    },
    {
      id: "3",
      timestamp: "2024-09-19 14:33:08",
      level: "warning",
      account: "OKEx-账户C",
      strategy: "趋势跟踪",
      message: "网络延迟较高，建议检查连接"
    },
    {
      id: "4",
      timestamp: "2024-09-19 14:32:45",
      level: "error",
      account: "OKEx-账户C",
      strategy: "趋势跟踪",
      message: "API密钥验证失败"
    },
    {
      id: "5",
      timestamp: "2024-09-19 14:31:30",
      level: "success",
      account: "火币-账户B",
      strategy: "套利策略",
      message: "套利交易完成",
      profit: 15.8
    },
    {
      id: "6",
      timestamp: "2024-09-19 14:30:12",
      level: "info",
      account: "币安-账户A",
      strategy: "网格策略",
      message: "网格策略启动成功"
    }
  ];

  const accounts = ["all", ...Array.from(new Set(mockLogs.map(log => log.account)))];
  
  const filteredLogs = mockLogs.filter(log => {
    const matchesLevel = levelFilter === "all" || log.level === levelFilter;
    const matchesAccount = accountFilter === "all" || log.account === accountFilter;
    const matchesSearch = searchQuery === "" || 
      log.message.toLowerCase().includes(searchQuery.toLowerCase()) ||
      log.strategy.toLowerCase().includes(searchQuery.toLowerCase());
    
    return matchesLevel && matchesAccount && matchesSearch;
  });

  const totalProfit = mockLogs
    .filter(log => log.profit !== undefined)
    .reduce((sum, log) => sum + (log.profit || 0), 0);

  const profitableTrades = mockLogs.filter(log => log.profit && log.profit > 0).length;
  const losingTrades = mockLogs.filter(log => log.profit && log.profit < 0).length;
  const winRate = profitableTrades + losingTrades > 0 
    ? (profitableTrades / (profitableTrades + losingTrades) * 100).toFixed(1)
    : "0";

  const getLevelBadge = (level: string) => {
    switch (level) {
      case 'success':
        return <Badge className="bg-green-100 text-green-800 border-green-200">成功</Badge>;
      case 'info':
        return <Badge className="bg-blue-100 text-blue-800 border-blue-200">信息</Badge>;
      case 'warning':
        return <Badge className="bg-yellow-100 text-yellow-800 border-yellow-200">警告</Badge>;
      case 'error':
        return <Badge className="bg-red-100 text-red-800 border-red-200">错误</Badge>;
      default:
        return <Badge>未知</Badge>;
    }
  };

  const exportLogs = (format: 'csv' | 'txt') => {
    const headers = ['时间', '级别', '账户', '策略', '消息', '盈亏'];
    const data = filteredLogs.map(log => [
      log.timestamp,
      log.level,
      log.account,
      log.strategy,
      log.message,
      log.profit?.toString() || ''
    ]);

    let content = '';
    if (format === 'csv') {
      content = [headers, ...data].map(row => row.join(',')).join('\n');
    } else {
      content = [
        headers.join('\t'),
        ...data.map(row => row.join('\t'))
      ].join('\n');
    }

    const blob = new Blob([content], { type: format === 'csv' ? 'text/csv' : 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `logs_${new Date().toISOString().split('T')[0]}.${format}`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      {/* Profit Statistics */}
      <div className="grid grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">总盈亏</p>
                <p className={`text-2xl font-bold ${totalProfit >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {totalProfit >= 0 ? '+' : ''}{totalProfit.toFixed(2)} USDT
                </p>
              </div>
              <DollarSign className="w-8 h-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">盈利交易</p>
                <p className="text-2xl font-bold text-green-600">{profitableTrades}</p>
              </div>
              <TrendingUp className="w-8 h-8 text-green-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">亏损交易</p>
                <p className="text-2xl font-bold text-red-600">{losingTrades}</p>
              </div>
              <TrendingDown className="w-8 h-8 text-red-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">胜率</p>
                <p className="text-2xl font-bold">{winRate}%</p>
              </div>
              <Filter className="w-8 h-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters and Export */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>交易日志</CardTitle>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" onClick={() => exportLogs('csv')}>
                <Download className="w-4 h-4 mr-1" />
                导出CSV
              </Button>
              <Button variant="outline" size="sm" onClick={() => exportLogs('txt')}>
                <Download className="w-4 h-4 mr-1" />
                导出TXT
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4 mb-4">
            <div className="flex items-center gap-2">
              <Search className="w-4 h-4 text-muted-foreground" />
              <Input
                placeholder="搜索日志..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-64"
              />
            </div>
            
            <Select value={levelFilter} onValueChange={setLevelFilter}>
              <SelectTrigger className="w-32">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部级别</SelectItem>
                <SelectItem value="success">成功</SelectItem>
                <SelectItem value="info">信息</SelectItem>
                <SelectItem value="warning">警告</SelectItem>
                <SelectItem value="error">错误</SelectItem>
              </SelectContent>
            </Select>

            <Select value={accountFilter} onValueChange={setAccountFilter}>
              <SelectTrigger className="w-48">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部账户</SelectItem>
                {accounts.slice(1).map(account => (
                  <SelectItem key={account} value={account}>{account}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <ScrollArea className="h-96">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>时间</TableHead>
                  <TableHead>级别</TableHead>
                  <TableHead>账户</TableHead>
                  <TableHead>策略</TableHead>
                  <TableHead>消息</TableHead>
                  <TableHead className="text-right">盈亏</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredLogs.map((log) => (
                  <TableRow key={log.id}>
                    <TableCell className="font-mono text-sm">{log.timestamp}</TableCell>
                    <TableCell>{getLevelBadge(log.level)}</TableCell>
                    <TableCell>{log.account}</TableCell>
                    <TableCell>{log.strategy}</TableCell>
                    <TableCell className="max-w-md truncate">{log.message}</TableCell>
                    <TableCell className="text-right">
                      {log.profit !== undefined && (
                        <span className={log.profit >= 0 ? 'text-green-600' : 'text-red-600'}>
                          {log.profit >= 0 ? '+' : ''}{log.profit.toFixed(2)} USDT
                        </span>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  );
}