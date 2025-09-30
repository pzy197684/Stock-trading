# Profiles配置档案目录说明

## 📁 目录结构

```
profiles/                       # 策略配置档案目录
├── DEMO_RECOVERY/              # 解套策略演示配置
├── DEMO_BINANCE_MARTINGALE/    # 币安马丁策略演示配置
├── DEMO_BN001/                 # 币安演示账户001配置
├── DEMO_CW002/                 # CoinW演示账户002配置
├── BINANCE_MARTINGALE_HEDGE/   # 币安马丁对冲配置
└── MARTINGALE_HEDGE_EXAMPLE/   # 马丁对冲示例配置
```

## 📋 配置档案说明

### 📂 配置档案结构
每个配置档案目录包含：
```
{PROFILE_NAME}/
├── config.json                 # 主配置文件
├── strategy_params.json        # 策略参数（可选）
└── risk_settings.json          # 风控设置（可选）
```

### 🔧 config.json 配置格式
```json
{
    "account_name": "BN_DEMO_001",
    "strategy_name": "recovery",
    "symbol": "BTCUSDT",
    "strategy_params": {
        "base_qty": 0.001,
        "max_add_times": 5,
        "add_ratio": 2.0,
        "tp_ratio": 0.01
    },
    "risk_control": {
        "max_position_ratio": 0.8,
        "stop_loss_ratio": 0.1,
        "daily_loss_limit": 1000
    }
}
```

## 🎯 配置档案类型

### 🔄 Recovery策略配置
- **DEMO_RECOVERY** - 解套策略演示配置
- 适用于被套持仓的解套操作
- 包含马丁格尔加仓和分层止盈设置

### 📈 马丁对冲策略配置
- **BINANCE_MARTINGALE_HEDGE** - 币安马丁对冲
- **DEMO_BINANCE_MARTINGALE** - 马丁策略演示
- 双向对冲交易配置

### 🏦 交易所专用配置
- **DEMO_BN001** - 币安演示配置
- **DEMO_CW002** - CoinW演示配置
- 针对不同交易所的优化设置

## 🔧 使用说明

### 创建新配置档案
1. 复制现有的演示配置目录
2. 重命名为新的配置档案名
3. 修改 `config.json` 中的参数
4. 调整策略和风控参数

### 配置参数说明
- **account_name**: 关联的账户名称
- **strategy_name**: 使用的策略名称
- **symbol**: 交易标的
- **strategy_params**: 策略特定参数
- **risk_control**: 风险控制参数

### 配置验证
启动前系统会自动验证：
- 配置文件格式正确性
- 必需参数完整性
- 参数值合理性
- 账户权限匹配性

## ⚠️ 注意事项

1. **参数安全**: 敏感参数使用环境变量
2. **备份配置**: 重要配置及时备份
3. **测试验证**: 新配置先在演示环境测试
4. **版本管理**: 配置变更建议版本控制

## 🚀 快速开始

1. **复制演示配置**: `cp -r DEMO_RECOVERY MY_RECOVERY`
2. **编辑配置**: 修改 `MY_RECOVERY/config.json`
3. **验证配置**: 运行配置验证工具
4. **启动策略**: 使用新配置启动交易