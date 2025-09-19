import { useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./components/ui/tabs";
import { CurrentRunning } from "./components/CurrentRunning";
import { ConsoleTools } from "./components/ConsoleTools";
import { LogsPanel } from "./components/LogsPanel";
import { StrategyPanel } from "./components/StrategyPanel";
import { AccountPanel } from "./components/AccountPanel";
import { PlatformConfig } from "./components/PlatformConfig";
import { GlobalSettings } from "./components/GlobalSettings";
import { Play, Terminal, FileText, Zap, User, Settings, Globe } from "lucide-react";

export default function App() {
  const [activeTab, setActiveTab] = useState("current-running");

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto p-4">
        <div className="mb-6">
          <h1 className="text-2xl font-semibold mb-2">智能交易系统</h1>
          <p className="text-muted-foreground">专业算法交易管理平台</p>
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-7 h-12">
            <TabsTrigger value="current-running" className="flex items-center gap-2">
              <Play className="w-4 h-4" />
              当前运行
            </TabsTrigger>
            <TabsTrigger value="console-tools" className="flex items-center gap-2">
              <Terminal className="w-4 h-4" />
              控制台工具
            </TabsTrigger>
            <TabsTrigger value="logs" className="flex items-center gap-2">
              <FileText className="w-4 h-4" />
              日志
            </TabsTrigger>
            <TabsTrigger value="strategy" className="flex items-center gap-2">
              <Zap className="w-4 h-4" />
              策略
            </TabsTrigger>
            <TabsTrigger value="account" className="flex items-center gap-2">
              <User className="w-4 h-4" />
              账号
            </TabsTrigger>
            <TabsTrigger value="platform-config" className="flex items-center gap-2">
              <Settings className="w-4 h-4" />
              平台配置
            </TabsTrigger>
            <TabsTrigger value="global-settings" className="flex items-center gap-2">
              <Globe className="w-4 h-4" />
              全局设置
            </TabsTrigger>
          </TabsList>

          <div className="mt-6">
            <TabsContent value="current-running" className="space-y-4">
              <CurrentRunning />
            </TabsContent>

            <TabsContent value="console-tools" className="space-y-4">
              <ConsoleTools />
            </TabsContent>

            <TabsContent value="logs" className="space-y-4">
              <LogsPanel />
            </TabsContent>

            <TabsContent value="strategy" className="space-y-4">
              <StrategyPanel />
            </TabsContent>

            <TabsContent value="account" className="space-y-4">
              <AccountPanel />
            </TabsContent>

            <TabsContent value="platform-config" className="space-y-4">
              <PlatformConfig />
            </TabsContent>

            <TabsContent value="global-settings" className="space-y-4">
              <GlobalSettings />
            </TabsContent>
          </div>
        </Tabs>
      </div>
    </div>
  );
}