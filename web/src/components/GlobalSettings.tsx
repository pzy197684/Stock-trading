import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select";
import { Switch } from "./ui/switch";
import { Slider } from "./ui/slider";
import { Separator } from "./ui/separator";
import { Badge } from "./ui/badge";
import { Textarea } from "./ui/textarea";
import { Settings, Bell, Palette, Shield, Database, Monitor, Globe2, Download } from "lucide-react";

interface GlobalSettings {
  appearance: {
    theme: 'light' | 'dark' | 'system';
    language: string;
    timezone: string;
    fontSize: number;
  };
  notifications: {
    enableDesktop: boolean;
    enableEmail: boolean;
    enableSound: boolean;
    tradingAlerts: boolean;
    systemAlerts: boolean;
    profitLossAlerts: boolean;
    emailAddress: string;
    soundVolume: number;
  };
  security: {
    enableTwoFactor: boolean;
    sessionTimeout: number;
    enableEncryption: boolean;
    logLevel: string;
    autoLogout: boolean;
  };
  performance: {
    maxConcurrentConnections: number;
    cacheTimeout: number;
    enableCompression: boolean;
    optimizeMemory: boolean;
  };
  backup: {
    autoBackup: boolean;
    backupInterval: number;
    backupLocation: string;
    keepBackups: number;
  };
}

