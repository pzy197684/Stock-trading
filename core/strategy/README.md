# 🛠️ 策略目录

交易策略实现模块，包含各种自动化交易策略。

## 📁 目录结构

```
strategy/                       # 交易策略实现目录
├── base.py                     # 策略基类 - 所有策略的基础接口
├── plugins/                    # 策略插件目录 - 策略注册和配置
├── recovery/                   # 解套策略目录 - 被套持仓的解套策略
└── martingale_hedge/           # 马丁对冲策略目录 - 马丁格尔对冲策略
```

## 📋 策略详细说明

### 📂 plugins/ - 策略插件目录
策略注册和动态加载配置
- `recovery.json` - 解套策略插件配置
- `martingale_hedge.json` - 马丁对冲策略插件配置
- 支持策略热插拔和动态加载

### 📂 recovery/ - 解套策略目录
针对被套持仓的马丁格尔解套策略
```
recovery/
├── __init__.py                 # 模块初始化
├── strategy.py                 # 解套策略主实现
├── executor.py                 # 策略执行器
├── recovery_state_persister.py # 状态持久化管理器
├── README.md                   # 策略详细文档
├── test_recovery_basic.py      # 基础测试
└── adapters/                   # 交易所适配器
    ├── __init__.py
    └── binance.py              # Binance适配器
```

**特性:**
- 双向解套（long_trapped/short_trapped）
- 马丁格尔加仓机制
- 分层止盈系统
- 容量控制和熔断保护
- K线过滤确认

### 📂 martingale_hedge/ - 马丁对冲策略目录
马丁格尔对冲交易策略
```
martingale_hedge/
├── __init__.py                 # 模块初始化
├── strategy.py                 # 马丁对冲策略主实现
├── executor.py                 # 策略执行器
├── utils.py                    # 工具函数和状态管理器
└── adapters/                   # 交易所适配器
    ├── __init__.py
    └── binance.py              # Binance适配器
```

**特性:**
- 双向对冲交易
- 马丁格尔加仓逻辑
- 锁仓和解锁机制
- 动态止盈策略
- 风控和熔断保护

## 🎯 策略开发规范

### 📝 基类继承
所有策略必须继承 `base.py` 中的基础策略类：
```python
from core.strategy.base import BaseStrategy

class MyStrategy(BaseStrategy):
    def generate_signal(self, context):
        # 实现信号生成逻辑
        pass
```

### 🔧 插件配置
在 `plugins/` 目录添加策略配置文件：
```json
{
    "name": "my_strategy",
    "display_name": "我的策略",
    "strategy_class": "core.strategy.my_strategy.strategy.MyStrategy",
    "supported_platforms": ["binance", "okx"],
    "parameters": {
        // 策略参数定义
    }
}
```

### 📂 目录结构
推荐的策略目录结构：
```
my_strategy/
├── __init__.py                 # 模块导出
├── strategy.py                 # 主策略实现
├── executor.py                 # 执行器（可选）
├── state_persister.py          # 状态管理器（可选）
├── README.md                   # 策略文档
└── adapters/                   # 交易所适配器（可选）
```

## 🚀 快速开始

1. **查看示例**: 参考 `recovery/` 或 `martingale_hedge/` 目录
2. **阅读文档**: 查看各策略的 README.md 文件
3. **配置参数**: 在 `profiles/` 目录创建策略配置
4. **测试运行**: 使用测试文件验证策略逻辑