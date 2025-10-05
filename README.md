# 股票交易系统 (Stock Trading System)

## 快速启动

只需要运行一个文件即可启动整个系统：

```cmd
start-trading.bat
```

## 系统结构

```
Stock-trading/
├── apps/                   # 应用程序
│   ├── api/               # 后端API服务
│   └── ui/                # 前端界面
├── core/                  # 核心模块
├── accounts/              # 账户配置
├── profiles/              # 配置文件
├── state/                 # 运行状态
├── logs/                  # 日志文件
├── tests/                 # 测试文件
├── start-trading.bat      # 🚀 唯一启动脚本
└── README.md              # 📖 说明文档
```

## 服务地址

启动成功后，可以通过以下地址访问：

- **前端界面**: http://localhost:3001
- **API服务**: http://localhost:8001
- **API文档**: http://localhost:8001/docs
- **WebSocket**: ws://localhost:8001/ws/logs

## 功能特性

- 🚀 一键启动所有服务
- 📊 实时交易监控界面
- 🔧 多平台账户管理
- 📈 策略配置和执行
- 📱 响应式Web界面
- 🔍 实时日志监控

## 环境要求

- Python 3.8+
- Node.js 16+
- npm 或 yarn

## 使用说明

1. 确保Python虚拟环境已创建并安装依赖
2. 确保Node.js和npm已安装
3. 运行 `start-trading.bat` 启动系统
4. 在浏览器中访问 http://localhost:3001

系统会自动处理环境检查、端口清理、服务启动等所有步骤。