export function GlobalSettings() {
  const [settings, setSettings] = useState<GlobalSettings>({
    appearance: {
      theme: 'system',
      language: 'zh-CN',
      timezone: 'Asia/Shanghai',
      fontSize: 14
    },
    notifications: {
      enableDesktop: true,
      enableEmail: false,
      enableSound: true,
      tradingAlerts: true,
      systemAlerts: true,
      profitLossAlerts: true,
      emailAddress: '',
      soundVolume: 70
    },
    security: {
      enableTwoFactor: false,
      sessionTimeout: 30,
      enableEncryption: true,
      logLevel: 'info',
      autoLogout: true
    },
    performance: {
      maxConcurrentConnections: 50,
      cacheTimeout: 300,
      enableCompression: true,
      optimizeMemory: true
    },
    backup: {
      autoBackup: true,
      backupInterval: 24,
      backupLocation: './backups',
      keepBackups: 7
    }
  });

  const updateSetting = (category: keyof GlobalSettings, key: string, value: any) => {
    setSettings(prev => ({
      ...prev,
      [category]: {
        ...prev[category],
        [key]: value
      }
    }));
  };

  const exportSettings = () => {
    const settingsJson = JSON.stringify(settings, null, 2);
    const blob = new Blob([settingsJson], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `trading_settings_${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-medium">全局设置</h2>
          <p className="text-sm text-muted-foreground">系统级别的配置和偏好设置</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={exportSettings}>
            <Download className="w-4 h-4 mr-2" />
            导出设置
          </Button>
          <Button>保存所有设置</Button>
        </div>
      </div>

      {/* Appearance Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Palette className="w-5 h-5" />
            外观设置
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid grid-cols-2 gap-6">
            <div className="space-y-2">
              <Label>主题</Label>
              <Select
                value={settings.appearance.theme}
                onValueChange={(value) => updateSetting('appearance', 'theme', value)}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="light">浅色</SelectItem>
                  <SelectItem value="dark">深色</SelectItem>
                  <SelectItem value="system">跟随系统</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>语言</Label>
              <Select
                value={settings.appearance.language}
                onValueChange={(value) => updateSetting('appearance', 'language', value)}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="zh-CN">简体中文</SelectItem>
                  <SelectItem value="zh-TW">繁體中文</SelectItem>
                  <SelectItem value="en-US">English</SelectItem>
                  <SelectItem value="ja-JP">日本語</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>时区</Label>
              <Select
                value={settings.appearance.timezone}
                onValueChange={(value) => updateSetting('appearance', 'timezone', value)}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="Asia/Shanghai">北京时间 (UTC+8)</SelectItem>
                  <SelectItem value="America/New_York">纽约时间 (UTC-5)</SelectItem>
                  <SelectItem value="Europe/London">伦敦时间 (UTC+0)</SelectItem>
                  <SelectItem value="Asia/Tokyo">东京时间 (UTC+9)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>字体大小</Label>
              <div className="px-3">
                <Slider
                  value={[settings.appearance.fontSize]}
                  onValueChange={(value) => updateSetting('appearance', 'fontSize', value[0])}
                  min={12}
                  max={20}
                  step={1}
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-muted-foreground mt-1">
                  <span>12px</span>
                  <span>{settings.appearance.fontSize}px</span>
                  <span>20px</span>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Notification Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Bell className="w-5 h-5" />
            通知设置
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <Label>桌面通知</Label>
                <p className="text-sm text-muted-foreground">在桌面显示系统通知</p>
              </div>
              <Switch
                checked={settings.notifications.enableDesktop}
                onCheckedChange={(checked) => updateSetting('notifications', 'enableDesktop', checked)}
              />
            </div>

            <div className="flex items-center justify-between">
              <div>
                <Label>邮件通知</Label>
                <p className="text-sm text-muted-foreground">发送重要通知到邮箱</p>
              </div>
              <Switch
                checked={settings.notifications.enableEmail}
                onCheckedChange={(checked) => updateSetting('notifications', 'enableEmail', checked)}
              />
            </div>

            {settings.notifications.enableEmail && (
              <div className="space-y-2 ml-6">
                <Label>邮箱地址</Label>
                <Input
                  type="email"
                  value={settings.notifications.emailAddress}
                  onChange={(e) => updateSetting('notifications', 'emailAddress', e.target.value)}
                  placeholder="your@email.com"
                />
              </div>
            )}

            <div className="flex items-center justify-between">
              <div>
                <Label>声音提醒</Label>
                <p className="text-sm text-muted-foreground">播放提示音</p>
              </div>
              <Switch
                checked={settings.notifications.enableSound}
                onCheckedChange={(checked) => updateSetting('notifications', 'enableSound', checked)}
              />
            </div>

            {settings.notifications.enableSound && (
              <div className="space-y-2 ml-6">
                <Label>音量</Label>
                <div className="px-3">
                  <Slider
                    value={[settings.notifications.soundVolume]}
                    onValueChange={(value) => updateSetting('notifications', 'soundVolume', value[0])}
                    max={100}
                    step={5}
                    className="w-full"
                  />
                  <div className="flex justify-between text-xs text-muted-foreground mt-1">
                    <span>0%</span>
                    <span>{settings.notifications.soundVolume}%</span>
                    <span>100%</span>
                  </div>
                </div>
              </div>
            )}
          </div>

          <Separator />

          <div className="space-y-4">
            <h4 className="font-medium">通知类型</h4>
            
            <div className="flex items-center justify-between">
              <div>
                <Label>交易提醒</Label>
                <p className="text-sm text-muted-foreground">订单执行、成交等交易相关通知</p>
              </div>
              <Switch
                checked={settings.notifications.tradingAlerts}
                onCheckedChange={(checked) => updateSetting('notifications', 'tradingAlerts', checked)}
              />
            </div>

            <div className="flex items-center justify-between">
              <div>
                <Label>系统提醒</Label>
                <p className="text-sm text-muted-foreground">连接状态、错误等系统通知</p>
              </div>
              <Switch
                checked={settings.notifications.systemAlerts}
                onCheckedChange={(checked) => updateSetting('notifications', 'systemAlerts', checked)}
              />
            </div>

            <div className="flex items-center justify-between">
              <div>
                <Label>盈亏提醒</Label>
                <p className="text-sm text-muted-foreground">达到盈亏阈值时的通知</p>
              </div>
              <Switch
                checked={settings.notifications.profitLossAlerts}
                onCheckedChange={(checked) => updateSetting('notifications', 'profitLossAlerts', checked)}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Security Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="w-5 h-5" />
            安全设置
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid grid-cols-2 gap-6">
            <div className="space-y-2">
              <Label>会话超时 (分钟)</Label>
              <Input
                type="number"
                value={settings.security.sessionTimeout}
                onChange={(e) => updateSetting('security', 'sessionTimeout', parseInt(e.target.value))}
                min="5"
                max="480"
              />
            </div>

            <div className="space-y-2">
              <Label>日志级别</Label>
              <Select
                value={settings.security.logLevel}
                onValueChange={(value) => updateSetting('security', 'logLevel', value)}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="debug">调试</SelectItem>
                  <SelectItem value="info">信息</SelectItem>
                  <SelectItem value="warning">警告</SelectItem>
                  <SelectItem value="error">错误</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <Label>两步验证</Label>
                <p className="text-sm text-muted-foreground">增强账户安全性</p>
              </div>
              <Switch
                checked={settings.security.enableTwoFactor}
                onCheckedChange={(checked) => updateSetting('security', 'enableTwoFactor', checked)}
              />
            </div>

            <div className="flex items-center justify-between">
              <div>
                <Label>数据加密</Label>
                <p className="text-sm text-muted-foreground">加密存储敏感数据</p>
              </div>
              <Switch
                checked={settings.security.enableEncryption}
                onCheckedChange={(checked) => updateSetting('security', 'enableEncryption', checked)}
              />
            </div>

            <div className="flex items-center justify-between">
              <div>
                <Label>自动登出</Label>
                <p className="text-sm text-muted-foreground">长时间无操作自动登出</p>
              </div>
              <Switch
                checked={settings.security.autoLogout}
                onCheckedChange={(checked) => updateSetting('security', 'autoLogout', checked)}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Performance Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Monitor className="w-5 h-5" />
            性能设置
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid grid-cols-2 gap-6">
            <div className="space-y-2">
              <Label>最大并发连接数</Label>
              <Input
                type="number"
                value={settings.performance.maxConcurrentConnections}
                onChange={(e) => updateSetting('performance', 'maxConcurrentConnections', parseInt(e.target.value))}
                min="10"
                max="200"
              />
            </div>

            <div className="space-y-2">
              <Label>缓存超时 (秒)</Label>
              <Input
                type="number"
                value={settings.performance.cacheTimeout}
                onChange={(e) => updateSetting('performance', 'cacheTimeout', parseInt(e.target.value))}
                min="60"
                max="3600"
              />
            </div>
          </div>

          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <Label>数据压缩</Label>
                <p className="text-sm text-muted-foreground">压缩网络传输数据</p>
              </div>
              <Switch
                checked={settings.performance.enableCompression}
                onCheckedChange={(checked) => updateSetting('performance', 'enableCompression', checked)}
              />
            </div>

            <div className="flex items-center justify-between">
              <div>
                <Label>内存优化</Label>
                <p className="text-sm text-muted-foreground">优化内存使用</p>
              </div>
              <Switch
                checked={settings.performance.optimizeMemory}
                onCheckedChange={(checked) => updateSetting('performance', 'optimizeMemory', checked)}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Backup Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Database className="w-5 h-5" />
            备份设置
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <Label>自动备份</Label>
              <p className="text-sm text-muted-foreground">定期备份重要数据</p>
            </div>
            <Switch
              checked={settings.backup.autoBackup}
              onCheckedChange={(checked) => updateSetting('backup', 'autoBackup', checked)}
            />
          </div>

          {settings.backup.autoBackup && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-6">
                <div className="space-y-2">
                  <Label>备份间隔 (小时)</Label>
                  <Select
                    value={settings.backup.backupInterval.toString()}
                    onValueChange={(value) => updateSetting('backup', 'backupInterval', parseInt(value))}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="1">1小时</SelectItem>
                      <SelectItem value="6">6小时</SelectItem>
                      <SelectItem value="12">12小时</SelectItem>
                      <SelectItem value="24">24小时</SelectItem>
                      <SelectItem value="168">1周</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label>保留备份数量</Label>
                  <Input
                    type="number"
                    value={settings.backup.keepBackups}
                    onChange={(e) => updateSetting('backup', 'keepBackups', parseInt(e.target.value))}
                    min="1"
                    max="30"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label>备份位置</Label>
                <Input
                  value={settings.backup.backupLocation}
                  onChange={(e) => updateSetting('backup', 'backupLocation', e.target.value)}
                  placeholder="./backups"
                />
              </div>
            </div>
          )}

          <div className="flex gap-2">
            <Button variant="outline">立即备份</Button>
            <Button variant="outline">恢复备份</Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}