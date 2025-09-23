import { useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./components/ui/tabs";
import { CurrentRunning } from "./components/CurrentRunning";
import { ConsoleTools } from "./components/ConsoleTools";
import { LogsPanel } from "./components/LogsPanel";
import { StrategyPanel } from "./components/StrategyPanel";
import { PlatformConfig } from "./components/PlatformConfig";
import { GlobalSettings } from "./components/GlobalSettings";
import { ToastProvider } from "./components/ui/toast";
import { Play, Terminal, FileText, Zap, Settings, Globe } from "lucide-react";

export default function App() {
  const [activeTab, setActiveTab] = useState("current-running");

  const tabList = ["current-running", "console-tools", "logs", "strategy", "platform-config", "global-settings"];
  const isMobile = typeof window !== 'undefined' && window.innerWidth < 768;
  const tabCount = isMobile ? 3 : 6;
  const activeIndex = tabList.indexOf(activeTab);
  
  // 计算手机端多行布局的位置
  const mobileRowCount = 2; // 手机端分为2行
  const mobileColCount = 3; // 每行3个标签
  const currentRow = Math.floor(activeIndex / mobileColCount);
  const currentCol = activeIndex % mobileColCount;
  
  // 指示器位置计算
  const indicatorStyle = isMobile 
    ? {
        width: `calc(${100 / mobileColCount}% - 4px)`,
        left: `calc(${(currentCol * 100) / mobileColCount}% + 2px)`,
        top: `calc(${currentRow * 50}% + 2px)`, // 每行占50%高度
        height: `calc(50% - 4px)` // 高度为一行的高度减去边距
      }
    : {
        width: `calc(${100 / tabCount}% - 4px)`,
        left: `calc(${(activeIndex * 100) / tabCount}% + 2px)`,
        top: '2px',
        height: 'calc(100% - 4px)'
      };

  return (
    <ToastProvider>
      <div className="min-h-screen bg-background">
        <div className="container mx-auto p-2 md:p-4">
          <div className="mb-4 md:mb-6">
            <h1 className="text-xl md:text-2xl font-semibold mb-2">智能交易系统</h1>
            <p className="text-sm md:text-base text-muted-foreground">专业算法交易管理平台</p>
          </div>

          <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
            <div className="sticky top-2 z-40 bg-background/95 backdrop-blur-md border rounded-lg shadow-sm p-2 mb-4 md:mb-6">
              <TabsList className="grid w-full grid-cols-3 md:grid-cols-6 h-auto relative overflow-hidden bg-muted/30 rounded-md">
                <div 
                  className="absolute bg-background rounded-sm shadow-sm transition-all duration-300 ease-out border"
                  style={indicatorStyle}
                />
                <TabsTrigger value="current-running" className="flex items-center gap-1 md:gap-2 text-xs md:text-sm p-2 md:p-3 relative z-10 transition-all duration-200 data-[state=active]:text-foreground data-[state=active]:bg-transparent">
                  <Play className="w-3 h-3 md:w-4 md:h-4" />
                  <span className="hidden sm:inline">当前运行</span>
                  <span className="sm:hidden">运行</span>
                </TabsTrigger>
                <TabsTrigger value="console-tools" className="flex items-center gap-1 md:gap-2 text-xs md:text-sm p-2 md:p-3 relative z-10 transition-all duration-200 data-[state=active]:text-foreground data-[state=active]:bg-transparent">
                  <Terminal className="w-3 h-3 md:w-4 md:h-4" />
                  <span className="hidden sm:inline">控制台工具</span>
                  <span className="sm:hidden">控制台</span>
                </TabsTrigger>
                <TabsTrigger value="logs" className="flex items-center gap-1 md:gap-2 text-xs md:text-sm p-2 md:p-3 relative z-10 transition-all duration-200 data-[state=active]:text-foreground data-[state=active]:bg-transparent">
                  <FileText className="w-3 h-3 md:w-4 md:h-4" />
                  日志
                </TabsTrigger>
                <TabsTrigger value="strategy" className="flex items-center gap-1 md:gap-2 text-xs md:text-sm p-2 md:p-3 relative z-10 transition-all duration-200 data-[state=active]:text-foreground data-[state=active]:bg-transparent">
                  <Zap className="w-3 h-3 md:w-4 md:h-4" />
                  策略
                </TabsTrigger>
                <TabsTrigger value="platform-config" className="flex items-center gap-1 md:gap-2 text-xs md:text-sm p-2 md:p-3 relative z-10 transition-all duration-200 data-[state=active]:text-foreground data-[state=active]:bg-transparent">
                  <Settings className="w-3 h-3 md:w-4 md:h-4" />
                  <span className="hidden sm:inline">平台配置</span>
                  <span className="sm:hidden">配置</span>
                </TabsTrigger>
                <TabsTrigger value="global-settings" className="flex items-center gap-1 md:gap-2 text-xs md:text-sm p-2 md:p-3 relative z-10 transition-all duration-200 data-[state=active]:text-foreground data-[state=active]:bg-transparent">
                  <Globe className="w-3 h-3 md:w-4 md:h-4" />
                  <span className="hidden sm:inline">全局设置</span>
                  <span className="sm:hidden">设置</span>
                </TabsTrigger>
              </TabsList>
            </div>

            <div className="transition-all duration-300 ease-out">
              <TabsContent value="current-running" className="space-y-4 data-[state=active]:animate-in data-[state=active]:fade-in-0 data-[state=active]:slide-in-from-bottom-2">
                <CurrentRunning />
              </TabsContent>

              <TabsContent value="console-tools" className="space-y-4 data-[state=active]:animate-in data-[state=active]:fade-in-0 data-[state=active]:slide-in-from-bottom-2">
                <ConsoleTools />
              </TabsContent>

              <TabsContent value="logs" className="space-y-4 data-[state=active]:animate-in data-[state=active]:fade-in-0 data-[state=active]:slide-in-from-bottom-2">
                <LogsPanel />
              </TabsContent>

              <TabsContent value="strategy" className="space-y-4 data-[state=active]:animate-in data-[state=active]:fade-in-0 data-[state=active]:slide-in-from-bottom-2">
                <StrategyPanel />
              </TabsContent>

              <TabsContent value="platform-config" className="space-y-4 data-[state=active]:animate-in data-[state=active]:fade-in-0 data-[state=active]:slide-in-from-bottom-2">
                <PlatformConfig />
              </TabsContent>

              <TabsContent value="global-settings" className="space-y-4 data-[state=active]:animate-in data-[state=active]:fade-in-0 data-[state=active]:slide-in-from-bottom-2">
                <GlobalSettings />
              </TabsContent>
            </div>
          </Tabs>
        </div>
      </div>
    </ToastProvider>
  );
}