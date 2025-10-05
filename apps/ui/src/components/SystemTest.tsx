import { useState } from 'react';
import { Button } from "./ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";
import { useToast } from "./ui/toast";
import { CheckCircle, XCircle, AlertCircle, RefreshCw, Wifi, WifiOff, Activity } from 'lucide-react';
import apiService from "../services/apiService";

interface TestResult {
  name: string;
  status: 'pending' | 'running' | 'success' | 'error';
  message?: string;
  details?: any;
  timestamp?: string;
}

export function SystemTest() {
  const { toast } = useToast();
  const [tests, setTests] = useState<TestResult[]>([
    { name: '重复实例错误中文化', status: 'pending' },
    { name: 'autoTrade参数持久化', status: 'pending' },
    { name: 'WebSocket日志连接', status: 'pending' },
    { name: '交易连接测试', status: 'pending' },
    { name: 'Webhook通知功能', status: 'pending' },
  ]);
  const [isRunning, setIsRunning] = useState(false);
  const [wsConnected, setWsConnected] = useState(false);

  const updateTestResult = (testName: string, result: Partial<TestResult>) => {
    setTests(prev => prev.map(test => 
      test.name === testName 
        ? { ...test, ...result, timestamp: new Date().toISOString() }
        : test
    ));
  };

  // 测试1：重复实例错误中文化
  const testDuplicateInstance = async () => {
    updateTestResult('重复实例错误中文化', { status: 'running' });
    
    try {
      // 先创建一个实例
      const createResult = await apiService.createInstance({
        account_id: 'BN1602',
        platform: 'BINANCE',
        strategy: 'martingale_hedge',
        symbol: 'OPUSDT'
      });

      if (createResult.success) {
        // 尝试创建重复实例
        const duplicateResult = await apiService.createInstance({
          account_id: 'BN1602', 
          platform: 'BINANCE',
          strategy: 'martingale_hedge',
          symbol: 'OPUSDT'
        });

        if (!duplicateResult.success && duplicateResult.error) {
          // 检查错误信息是否包含中文
          const errorStr = JSON.stringify(duplicateResult.error);
          const hasChinese = /[\u4e00-\u9fa5]/.test(errorStr);
          
          if (hasChinese && errorStr.includes('相同的交易对不允许再建实例')) {
            updateTestResult('重复实例错误中文化', { 
              status: 'success', 
              message: '✅ 错误信息已正确中文化' 
            });
          } else {
            updateTestResult('重复实例错误中文化', { 
              status: 'error', 
              message: '❌ 错误信息未中文化或格式不正确',
              details: duplicateResult.error
            });
          }
        } else {
          updateTestResult('重复实例错误中文化', { 
            status: 'error', 
            message: '❌ 未收到预期的重复实例错误' 
          });
        }
      } else {
        updateTestResult('重复实例错误中文化', { 
          status: 'error', 
          message: '❌ 初始实例创建失败' 
        });
      }
    } catch (error) {
      updateTestResult('重复实例错误中文化', { 
        status: 'error', 
        message: `❌ 测试异常: ${error}` 
      });
    }
  };

  // 测试2：autoTrade参数持久化
  const testAutoTradePersistence = async () => {
    updateTestResult('autoTrade参数持久化', { status: 'running' });
    
    try {
      // 设置autoTrade为true
      const updateResult = await apiService.updateInstanceParameters('BN1602', {
        autoTrade: true,
        long: { first_qty: 0.01 },
        short: { first_qty: 0.01 },
        hedge: { trigger_loss: 0.05 }
      });

      if (updateResult.success) {
        // 等待一秒然后读取参数
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        const getResult = await apiService.getInstanceParameters('BN1602');
        
        if (getResult.success && getResult.data?.raw_parameters?.autoTrade === true) {
          updateTestResult('autoTrade参数持久化', { 
            status: 'success', 
            message: '✅ autoTrade参数已正确保存' 
          });
        } else {
          updateTestResult('autoTrade参数持久化', { 
            status: 'error', 
            message: '❌ autoTrade参数未正确保存',
            details: getResult.data
          });
        }
      } else {
        updateTestResult('autoTrade参数持久化', { 
          status: 'error', 
          message: '❌ 参数更新失败' 
        });
      }
    } catch (error) {
      updateTestResult('autoTrade参数持久化', { 
        status: 'error', 
        message: `❌ 测试异常: ${error}` 
      });
    }
  };

  // 测试3：WebSocket日志连接
  const testWebSocketLog = async () => {
    updateTestResult('WebSocket日志连接', { status: 'running' });
    
    try {
      // 创建WebSocket连接
      const ws = new WebSocket('ws://localhost:8001/ws/logs');
      
      const timeout = setTimeout(() => {
        ws.close();
        updateTestResult('WebSocket日志连接', { 
          status: 'error', 
          message: '❌ WebSocket连接超时' 
        });
      }, 5000);

      ws.onopen = () => {
        clearTimeout(timeout);
        setWsConnected(true);
        updateTestResult('WebSocket日志连接', { 
          status: 'success', 
          message: '✅ WebSocket连接成功' 
        });
        
        // 触发日志测试
        apiService.testLogs();
        
        setTimeout(() => {
          ws.close();
          setWsConnected(false);
        }, 2000);
      };

      ws.onerror = () => {
        clearTimeout(timeout);
        updateTestResult('WebSocket日志连接', { 
          status: 'error', 
          message: '❌ WebSocket连接失败' 
        });
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'log') {
            updateTestResult('WebSocket日志连接', { 
              status: 'success', 
              message: '✅ 收到日志消息，连接正常',
              details: data.data
            });
          }
        } catch (e) {
          // 忽略解析错误
        }
      };
    } catch (error) {
      updateTestResult('WebSocket日志连接', { 
        status: 'error', 
        message: `❌ 测试异常: ${error}` 
      });
    }
  };

  // 测试4：交易连接测试
  const testTradingConnection = async () => {
    updateTestResult('交易连接测试', { status: 'running' });
    
    try {
      const result = await apiService.testConnection({
        platform: 'BINANCE',
        account_id: 'BN1602'
      });

      if (result.success) {
        updateTestResult('交易连接测试', { 
          status: 'success', 
          message: '✅ 交易连接测试成功',
          details: result.data
        });
      } else {
        // 检查错误信息是否包含中文提示和故障排除建议
        const errorMsg = result.error || result.message || '未知错误';
        const hasTroubleshooting = result.data?.troubleshooting;
        
        if (hasTroubleshooting) {
          updateTestResult('交易连接测试', { 
            status: 'success', 
            message: '✅ 连接失败但错误处理完善（包含故障排除建议）',
            details: result
          });
        } else {
          updateTestResult('交易连接测试', { 
            status: 'error', 
            message: '❌ 连接失败且错误处理不完善',
            details: result
          });
        }
      }
    } catch (error) {
      updateTestResult('交易连接测试', { 
        status: 'error', 
        message: `❌ 测试异常: ${error}` 
      });
    }
  };

  // 测试5：Webhook通知功能
  const testWebhookNotification = async () => {
    updateTestResult('Webhook通知功能', { status: 'running' });
    
    try {
      const result = await fetch('http://localhost:8001/api/webhook/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      
      const data = await result.json();
      
      if (data.success) {
        updateTestResult('Webhook通知功能', { 
          status: 'success', 
          message: '✅ Webhook通知功能测试成功',
          details: data.test_data
        });
      } else {
        updateTestResult('Webhook通知功能', { 
          status: 'error', 
          message: '❌ Webhook通知功能测试失败',
          details: data
        });
      }
    } catch (error) {
      updateTestResult('Webhook通知功能', { 
        status: 'error', 
        message: `❌ 测试异常: ${error}` 
      });
    }
  };

  const runAllTests = async () => {
    setIsRunning(true);
    
    // 重置所有测试状态
    setTests(prev => prev.map(test => ({ ...test, status: 'pending' as const })));
    
    try {
      await testDuplicateInstance();
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      await testAutoTradePersistence();
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      await testWebSocketLog();
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      await testTradingConnection();
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      await testWebhookNotification();
      
      toast({
        title: "系统测试完成",
        description: "所有测试项目已执行完毕",
        type: "success"
      });
    } catch (error) {
      toast({
        title: "测试执行失败",
        description: `测试过程中发生错误: ${error}`,
        type: "error"
      });
    } finally {
      setIsRunning(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'error':
        return <XCircle className="w-5 h-5 text-red-500" />;
      case 'running':
        return <RefreshCw className="w-5 h-5 text-blue-500 animate-spin" />;
      default:
        return <AlertCircle className="w-5 h-5 text-gray-400" />;
    }
  };

  const getStatusBadge = (status: string) => {
    const variants = {
      pending: 'secondary',
      running: 'default',
      success: 'success',
      error: 'destructive'
    } as const;
    
    return <Badge variant={variants[status as keyof typeof variants] || 'secondary'}>{status}</Badge>;
  };

  return (
    <Card className="w-full max-w-4xl mx-auto">
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>系统功能测试</span>
          <div className="flex items-center gap-2">
            {wsConnected ? 
              <Wifi className="w-5 h-5 text-green-500" /> : 
              <WifiOff className="w-5 h-5 text-gray-400" />
            }
            <Button onClick={runAllTests} disabled={isRunning}>
              {isRunning ? (
                <>
                  <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                  测试中...
                </>
              ) : (
                <>
                  <Activity className="w-4 h-4 mr-2" />
                  运行所有测试
                </>
              )}
            </Button>
          </div>
        </CardTitle>
        <CardDescription>
          测试所有6个已修复的系统功能
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {tests.map((test, index) => (
          <div
            key={index}
            className="flex items-center justify-between p-4 border rounded-lg"
          >
            <div className="flex items-center gap-3">
              {getStatusIcon(test.status)}
              <div>
                <div className="font-medium">{test.name}</div>
                {test.message && (
                  <div className="text-sm text-muted-foreground">{test.message}</div>
                )}
                {test.timestamp && (
                  <div className="text-xs text-muted-foreground">
                    {(() => {
                      try {
                        const date = new Date(test.timestamp);
                        return isNaN(date.getTime()) ? '时间无效' : date.toLocaleTimeString();
                      } catch {
                        return '时间无效';
                      }
                    })()}
                  </div>
                )}
              </div>
            </div>
            <div className="flex items-center gap-2">
              {getStatusBadge(test.status)}
              {test.details && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    console.log(`${test.name} 详细信息:`, test.details);
                    toast({
                      title: `${test.name} 详细信息`,
                      description: "详细信息已输出到控制台",
                      type: "info"
                    });
                  }}
                >
                  详情
                </Button>
              )}
            </div>
          </div>
        ))}
        
        <div className="mt-6 p-4 bg-muted rounded-lg">
          <h4 className="font-medium mb-2">测试说明</h4>
          <ul className="text-sm text-muted-foreground space-y-1">
            <li>• <strong>重复实例错误中文化</strong>: 验证HTTP 400错误信息是否正确显示中文</li>
            <li>• <strong>autoTrade参数持久化</strong>: 验证自动交易模式设置是否能正确保存</li>
            <li>• <strong>WebSocket日志连接</strong>: 验证日志推送功能是否正常工作</li>
            <li>• <strong>交易连接测试</strong>: 验证交易平台连接和错误处理是否完善</li>
            <li>• <strong>Webhook通知功能</strong>: 验证Webhook通知开关是否有效</li>
          </ul>
        </div>
      </CardContent>
    </Card>
  );
}