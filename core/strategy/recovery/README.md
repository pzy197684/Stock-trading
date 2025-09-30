# 📈 Recovery解套策略

基于马丁格尔原理的智能解套交易策略，用于自动处理被套订单。

## 概述

解套策略是专门为处理被套持仓而设计的马丁格尔交易策略。当投资者持有的多头或空头仓位出现亏损时，该策略通过在反方向进行马丁格尔加仓和分层止盈来帮助解套。

## 核心特性

### 1. 双向解套模式
- **long_trapped**: 多头被套模式，在空头方向进行解套交易
- **short_trapped**: 空头被套模式，在多头方向进行解套交易

### 2. 马丁格尔加仓策略
- 首仓开仓：按配置的first_qty开启解套仓位
- 间距加仓：价格移动达到add_interval_pct时触发加仓
- 倍率递增：每次加仓数量按multiplier倍率递增
- 次数限制：最多加仓max_add_times次，防止无限加仓

### 3. 分层止盈机制
- **首仓独立TP**: 首仓可设置独立的止盈比例
- **满仓前均价TP**: 未达到容量上限时的均价止盈
- **满仓后均价TP**: 达到容量上限后的保守均价止盈

### 4. 容量控制系统
- **cap_ratio**: 解套仓位相对被套仓位的上限比例
- **满仓锁定**: 达到容量上限后只允许止盈，不再加仓
- **动态调整**: 根据被套仓位变化动态调整容量

### 5. 熔断保护机制
- **跳跃熔断**: 检测短期价格异常跳跃，暂停交易
- **ATR熔断**: 基于ATR检测市场异常波动，长期暂停
- **智能恢复**: 熔断期满后自动恢复交易

### 6. K线确认过滤
- **F1过滤**: 实体占比过滤，确保K线实体足够大
- **F2过滤**: 影线比例过滤，避免在假突破时交易
- **F3过滤**: 方向确认过滤，确保价格朝有利方向移动

## 配置参数详解

### 基础配置
```json
{
  "symbol": "ETHUSDT",          // 交易对
  "recovery": {
    "mode": "long_trapped",     // 解套模式: long_trapped | short_trapped
    "cap_ratio": 0.75,          // 容量比例: 0.1-1.0
    "ttl_seconds": 300,         // 订单生存时间(秒)
    "use_limit_tp": true        // 是否使用限价止盈
  }
}
```

### 网格交易配置
```json
{
  "grid": {
    "add_interval_pct": 0.04,         // 加仓间距百分比
    "tp_first_order_pct": 0.01,       // 首仓独立止盈百分比(0=禁用)
    "tp_before_full_pct": 0.02,       // 满仓前均价止盈百分比
    "tp_after_full_pct": 0.01,        // 满仓后均价止盈百分比
    "tp_reprice_tol_ratio": 0.001,    // 止盈重新定价容忍比例
    
    "martingale": {
      "first_qty": 50.0,              // 首仓数量
      "multiplier": 2.0,              // 马丁倍率
      "max_add_times": 4              // 最大加仓次数
    }
  }
}
```

### 确认过滤配置
```json
{
  "confirm": {
    "kline": "15m",                   // 确认K线时间框架
    "filters": {
      "body_min_frac_of_interval": 0.25,   // F1: 实体最小占比
      "wick_to_body_max": 2.0,             // F2: 影线相对实体最大比例
      "followthrough_window_min": 15       // F3: 跟进确认窗口(分钟)
    }
  }
}
```

### 熔断保护配置
```json
{
  "circuit_breakers": {
    "jump": {
      "enabled": true,            // 启用跳跃熔断
      "window_minutes": 30,       // 检测窗口(分钟)
      "factor_vs_interval": 2.0,  // 触发因子(相对加仓间距倍数)
      "pause_minutes": 15         // 暂停时长(分钟)
    },
    "atr": {
      "enabled": true,            // 启用ATR熔断
      "tf": "1h",                 // ATR计算时间框架
      "factor_vs_interval": 3.0,  // 触发因子(相对加仓间距倍数)
      "pause_hours": 24           // 暂停时长(小时)
    }
  }
}
```

## 使用场景

### 1. 多头被套解套
当持有多头仓位出现亏损时：
```json
{
  "recovery": {
    "mode": "long_trapped"
  }
}
```
策略将在空头方向进行马丁格尔交易，通过空头盈利来抵消多头亏损。

### 2. 空头被套解套
当持有空头仓位出现亏损时：
```json
{
  "recovery": {
    "mode": "short_trapped"
  }
}
```
策略将在多头方向进行马丁格尔交易，通过多头盈利来抵消空头亏损。

## 风险管理建议

### 1. 资金管理
- 确保账户有足够资金支持多次加仓
- cap_ratio建议设置在0.5-0.8之间
- 单次交易资金不超过总资金的10%

### 2. 市场环境
- 适合在震荡市场中使用
- 避免在强烈趋势市场中使用
- 关注重大消息面，及时暂停策略

### 3. 参数调优
- add_interval_pct根据标的波动率调整
- multiplier不宜过大，建议1.5-2.5之间
- 开启熔断保护，避免极端风险

## 监控指标

### 关键指标
- `total_trades`: 总交易次数
- `successful_tp_rate`: 成功止盈率
- `avg_holding_time`: 平均持仓时间
- `max_add_times_used`: 最大加仓次数使用情况
- `circuit_breaker_triggers`: 熔断触发次数

### 警报条件
- 连续订单失败 > 5次
- 熔断触发频繁 > 3次/天
- 最大加仓次数使用率 > 80%

## 部署流程

### 1. 配置策略
复制并修改示例配置文件：
```bash
cp profiles/DEMO_RECOVERY/config.json profiles/MY_RECOVERY/config.json
```

### 2. 配置账户
设置对应平台的API密钥：
```json
{
  "platform": "binance",
  "account": "my_account"
}
```

### 3. 启动策略
```bash
python apps/api/main.py --profile MY_RECOVERY
```

### 4. 监控运行
通过日志和监控面板跟踪策略运行状态。

## 常见问题

### Q: 策略什么时候会停止？
A: 以下情况策略会停止：
- 被套仓位完全平仓
- 触发紧急止损
- 手动停止
- 系统错误

### Q: 如何调整风险水平？
A: 主要通过以下参数：
- 降低cap_ratio减少风险敞口
- 增大add_interval_pct减少加仓频率
- 减小multiplier降低加仓增幅
- 启用熔断保护

### Q: 策略状态如何持久化？
A: 策略状态自动保存到state目录，重启后会自动恢复状态，包括：
- 持仓数量和均价
- 加仓次数和历史
- 暂停状态和原因

## 技术实现

### 核心类结构
- `RecoveryStrategy`: 主策略类，实现决策逻辑
- `RecoveryExecutor`: 执行器类，处理订单执行
- `RecoveryBinanceAdapter`: Binance适配器，处理平台特定逻辑
- `RecoveryStatePersister`: 状态持久化管理器，处理Recovery策略状态持久化

### 执行流程
1. 熔断检查 → 2. 状态更新 → 3. 容量判断 → 4. 止盈检查 → 5. 加仓判断 → 6. 信号生成

### 扩展性
- 支持添加新的交易所适配器
- 支持自定义确认过滤器
- 支持插件式风险管理模块