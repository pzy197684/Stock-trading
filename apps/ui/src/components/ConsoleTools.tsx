import { useState, useRef, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "./ui/dialog";
import { ScrollArea } from "./ui/scroll-area";
import { Terminal, Calculator, Database, BarChart3, Send } from "lucide-react";

export function ConsoleTools() {
  const [consoleOutput, setConsoleOutput] = useState<string[]>([
    "智能交易系统控制台 v1.0.0",
    "输入 'help' 查看可用命令",
    ""
  ]);
  const [currentInput, setCurrentInput] = useState("");
  const [showCalculator, setShowCalculator] = useState(false);
  const [calculatorInput, setCalculatorInput] = useState("");
  const [calculatorResult, setCalculatorResult] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [consoleOutput]);

  const executeCommand = (command: string) => {
    const newOutput = [...consoleOutput, `> ${command}`];
    
    const cmd = command.toLowerCase().trim();
    
    // 尝试从API获取系统信息
    if (cmd === 'status') {
      fetch('http://localhost:8001/health')
        .then(response => response.json())
        .then(data => {
          const apiOutput = [
            ...newOutput,
            `系统状态: ${data.status}`,
            `API时间: ${data.timestamp}`,
            `缺失功能数: ${data.missing_features}`
          ];
          setConsoleOutput(apiOutput);
        })
        .catch(() => {
          setConsoleOutput([...newOutput, "系统状态: API连接失败", "活跃实例: 无法获取", "总盈亏: 无法获取"]);
        });
      return;
    }
    
    if (cmd === 'accounts') {
      fetch('http://localhost:8001/api/dashboard/summary')
        .then(response => response.json())
        .then(data => {
          const apiOutput = [
            ...newOutput,
            "账户列表:",
            ...data.accounts.map((account: any, index: number) => 
              `  ${index + 1}. ${account.platform}-${account.id} (${account.status})`
            )
          ];
          setConsoleOutput(apiOutput);
        })
        .catch(() => {
          setConsoleOutput([...newOutput, "账户列表:", "  API连接失败，无法获取账户信息"]);
        });
      return;
    }
    
    if (cmd === 'strategies') {
      fetch('http://localhost:8001/api/strategies/available')
        .then(response => response.json())
        .then(data => {
          const apiOutput = [
            ...newOutput,
            "可用策略:",
            ...data.strategies.map((strategy: any) => 
              `  - ${strategy.name} (v${strategy.version})`
            )
          ];
          setConsoleOutput(apiOutput);
        })
        .catch(() => {
          setConsoleOutput([...newOutput, "可用策略:", "  API连接失败，无法获取策略信息"]);
        });
      return;
    }
    
    // 原有的本地命令处理逻辑
    if (cmd === 'help') {
      newOutput.push("可用命令:");
      newOutput.push("  help           - 显示此帮助信息");
      newOutput.push("  status         - 显示系统状态");
      newOutput.push("  accounts       - 列出所有账户");
      newOutput.push("  strategies     - 列出所有策略");
      newOutput.push("  start <id>     - 启动指定实例");
      newOutput.push("  stop <id>      - 停止指定实例");
      newOutput.push("  clear          - 清空控制台");
    } else if (cmd === 'status') {
      newOutput.push("系统状态: 运行中");
      newOutput.push("活跃实例: 3");
      newOutput.push("总盈亏: +929.7 USDT");
      newOutput.push("系统负载: 23%");
    } else if (cmd === 'accounts') {
      newOutput.push("账户列表:");
      newOutput.push("  1. 币安-账户A (运行中)");
      newOutput.push("  2. 火币-账户B (运行中)");
      newOutput.push("  3. OKEx-账户C (错误)");
    } else if (cmd === 'strategies') {
      newOutput.push("策略列表:");
      newOutput.push("  1. 网格策略 - 适用于震荡行情");
      newOutput.push("  2. 套利策略 - 跨平台价差套利");
      newOutput.push("  3. 趋势跟踪 - 追踪市场趋势");
    } else if (cmd === 'clear') {
      setConsoleOutput(["控制台已清空", ""]);
      return;
    } else if (cmd.startsWith('start ')) {
      const id = cmd.split(' ')[1];
      newOutput.push(`正在启动实例 ${id}...`);
      newOutput.push(`实例 ${id} 启动成功`);
    } else if (cmd.startsWith('stop ')) {
      const id = cmd.split(' ')[1];
      newOutput.push(`正在停止实例 ${id}...`);
      newOutput.push(`实例 ${id} 已停止`);
    } else if (cmd === '') {
      // 空命令，不做处理
    } else {
      newOutput.push(`未知命令: ${command}`);
      newOutput.push("输入 'help' 查看可用命令");
    }
    
    newOutput.push("");
    setConsoleOutput(newOutput);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      executeCommand(currentInput);
      setCurrentInput("");
    }
  };

  const calculate = (expression: string) => {
    try {
      // 基础的安全计算器
      const sanitized = expression.replace(/[^0-9+\-*/().\s]/g, '');
      const result = Function(`"use strict"; return (${sanitized})`)();
      setCalculatorResult(result.toString());
    } catch {
      setCalculatorResult("错误");
    }
  };

  const handleCalculatorKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      calculate(calculatorInput);
    }
  };

  return (
    <div className="space-y-6">
      {/* Console */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Terminal className="w-5 h-5" />
            控制台
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="bg-black text-green-400 p-4 rounded-lg font-mono text-sm">
            <ScrollArea className="h-80" ref={scrollRef}>
              {consoleOutput.map((line, index) => (
                <div key={index} className="min-h-[1.2em]">
                  {line}
                </div>
              ))}
            </ScrollArea>
            <div className="flex items-center mt-2 pt-2 border-t border-green-400/20">
              <span className="text-green-400 mr-2">$</span>
              <Input
                value={currentInput}
                onChange={(e) => setCurrentInput(e.target.value)}
                onKeyPress={handleKeyPress}
                className="bg-transparent border-none text-green-400 p-0 h-auto focus-visible:ring-0 focus-visible:ring-offset-0"
                placeholder="输入命令..."
              />
              <Button
                size="sm"
                variant="ghost"
                onClick={() => executeCommand(currentInput)}
                className="ml-2 h-6 w-6 p-0 text-green-400 hover:bg-green-400/10"
              >
                <Send className="w-3 h-3" />
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Tool Buttons */}
      <Card>
        <CardHeader>
          <CardTitle>快捷工具</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4">
            {/* Calculator */}
            <Dialog open={showCalculator} onOpenChange={setShowCalculator}>
              <DialogTrigger asChild>
                <Button variant="outline" className="h-20 flex-col gap-2">
                  <Calculator className="w-8 h-8" />
                  计算器
                </Button>
              </DialogTrigger>
              <DialogContent className="sm:max-w-md">
                <DialogHeader>
                  <DialogTitle>计算器</DialogTitle>
                </DialogHeader>
                <div className="space-y-4">
                  <div>
                    <Input
                      value={calculatorInput}
                      onChange={(e) => setCalculatorInput(e.target.value)}
                      onKeyPress={handleCalculatorKeyPress}
                      placeholder="输入计算表达式..."
                      className="text-right"
                    />
                  </div>
                  <div className="text-right">
                    <span className="text-sm text-muted-foreground">结果: </span>
                    <span className="text-lg font-mono">{calculatorResult}</span>
                  </div>
                  <div className="grid grid-cols-4 gap-2">
                    {['7', '8', '9', '/'].map(btn => (
                      <Button key={btn} variant="outline" onClick={() => setCalculatorInput(prev => prev + btn)}>
                        {btn}
                      </Button>
                    ))}
                    {['4', '5', '6', '*'].map(btn => (
                      <Button key={btn} variant="outline" onClick={() => setCalculatorInput(prev => prev + btn)}>
                        {btn}
                      </Button>
                    ))}
                    {['1', '2', '3', '-'].map(btn => (
                      <Button key={btn} variant="outline" onClick={() => setCalculatorInput(prev => prev + btn)}>
                        {btn}
                      </Button>
                    ))}
                    {['0', '.', '=', '+'].map(btn => (
                      <Button 
                        key={btn} 
                        variant={btn === '=' ? "default" : "outline"} 
                        onClick={() => {
                          if (btn === '=') {
                            calculate(calculatorInput);
                          } else {
                            setCalculatorInput(prev => prev + btn);
                          }
                        }}
                      >
                        {btn}
                      </Button>
                    ))}
                  </div>
                  <div className="flex gap-2">
                    <Button variant="outline" onClick={() => setCalculatorInput("")} className="flex-1">
                      清空
                    </Button>
                    <Button variant="outline" onClick={() => setCalculatorInput(prev => prev.slice(0, -1))} className="flex-1">
                      退格
                    </Button>
                  </div>
                </div>
              </DialogContent>
            </Dialog>

            {/* Database Tool */}
            <Button variant="outline" className="h-20 flex-col gap-2">
              <Database className="w-8 h-8" />
              数据库工具
            </Button>

            {/* Performance Monitor */}
            <Button variant="outline" className="h-20 flex-col gap-2">
              <BarChart3 className="w-8 h-8" />
              性能监控
            </Button>

            {/* Network Test */}
            <Button variant="outline" className="h-20 flex-col gap-2">
              <Terminal className="w-8 h-8" />
              网络测试
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}