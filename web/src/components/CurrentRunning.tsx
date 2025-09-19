import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "./ui/dialog";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from "./ui/alert-dialog";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "./ui/collapsible";
import { Progress } from "./ui/progress";
import { ChevronDown, Plus, Square, AlertTriangle, Activity, TrendingUp, TrendingDown } from "lucide-react";
import { cn } from "./ui/utils";

interface TradingInstance {
  id: string;
  platform: string;
  account: string;
  strategy: string;
  status: 'running' | 'stopped' | 'error';
  owner: string;
  profit: number;
  positions: { long: number; short: number };
  logs: string[];
}

export function CurrentRunning() {
  const [selectedOwner, setSelectedOwner] = useState<string>("all");
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [expandedInstances, setExpandedInstances] = useState<Set<string>>(new Set());

  const mockInstances: TradingInstance[] = [
    {
      id: "1",
      platform: "币安",
      account: "账户A",
      strategy: "网格策略",
      status: "running",
      owner: "张三",
      profit: 1250.5,
      positions: { long: 3, short: 2 },
      logs: ["14:30 开启网格交易", "14:35 买入订单执行", "14:40 卖出订单执行"]
    },
    {
      id: "2",
      platform: "火币",
      account: "账户B",
      strategy: "套利策略",
      status: "running",
      owner: "李四",
      profit: -320.8,
      positions: { long: 1, short: 4 },
      logs: ["14:25 检测到套利机会", "14:30 执行套利订单", "14:38 套利完成"]
    },
    {
      id: "3",
      platform: "OKEx",
      account: "账户C",
      strategy: "趋势跟踪",
      status: "error",
      owner: "张三",
      profit: 0,
      positions: { long: 0, short: 0 },
      logs: ["14:20 策略启动失败", "14:21 连接错误"]
    }
  ];

  const owners = ["all", ...Array.from(new Set(mockInstances.map(i => i.owner)))];
  const filteredInstances = selectedOwner === "all" 
    ? mockInstances 
    : mockInstances.filter(i => i.owner === selectedOwner);

  const toggleExpanded = (instanceId: string) => {
    const newExpanded = new Set(expandedInstances);
    if (newExpanded.has(instanceId)) {
      newExpanded.delete(instanceId);
    } else {
      newExpanded.add(instanceId);
    }
    setExpandedInstances(newExpanded);
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'running':
        return <Badge className="bg-green-100 text-green-800 border-green-200">运行中</Badge>;
      case 'stopped':
        return <Badge className="bg-gray-100 text-gray-800 border-gray-200">已停止</Badge>;
      case 'error':
        return <Badge className="bg-red-100 text-red-800 border-red-200">错误</Badge>;
      default:
        return <Badge>未知</Badge>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Owner Filter */}
      {owners.length > 2 && (
        <div className="flex items-center gap-4">
          <label>拥有人筛选:</label>
          <Select value={selectedOwner} onValueChange={setSelectedOwner}>
            <SelectTrigger className="w-48">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">全部</SelectItem>
              {owners.slice(1).map(owner => (
                <SelectItem key={owner} value={owner}>{owner}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      )}

      {/* Running Instances */}
      <div className="space-y-4">
        {filteredInstances.map((instance) => (
          <Card key={instance.id} className="w-full">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <CardTitle className="text-lg">{instance.account}</CardTitle>
                  {getStatusBadge(instance.status)}
                  <span className="text-sm text-muted-foreground">拥有人: {instance.owner}</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className={cn(
                    "flex items-center gap-1 px-2 py-1 rounded",
                    instance.profit >= 0 ? "text-green-600 bg-green-50" : "text-red-600 bg-red-50"
                  )}>
                    {instance.profit >= 0 ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
                    <span className="font-medium">
                      {instance.profit >= 0 ? '+' : ''}{instance.profit.toFixed(2)} USDT
                    </span>
                  </div>
                  <Collapsible>
                    <CollapsibleTrigger asChild>
                      <Button 
                        variant="ghost" 
                        size="sm"
                        onClick={() => toggleExpanded(instance.id)}
                      >
                        <ChevronDown className={cn(
                          "w-4 h-4 transition-transform",
                          expandedInstances.has(instance.id) && "rotate-180"
                        )} />
                      </Button>
                    </CollapsibleTrigger>
                  </Collapsible>
                </div>
              </div>
            </CardHeader>
            
            <CardContent className="pt-0">
              <div className="grid grid-cols-3 gap-4 mb-4">
                <div>
                  <span className="text-sm text-muted-foreground">运行平台</span>
                  <p className="font-medium">{instance.platform}</p>
                </div>
                <div>
                  <span className="text-sm text-muted-foreground">策略</span>
                  <p className="font-medium">{instance.strategy}</p>
                </div>
                <div>
                  <span className="text-sm text-muted-foreground">持仓</span>
                  <p className="font-medium">多:{instance.positions.long} 空:{instance.positions.short}</p>
                </div>
              </div>

              <div className="flex gap-2 mb-4">
                <AlertDialog>
                  <AlertDialogTrigger asChild>
                    <Button variant="outline" size="sm">
                      <Square className="w-4 h-4 mr-1" />
                      停止策略
                    </Button>
                  </AlertDialogTrigger>
                  <AlertDialogContent>
                    <AlertDialogHeader>
                      <AlertDialogTitle>确认停止策略</AlertDialogTitle>
                      <AlertDialogDescription>
                        您确定要停止 {instance.account} 的 {instance.strategy} 吗？
                      </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                      <AlertDialogCancel>取消</AlertDialogCancel>
                      <AlertDialogAction>确认停止</AlertDialogAction>
                    </AlertDialogFooter>
                  </AlertDialogContent>
                </AlertDialog>

                <AlertDialog>
                  <AlertDialogTrigger asChild>
                    <Button variant="destructive" size="sm">
                      <AlertTriangle className="w-4 h-4 mr-1" />
                      一键平仓并停止
                    </Button>
                  </AlertDialogTrigger>
                  <AlertDialogContent>
                    <AlertDialogHeader>
                      <AlertDialogTitle>确认平仓并停止</AlertDialogTitle>
                      <AlertDialogDescription>
                        这将立即平仓所有持仓并停止策略，此操作不可撤销。您确定要继续吗？
                      </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                      <AlertDialogCancel>取消</AlertDialogCancel>
                      <AlertDialogAction className="bg-destructive text-destructive-foreground">
                        确认平仓并停止
                      </AlertDialogAction>
                    </AlertDialogFooter>
                  </AlertDialogContent>
                </AlertDialog>
              </div>

              <Collapsible open={expandedInstances.has(instance.id)}>
                <CollapsibleContent className="space-y-4">
                  <div className="border rounded-lg p-4 bg-muted/50">
                    <h4 className="font-medium mb-2 flex items-center gap-2">
                      <Activity className="w-4 h-4" />
                      详细状态
                    </h4>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>运行时长: 2小时35分钟</div>
                      <div>交易次数: 42</div>
                      <div>成功率: 78.5%</div>
                      <div>最大回撤: -2.3%</div>
                    </div>
                  </div>

                  <div className="border rounded-lg p-4 bg-muted/50">
                    <h4 className="font-medium mb-2">最近日志</h4>
                    <div className="space-y-1 text-sm text-muted-foreground max-h-32 overflow-y-auto">
                      {instance.logs.map((log, index) => (
                        <div key={index} className="font-mono">{log}</div>
                      ))}
                    </div>
                  </div>

                  <div className="border rounded-lg p-4 bg-muted/50">
                    <h4 className="font-medium mb-2">收益波浪图</h4>
                    <div className="h-20 flex items-end gap-1">
                      {Array.from({length: 20}, (_, i) => (
                        <div 
                          key={i}
                          className="bg-blue-500 w-2 rounded-t"
                          style={{height: `${Math.random() * 80 + 10}%`}}
                        />
                      ))}
                    </div>
                  </div>
                </CollapsibleContent>
              </Collapsible>
            </CardContent>
          </Card>
        ))}

        {/* Add New Instance Card */}
        <Card className="w-full border-dashed border-2 border-muted-foreground/25">
          <CardContent className="flex items-center justify-center p-8">
            <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
              <DialogTrigger asChild>
                <Button variant="ghost" className="h-auto flex-col gap-2">
                  <Plus className="w-8 h-8 text-muted-foreground" />
                  <span className="text-muted-foreground">添加新实例</span>
                </Button>
              </DialogTrigger>
              <DialogContent className="sm:max-w-md">
                <DialogHeader>
                  <DialogTitle>创建新交易实例</DialogTitle>
                  <DialogDescription>
                    选择平台、账号和策略来创建新的交易实例
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-4">
                  <div>
                    <label className="text-sm font-medium">交易平台</label>
                    <Select>
                      <SelectTrigger>
                        <SelectValue placeholder="选择交易平台" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="binance">币安</SelectItem>
                        <SelectItem value="huobi">火币</SelectItem>
                        <SelectItem value="okex">OKEx</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <label className="text-sm font-medium">账号</label>
                    <Select>
                      <SelectTrigger>
                        <SelectValue placeholder="选择账号" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="account1">账户A</SelectItem>
                        <SelectItem value="account2">账户B</SelectItem>
                        <SelectItem value="account3">账户C</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <label className="text-sm font-medium">交易策略</label>
                    <Select>
                      <SelectTrigger>
                        <SelectValue placeholder="选择策略" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="grid">网格策略</SelectItem>
                        <SelectItem value="arbitrage">套利策略</SelectItem>
                        <SelectItem value="trend">趋势跟踪</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => setShowCreateDialog(false)}>
                    取消
                  </Button>
                  <Button onClick={() => setShowCreateDialog(false)}>
                    创建实例
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}