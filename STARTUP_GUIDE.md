# 股票交易系统 - 完整启动指南

## 🎯 系统概览

这是一个完整的股票交易系统，包含以下组件：
- **后端API服务器** (Python FastAPI)
- **前端界面** (React + TypeScript + Vite)
- **WebSocket实时日志系统**
- **策略执行引擎**
- **多平台交易支持** (Binance、OKX、COINW等)

## 🚀 快速启动

### 一键启动（推荐）
```batch
start-trading.bat
```

这个脚本会：
1. ✅ 检查系统环境
2. ✅ 清理之前的进程
3. ✅ 启动API服务器
4. ✅ 启动前端界面
5. ✅ 提供管理选项

### 其他启动选项

#### 分别启动服务
```batch
# 启动API服务器
start-api-stable.bat

# 启动前端（在另一个终端）
cd apps\ui
npm run dev
```

#### 手动启动
```batch
# API服务器
apps\api\venv\Scripts\python.exe apps\api\main.py

# 前端服务器
cd apps\ui && npm run dev
```

## 🛠️ 管理工具

### 系统控制
- `start-trading.bat` - 完整系统启动
- `stop-trading.bat` - 优雅停止所有服务
- `health-check.bat` - 全面健康检查

### 服务器启动脚本
- `start-api-stable.bat` - 稳定版API启动
- `start-api-simple.bat` - 简化版API启动

## 📊 访问地址

### 主要服务
- **前端界面**: http://localhost:3001
- **API服务器**: http://localhost:8001
- **API文档**: http://localhost:8001/docs

### 监控工具
- **WebSocket测试**: http://localhost:8001/websocket-test.html
- **系统状态**: http://localhost:8001/api/logs/websocket/status
- **健康检查**: http://localhost:8001/api/health

## 🔧 故障排除

### 常见问题

#### 1. 端口被占用
```batch
# 检查端口占用
netstat -ano | findstr :8001
netstat -ano | findstr :3001

# 清理进程
taskkill /f /im python.exe
taskkill /f /im node.exe
```

#### 2. WebSocket连接问题
```batch
# 检查WebSocket状态
powershell -Command "Invoke-RestMethod -Uri 'http://localhost:8001/api/logs/websocket/status'"

# 清理WebSocket连接
powershell -Command "Invoke-RestMethod -Uri 'http://localhost:8001/api/logs/websocket/cleanup' -Method POST"
```

#### 3. 前端依赖问题
```batch
cd apps\ui
npm install
```

#### 4. Python环境问题
```batch
# 重新创建虚拟环境
python -m venv apps\api\venv
apps\api\venv\Scripts\pip install -r apps\api\requirements.txt
```

### 日志查看
- **运行日志**: `logs\runtime.log`
- **交易日志**: `logs\trade.log`
- **错误日志**: `logs\error.log`

## 📋 系统检查清单

运行 `health-check.bat` 会检查：
- ✅ API服务器状态
- ✅ 前端服务器状态  
- ✅ WebSocket连接状态
- ✅ 端口占用情况
- ✅ 进程运行状态
- ✅ 策略实例状态
- ✅ 日志系统状态
- ✅ 系统资源使用
- ✅ 配置文件安全

## 🔒 安全设置

### 自动交易保护
系统默认配置了多重安全保护：
- 需要手动启动策略
- 自动交易功能需要明确启用
- 风险控制参数限制
- 紧急停止机制

### 配置文件检查
健康检查会验证：
- `autoTrade` 设置
- `require_manual_start` 配置
- 风险控制参数

## 📈 性能监控

### WebSocket连接监控
- 最大连接数: 50
- 心跳间隔: 60秒
- 自动清理: 每5分钟
- 连接质量检查

### 系统资源
- CPU使用监控
- 内存使用检查
- 日志文件大小
- 进程状态跟踪

## 🎛️ 高级功能

### API接口
- REST API文档: `/docs`
- WebSocket日志: `/ws/logs`
- 健康检查: `/api/health`
- 状态监控: `/api/logs/websocket/status`

### 开发工具
- 热重载前端开发
- 实时日志监控
- WebSocket连接测试
- API调试界面

## 💡 最佳实践

### 日常使用
1. 使用 `start-trading.bat` 启动系统
2. 定期运行 `health-check.bat` 检查状态
3. 监控日志文件大小
4. 及时处理异常连接

### 维护建议
1. 定期清理日志文件
2. 监控系统资源使用
3. 更新依赖包版本
4. 备份重要配置文件

### 安全建议
1. 定期检查配置文件
2. 监控自动交易设置
3. 启用风险控制参数
4. 使用手动启动模式

---

## 🎉 现在开始

推荐使用以下命令开始：

```batch
start-trading.bat
```

系统启动后，选择 `[1] 打开交易系统前端` 即可开始使用！