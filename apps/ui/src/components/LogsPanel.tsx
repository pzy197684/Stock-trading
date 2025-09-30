import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select";
import { Input } from "./ui/input";
import { Badge } from "./ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "./ui/table";
import { ScrollArea } from "./ui/scroll-area";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import { useToast } from "./ui/toast";
import { Download, Search, Filter, TrendingUp, TrendingDown, DollarSign, FileText, List, BarChart3 } from "lucide-react";

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
  
  // API数据状态
  const [apiLogs, setApiLogs] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);
  
  const { toast } = useToast();

  // 从API获取日志
  const fetchLogs = async () => {
    try {
      setIsLoading(true);
      setApiError(null);
      
      const params = new URLSearchParams();
      params.append('limit', '100');
      if (levelFilter !== 'all') {
        params.append('level', levelFilter.toUpperCase());
      }
      
      const response = await fetch(`http://localhost:8001/api/logs/recent?${params}`);
      if (!response.ok) {
        throw new Error(`API错误: ${response.status}`);
      }
      
      const data = await response.json();
      setApiLogs(data.logs || []);
      
      if (data.note) {
        setApiError(data.note);
      }
    } catch (error) {
      console.error('获取日志失败:', error);
      setApiError('无法连接到API服务器');
    } finally {
      setIsLoading(false);
    }
  };

  // 初始化和定期刷新日志
  useEffect(() => {
    fetchLogs();
    
    const interval = setInterval(fetchLogs, 10000); // 每10秒刷新日志
    return () => clearInterval(interval);
  }, [levelFilter]);

  // 响应式刷新日志
  useEffect(() => {
    if (levelFilter !== 'all') {
      fetchLogs();
    }
  }, [levelFilter]);

  // 直接使用API数据
  const logs = apiLogs.map((apiLog: any, index: number) => ({
    id: index.toString(),
    timestamp: apiLog.timestamp,
    level: apiLog.level.toLowerCase(),
    account: apiLog.source || "系统",
    strategy: "未知", // API暂不支持
    message: apiLog.message,
    profit: undefined // API日志暂不包含盈亏信息
  }));

  const accounts = ["all", ...Array.from(new Set(logs.map(log => log.account)))];
  
  const filteredLogs = logs.filter(log => {
    const matchesLevel = levelFilter === "all" || log.level === levelFilter;
    const matchesAccount = accountFilter === "all" || log.account === accountFilter;
    const matchesSearch = searchQuery === "" || 
      log.message.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (log.strategy && log.strategy.toLowerCase().includes(searchQuery.toLowerCase()));
    
    return matchesLevel && matchesAccount && matchesSearch;
  });

  const totalProfit = logs
    .filter(log => log.profit !== undefined)
    .reduce((sum, log) => sum + (log.profit || 0), 0);

  const profitableTrades = logs.filter(log => log.profit && log.profit > 0).length;
  const losingTrades = logs.filter(log => log.profit && log.profit < 0).length;
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
    
    toast({ 
      type: 'success', 
      title: `导出${format.toUpperCase()}成功`, 
      description: '文件已下载到本地' 
    });
  };

  return (
    <div className="space-y-4 md:space-y-6">
      {/* Profit Statistics - Mobile Responsive */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-2 md:gap-4">
        <Card>
          <CardContent className="p-3 md:p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs md:text-sm text-muted-foreground">总盈亏</p>
                <p className={`text-lg md:text-2xl font-bold ${totalProfit >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {totalProfit >= 0 ? '+' : ''}{totalProfit.toFixed(2)}
                </p>
                <p className="text-xs text-muted-foreground">USDT</p>
              </div>
              <DollarSign className="w-6 h-6 md:w-8 md:h-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-3 md:p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs md:text-sm text-muted-foreground">盈利交易</p>
                <p className="text-lg md:text-2xl font-bold text-green-600">{profitableTrades}</p>
                <p className="text-xs text-muted-foreground">次</p>
              </div>
              <TrendingUp className="w-6 h-6 md:w-8 md:h-8 text-green-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-3 md:p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs md:text-sm text-muted-foreground">亏损交易</p>
                <p className="text-lg md:text-2xl font-bold text-red-600">{losingTrades}</p>
                <p className="text-xs text-muted-foreground">次</p>
              </div>
              <TrendingDown className="w-6 h-6 md:w-8 md:h-8 text-red-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-3 md:p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs md:text-sm text-muted-foreground">胜率</p>
                <p className="text-lg md:text-2xl font-bold">{winRate}</p>
                <p className="text-xs text-muted-foreground">%</p>
              </div>
              <Filter className="w-6 h-6 md:w-8 md:h-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content with Tabs */}
      <Tabs defaultValue="logs" className="w-full">
        <TabsList className="grid w-full grid-cols-3 h-auto">
          <TabsTrigger value="logs" className="flex items-center gap-1 md:gap-2 text-xs md:text-sm p-2 md:p-3 transition-all duration-300">
            <FileText className="w-3 h-3 md:w-4 md:h-4" />
            交易日志
          </TabsTrigger>
          <TabsTrigger value="trades" className="flex items-center gap-1 md:gap-2 text-xs md:text-sm p-2 md:p-3 transition-all duration-300">
            <List className="w-3 h-3 md:w-4 md:h-4" />
            交易清单
          </TabsTrigger>
          <TabsTrigger value="summary" className="flex items-center gap-1 md:gap-2 text-xs md:text-sm p-2 md:p-3 transition-all duration-300">
            <BarChart3 className="w-3 h-3 md:w-4 md:h-4" />
            盈亏汇总
          </TabsTrigger>
        </TabsList>

        <TabsContent value="logs" className="space-y-4 data-[state=active]:animate-in data-[state=active]:fade-in-0 data-[state=active]:slide-in-from-bottom-2 duration-300">
          <Card>
            <CardHeader>
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <CardTitle>交易日志</CardTitle>
                <div className="flex gap-2">
                  <Button variant="outline" size="sm" onClick={() => exportLogs('csv')} className="transition-all duration-200">
                    <Download className="w-4 h-4 mr-1" />
                    导出CSV
                  </Button>
                  <Button variant="outline" size="sm" onClick={() => exportLogs('txt')} className="transition-all duration-200">
                    <Download className="w-4 h-4 mr-1" />
                    导出TXT
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="flex flex-col md:flex-row gap-2 md:gap-4 mb-4">
                <div className="flex items-center gap-2 flex-1 min-w-0">
                  <Search className="w-4 h-4 text-muted-foreground" />
                  <Input
                    placeholder="搜索日志..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="flex-1"
                  />
                </div>
                
                <Select value={levelFilter} onValueChange={setLevelFilter}>
                  <SelectTrigger className="w-full md:w-32">
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
                  <SelectTrigger className="w-full md:w-48">
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

              <div className="border rounded-lg overflow-hidden">
                <ScrollArea className="h-96 pr-4">
                  <Table>
                    <TableHeader className="sticky top-0 bg-background z-10">
                      <TableRow>
                        <TableHead className="min-w-[140px]">时间</TableHead>
                        <TableHead className="min-w-[80px]">级别</TableHead>
                        <TableHead className="min-w-[120px]">账户</TableHead>
                        <TableHead className="min-w-[100px]">策略</TableHead>
                        <TableHead className="min-w-[200px]">消息</TableHead>
                        <TableHead className="text-right min-w-[100px] pr-4">盈亏</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {filteredLogs.map((log) => (
                        <TableRow key={log.id}>
                          <TableCell className="font-mono text-xs md:text-sm">{log.timestamp}</TableCell>
                          <TableCell>{getLevelBadge(log.level)}</TableCell>
                          <TableCell className="text-xs md:text-sm">{log.account}</TableCell>
                          <TableCell className="text-xs md:text-sm">{log.strategy}</TableCell>
                          <TableCell className="max-w-md truncate text-xs md:text-sm">{log.message}</TableCell>
                          <TableCell className="text-right pr-4">
                            {log.profit !== undefined && (
                              <span className={`text-xs md:text-sm ${log.profit >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                {log.profit >= 0 ? '+' : ''}{log.profit.toFixed(2)} USDT
                              </span>
                            )}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </ScrollArea>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="trades" className="space-y-4 data-[state=active]:animate-in data-[state=active]:fade-in-0 data-[state=active]:slide-in-from-bottom-2 duration-300">
          <Card>
            <CardHeader>
              <CardTitle>交易清单</CardTitle>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-96 pr-4">
                <div className="space-y-4 pb-4">
                  {logs.filter(log => log.profit !== undefined).map((trade) => (
                    <div key={trade.id} className="border rounded-lg p-3 md:p-4 transition-all duration-200 hover:bg-muted/30">
                      <div className="flex flex-col md:flex-row md:items-center justify-between gap-2">
                        <div>
                          <div className="flex items-center gap-2 mb-1">
                            <span className="font-medium text-sm md:text-base">{trade.account}</span>
                            <Badge variant="outline" className="text-xs">{trade.strategy}</Badge>
                          </div>
                          <p className="text-xs md:text-sm text-muted-foreground">{trade.message}</p>
                          <p className="text-xs text-muted-foreground mt-1">{trade.timestamp}</p>
                        </div>
                        <div className={`text-right ${trade.profit && trade.profit >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                          <p className="font-bold text-sm md:text-lg">
                            {trade.profit && trade.profit >= 0 ? '+' : ''}{trade.profit?.toFixed(2)} USDT
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="summary" className="space-y-4 data-[state=active]:animate-in data-[state=active]:fade-in-0 data-[state=active]:slide-in-from-bottom-2 duration-300">
          <Card>
            <CardHeader>
              <CardTitle>盈亏汇总</CardTitle>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-96 pr-4">
                <div className="space-y-6 pb-4">
                  {/* Account Summary */}
                  <div>
                    <h4 className="font-medium mb-4">按账户统计</h4>
                    <div className="space-y-3">
                      {accounts.slice(1).map(account => {
                        const accountTrades = logs.filter(log => log.account === account && log.profit !== undefined);
                        const accountProfit = accountTrades.reduce((sum, log) => sum + (log.profit || 0), 0);
                        const accountTradeCount = accountTrades.length;
                        
                        return (
                          <div key={account} className="flex items-center justify-between p-3 bg-muted/30 rounded-lg transition-all duration-200 hover:bg-muted/50">
                            <div>
                              <p className="font-medium text-sm md:text-base">{account}</p>
                              <p className="text-xs md:text-sm text-muted-foreground">{accountTradeCount} 笔交易</p>
                            </div>
                            <div className={`text-right ${accountProfit >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                              <p className="font-bold text-sm md:text-lg">
                                {accountProfit >= 0 ? '+' : ''}{accountProfit.toFixed(2)} USDT
                              </p>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  {/* Strategy Summary */}
                  <div>
                    <h4 className="font-medium mb-4">按策略统计</h4>
                    <div className="space-y-3">
                      {Array.from(new Set(logs.map(log => log.strategy))).map(strategy => {
                        const strategyTrades = logs.filter(log => log.strategy === strategy && log.profit !== undefined);
                        const strategyProfit = strategyTrades.reduce((sum, log) => sum + (log.profit || 0), 0);
                        const strategyTradeCount = strategyTrades.length;
                        
                        return (
                          <div key={strategy} className="flex items-center justify-between p-3 bg-muted/30 rounded-lg transition-all duration-200 hover:bg-muted/50">
                            <div>
                              <p className="font-medium text-sm md:text-base">{strategy}</p>
                              <p className="text-xs md:text-sm text-muted-foreground">{strategyTradeCount} 笔交易</p>
                            </div>
                            <div className={`text-right ${strategyProfit >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                              <p className="font-bold text-sm md:text-lg">
                                {strategyProfit >= 0 ? '+' : ''}{strategyProfit.toFixed(2)} USDT
                              </p>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}